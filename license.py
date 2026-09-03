# -*- coding: utf-8 -*-
"""
=============================================================================
【业务端】Ed25519 硬件指纹绑定、纯离线验签与功能模块权限守卫引擎模板
=============================================================================
使用说明：
1. 拷贝本文件到项目的核心子目录下（如 backend/app/core/license.py 或 core/license.py 或根目录 license.py）
2. 替换下方的 ED25519_PUBLIC_KEY_PEM 公钥
3. 本文件在出厂时会被 Cython 自动编译为原生 .so 机器码，源码会被彻底销毁，公钥与验签逻辑无法被逆向篡改！
=============================================================================
"""
import os
import sys
import json
import base64
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

# ===========================================================================
# 👉 【必须修改 1】：内置开发者专属 Ed25519 公钥 (由本地 license_issuer.py 生成)
# ===========================================================================
# ⚠️ 注意：开头的 b 和三引号 """ 绝对不能删！把引号里的内容替换为您专属的公钥文本即可：
ED25519_PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAbRtQWdxRcSVM6LdDiClf0BQA1sZ+A3sGRbAA1Mkh/O4=
-----END PUBLIC KEY-----"""

# 🔒 【严禁修改】：全局内存缓存，存储启动时验签通过的授权载荷
_CURRENT_ACTIVE_LICENSE: Dict[str, Any] = {}

# ===========================================================================
# 🔒 【严禁修改】：核心底层硬件特征提取算法（与 probe_machine.sh 100% 绝对对齐）
# ===========================================================================
def get_current_machine_code() -> str:
    """读取宿主机映射的硬件特征并计算统一 32 位 (4段式) SHA256 抗碰撞指纹"""
    board_uuid = "BOARD-DEFAULT-NODE"
    for p in ["/etc/host_product_uuid", "/sys/class/dmi/id/product_uuid", "/etc/machine-id"]:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    content = f.read().strip()
                    if content:
                        board_uuid = content
                        break
            except Exception:
                pass
                
    cpu_info = "CPU-GENERIC"
    if os.path.exists("/proc/cpuinfo"):
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        # 兼容海光等型号内部带冒号的情况，只截取第 1 个冒号之后的内容
                        cpu_info = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass

    raw_str = f"BOARD={board_uuid};CPU={cpu_info}"
    h = hashlib.sha256(raw_str.encode("utf-8")).hexdigest().upper()
    return "-".join([h[i:i+8] for i in range(0, 32, 8)])

# ===========================================================================
# 🔒 【严禁修改】：启动前微秒级 (0.05ms) 证书验签核心引擎
# ===========================================================================
def verify_license(license_file_path: str = "/app/license.lic") -> Dict[str, Any]:
    """
    Ed25519 启动前微秒级授权校验引擎
    校验项：
    1. 签名防篡改验证 (Ed25519 Asymmetric Verification)
    2. 硬件机器指纹匹配验证 (Machine Code Matching)
    3. 有效期检测 (Expiration Date Checking)
    """
    global _CURRENT_ACTIVE_LICENSE
    
    if not os.path.exists(license_file_path):
        sys.exit("\n[❌ LICENSE ERROR] 授权证书文件 license.lic 不存在，系统拒绝启动！\n")
        
    try:
        with open(license_file_path, "r", encoding="utf-8") as f:
            lic_json = json.load(f)
            
        payload_bytes = base64.b64decode(lic_json["payload"])
        signature = base64.b64decode(lic_json["signature"])
        
        # 1. 使用 Ed25519 公钥验证数字签名（防伪造、防篡改）
        public_key = serialization.load_pem_public_key(ED25519_PUBLIC_KEY_PEM)
        public_key.verify(signature, payload_bytes)
        
        data = json.loads(payload_bytes.decode("utf-8"))
        
        # 2. 校验机器硬件指纹（防跨机器拷贝与容器漂移）
        current_mcode = get_current_machine_code()
        bound_mcode = data.get("machine_code", "").strip()
        
        # 兼容 4段 (32位) 与 8段 (64位) 格式匹配
        if bound_mcode != current_mcode and not bound_mcode.startswith(current_mcode):
            sys.exit(f"\n[❌ LICENSE ERROR] 授权机器指纹不匹配！\n授权绑定: {bound_mcode}\n当前机器: {current_mcode}\n")
            
        # 3. 校验有效到期时间（防超期使用）
        expire_at = datetime.strptime(data.get("expire_at"), "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expire_at:
            sys.exit(f"\n[❌ LICENSE ERROR] 软件授权已于 {data.get('expire_at')} 到期，请联系软件供应商续期！\n")
            
        _CURRENT_ACTIVE_LICENSE = data
        tier_name = data.get("tier", "CUSTOM")
        active_modules = data.get("modules", [])
        
        print(f"[✓] 🔑 【Ed25519 授权验证成功】 客户: {data.get('customer')} | 有效期至: {data.get('expire_at')}")
        print(f"    -> 激活模块: {', '.join(active_modules)}")
        return _CURRENT_ACTIVE_LICENSE
        
    except InvalidSignature:
        sys.exit("\n[❌ LICENSE ERROR] 授权证书签名非法（证书已被篡改或伪造），系统拒绝启动！\n")
    except Exception as e:
        sys.exit(f"\n[❌ LICENSE ERROR] 授权证书解析失败: {e}\n")

# ===========================================================================
# 🔒 【严禁修改】：功能模块激活状态查询工具
# ===========================================================================
def is_module_enabled(module_name: str) -> bool:
    """判断某个功能模块是否已在当前授权中激活"""
    active_modules = _CURRENT_ACTIVE_LICENSE.get("modules", [])
    if "ALL" in active_modules or module_name.upper() in [m.upper() for m in active_modules]:
        return True
    return False

def get_active_license_info() -> Dict[str, Any]:
    """获取当前已激活的授权详情（供前端 UI 接口调用，用于在导航栏隐藏未购买的菜单按钮）"""
    return {
        "customer": _CURRENT_ACTIVE_LICENSE.get("customer", "Unknown"),
        "tier": _CURRENT_ACTIVE_LICENSE.get("tier", "STANDARD"),
        "expire_at": _CURRENT_ACTIVE_LICENSE.get("expire_at", "Expired"),
        "modules": _CURRENT_ACTIVE_LICENSE.get("modules", [])
    }

def require_module(module_name: str):
    """
    FastAPI 路由守卫依赖项：保护特定收费接口，未购买该模块的客户调用将直接抛出 403 Forbidden
    """
    from fastapi import HTTPException, status
    
    def dependency():
        if not is_module_enabled(module_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"抱歉，您当前的软件授权未开通【{module_name}】功能模块，请联系软件供应商升级开通！"
            )
        return True
    return dependency


# ===========================================================================
# 📖 【不同项目集成实操参考指南】（按需复制到您项目的具体业务代码中）
# ===========================================================================
"""
===============================================================================
【用法 1：在项目入口文件第一行加入启动验签】
位置：在 main.py / app.py 的最顶端第一行写入
-------------------------------------------------------------------------------
# 👉 【按需修改】：根据 license.py 放置的位置调整导入路径：
# 如果放在 app/core/license.py ➔ 写 from app.core.license import verify_license
# 如果直接放在根目录 license.py ➔ 写 from license import verify_license
from app.core.license import verify_license

