# -*- coding: utf-8 -*-
"""
=============================================================================
【开发者专属】企业级离线 License 授权签发工作台 (Ed25519 + 模块化分级售卖系统)
=============================================================================
核心功能：
1. 采用 Ed25519 椭圆曲线数字签名（超轻量 64 字节不可伪造签名）
2. 支持版本分级售卖（基础版 / 专业版 / 旗舰版 / 自定义模块套餐）
3. 绑定目标宿主机物理硬件指纹（防跨机器克隆与未授权扩散）
4. 一键生成不可篡改的商业离线授权证书 license.lic
=============================================================================
依赖安装：pip install cryptography>=41.0.0
"""
import os
import json
import base64
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

PRIVATE_KEY_FILE = "ed25519_private_key.pem"
PUBLIC_KEY_FILE = "ed25519_public_key.pem"

# 预设的常用业务功能模块清单（可根据您的具体项目增减）
TIER_MODULES_MAP = {
    "1": {
        "name": "👑 旗舰版 (ENTERPRISE)",
        "tier": "ENTERPRISE",
        "modules": ["ALL"]
    },
    "2": {
        "name": "🚀 专业版 (PROFESSIONAL)",
        "tier": "PROFESSIONAL",
        "modules": ["USER_MANAGE", "BASIC_DATA", "STATISTICS", "DATA_EXPORT"]
    },
    "3": {
        "name": "📦 基础版 (STANDARD)",
        "tier": "STANDARD",
        "modules": ["USER_MANAGE", "BASIC_DATA"]
    }
}

def get_or_create_keys():
    """首次运行自动生成 Ed25519 高安全密钥对"""
    if not os.path.exists(PRIVATE_KEY_FILE):
        print("[+] 首次运行：正在为您生成开发者专属 Ed25519 密钥对...")
        private_key = ed25519.Ed25519PrivateKey.generate()
        
        # 保存 Ed25519 私钥（绝密，严禁出厂）
        with open(PRIVATE_KEY_FILE, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        # 保存 Ed25519 公钥（可公开，内置到项目中供 Cython 编译验签）
        with open(PUBLIC_KEY_FILE, "wb") as f:
            f.write(private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        print(f"[✓] 密钥生成完毕！私钥: {PRIVATE_KEY_FILE} | 公钥: {PUBLIC_KEY_FILE}\n")
    else:
        with open(PRIVATE_KEY_FILE, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
    return private_key

def main():
    print("==================================================================")
    print("   🚀 企业级 Ed25519 商业授权离线签发工作台 (License Issuer v3.0)  ")
    print("==================================================================")
    
    private_key = get_or_create_keys()
    
    # 1. 客户基本信息
    customer_name = input("1. 请输入客户企业名称 (如 某某科技有限公司): ").strip()
    if not customer_name:
        customer_name = "VIP_CUSTOMER"
        
    machine_code = input("2. 请输入客户发来的机器码 (Machine Code): ").strip()
    if not machine_code:
        print("[❌ 错误] 机器码不能为空！")
        return
        
    days_input = input("3. 请输入授权有效天数 (默认 365，输入 9999 为永久版): ").strip()
    expire_days = int(days_input) if days_input.isdigit() else 365
    expire_date = (datetime.now() + timedelta(days=expire_days)).strftime("%Y-%m-%d %H:%M:%S")
    
    # 2. 版本套餐与功能模块选择
    print("\n---------------- 请选择授权售卖版本套餐 ----------------")
    print(" [1] 👑 旗舰版 (ENTERPRISE - 开通全部功能, modules: ['ALL']) [默认]")
    print(" [2] 🚀 专业版 (PROFESSIONAL - 基础功能 + 高级统计 + 批量导出)")
    print(" [3] 📦 基础版 (STANDARD - 仅用户管理 + 基础数据录入)")
    print(" [4] 🛠️ 自定义模块套餐 (Custom Modules)")
    print("---------------------------------------------------------")
    tier_choice = input("请选择套餐编号 [1-4] (默认 1): ").strip()
    if not tier_choice:
        tier_choice = "1"
        
    if tier_choice in TIER_MODULES_MAP:
        selected = TIER_MODULES_MAP[tier_choice]
        tier_name = selected["tier"]
        tier_display = selected["name"]
        modules_list = selected["modules"]
    else:
        tier_name = "CUSTOM"
        tier_display = "🛠️ 自定义套餐 (CUSTOM)"
        custom_input = input("请输入允许开通的模块代号 (逗号分隔，如 USERS,EXPORT,AI_CHAT): ").strip()
        modules_list = [m.strip().upper() for m in custom_input.split(",") if m.strip()] if custom_input else ["ALL"]

    # 3. 构造授权证书载荷 (Payload)
    payload_dict = {
        "customer": customer_name,
        "machine_code": machine_code,
        "issued_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expire_at": expire_date,
        "tier": tier_name,
        "modules": modules_list,
        "algorithm": "Ed25519",
        "license_version": "v3.0"
    }
    
    payload_bytes = json.dumps(payload_dict, sort_keys=True).encode("utf-8")
    
    # 4. 使用 Ed25519 私钥执行高速数字签名 (固定输出 64 字节不可伪造签名)
    signature = private_key.sign(payload_bytes)
    
    # 5. 打包生成最终 license.lic 证书文件
    license_file_content = {
        "payload": base64.b64encode(payload_bytes).decode("utf-8"),
        "signature": base64.b64encode(signature).decode("utf-8")
    }
    
    with open("license.lic", "w", encoding="utf-8") as f:
        json.dump(license_file_content, f, indent=2)
        
    print("\n" + "=" * 62)
    print("🎉 恭喜！商业授权离线证书签发成功！")
    print(f"📄 证书文件路径: {os.path.abspath('license.lic')}")
    print(f"🏢 授权客户名称: {customer_name}")
    print(f"🖥️ 绑定机器指纹: {machine_code}")
    print(f"🎖️ 授权版本套餐: {tier_display}")
    print(f"📦 激活功能模块: {', '.join(modules_list)}")
    print(f"⏳ 有效到期时间: {expire_date} (共 {expire_days} 天)")
    print("=" * 62)
    print("👉 将生成的 【license.lic】 发送给客户放入部署根目录即可！")

if __name__ == "__main__":
    main()