# 🚀 启动首行执行验签，0.05ms 微秒级完成，验签不通过则直接拒绝启动系统：
verify_license("/app/license.lic")

from fastapi import FastAPI
app = FastAPI()
===============================================================================


===============================================================================
【用法 2：后端路由守卫（未购买模块的客户调用直接返回 403 Forbidden）】
位置：在需要收费限制的 API 接口文件上挂载（如 api/routes/items.py）
-------------------------------------------------------------------------------
from fastapi import APIRouter, Depends

# 👉 【按需修改 1】：根据目录调整导入路径
from app.core.license import require_module

router = APIRouter()

# 👉 【按需修改 2】：替换路由变量名（@router 或 @api_router 或 @app）
# 👉 【按需修改 3】：将 "AI_ANALYSIS" 替换为您项目实际要限制收费的模块英文代号
# （例如替换为: "CATEGORY_MANAGE", "EXPORT_EXCEL", "SYSTEM_CONFIG"）
@router.post("/ai-analysis", dependencies=[Depends(require_module("AI_ANALYSIS"))])
def ai_analysis():
    return {"result": "AI 分析报告生成成功"}
===============================================================================


===============================================================================
【用法 3：前端 UI 动态过滤接口（让未购买的功能在页面侧边栏导航中完全隐形）】
位置：在系统的通用接口路由（如 main.py 或 api/system.py）中加入
-------------------------------------------------------------------------------
# 👉 【按需修改 1】：根据目录调整导入路径
from app.core.license import get_active_license_info

# 👉 【按需修改 2】：将接口挂载在您的 app 或 api_router 上
@app.get("/api/v1/system/license")
def get_license():
    \"\"\"
    向前端返回当前已激活的功能列表：
    返回格式示例：
    {
        "customer": "某某科技",
        "expire_at": "2027-09-03 10:00:00",
        "modules": ["DASHBOARD", "ADMIN_MANAGE", "CATEGORY_MANAGE"]
    }
    前端（Vue/React）在渲染左侧菜单导航栏时：
    if (modules.includes("CATEGORY_MANAGE")) { 显示分类菜单 } else { 隐藏菜单 }
    \"\"\"
    return get_active_license_info()
===============================================================================
"""
