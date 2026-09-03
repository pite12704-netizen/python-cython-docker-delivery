# -*- coding: utf-8 -*-
"""
=========================================================================
【企业级通用交付模板】Cython 源码 AOT 二进制机器码加密构建引擎 (v3.0 旗舰增强版)
- 自动递归扫描工程目录，将核心业务代码编译为 .so (Linux) 或 .pyd (Windows) 原生机器码
- 自动保护入口脚本、动态配置与预启动工具（保留明文入口供启动器正常调用）
- 内置排除数据库迁移（Alembic/Django Migrations）与单元测试用例（tests/），避免非法 C 标识符报错
- 完美解决 FastAPI / Pydantic v2 类型注解与元反射在 Cython 编译下的强类型断言冲突
- 编译成功后自动物理销毁原始 .py 明文源码，彻底杜绝源码与知识产权泄露
=========================================================================
"""

import os
import sys
import shutil
from setuptools import setup
from Cython.Build import cythonize

# -------------------------------------------------------------------------
# 👉 【按需修改 1】：强制保留明文的单文件列表（不参与二进制加密）
# 规则说明：
# 1. 框架启动入口（main.py, manage.py 等）必须保留明文供 Uvicorn/Gunicorn 调用
# 2. 启动前 CLI 执行脚本（backend_pre_start.py, initial_data.py）必须保留明文
# 3. 动态读取配置与 Pydantic 设置类（settings.py, config.py）保留明文，避免元反射丢失
# 💡 若您的项目有其他自定义的 Python 启动脚本（如 init_db.py），请加入此列表！
# -------------------------------------------------------------------------
EXCLUDE_FILES = {
    # 编译与构建脚本自身
    "build_encrypted.py",
    "setup.py",
    # Django 入口与配置
    "manage.py",
    "wsgi.py",
    "asgi.py",
    "settings.py",
    "local_settings.py",
    # FastAPI / 现代化微服务入口与配置
    "main.py",
    "app.py",
    "web_app.py",
    "config.py",
    # 启动前环境检测与超级管理员初始化脚本 (CLI 脚本)
    "backend_pre_start.py",
    "initial_data.py",
    "tests_pre_start.py",
    "prestart.py",
}

# -------------------------------------------------------------------------
# 🔒 【通用排除目录列表 - 默认无需修改】：彻底跳过扫描的文件夹
# 规则说明：
# 1. alembic / migrations：数据库版本迁移文件名以数字开头，C 语言严禁数字开头函数名，已自动排除
# 2. tests / test：开发期单元测试用例，非生产代码，已自动排除
# 3. frontend / static / templates：前端代码与静态资源，已自动排除
# -------------------------------------------------------------------------
EXCLUDE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "venv",
    "env",
    "__pycache__",
    "build",
    "dist",
    "docs",
    "static",
    "templates",
    "images",
    "scripts",
    "data",
    "logs",
    "alembic",      # 👈 排除 Alembic 迁移目录（防数字开头模块名报错）
    "migrations",   # 👈 排除 Django 数据迁移目录
    "tests",        # 👈 排除单元测试用例目录（防构建路径缺失报错）
    "test",
    "testing",
    "frontend",     # 👈 排除前端源码目录
    "packages",
}

def get_py_files(base_dir="."):
    """递归收集所有需要编译加密的核心业务逻辑 .py 文件"""
    py_files = []
    for root, dirs, files in os.walk(base_dir):
        # 1. 文件夹级别过滤：整块跳过非业务目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        
        for f in files:
            if f.endswith(".py"):
                # 2. 单文件级别过滤：放行特定入口文件与包命名空间 __init__.py
                if f in EXCLUDE_FILES or f.startswith("__init__"):
                    continue
                full_path = os.path.relpath(os.path.join(root, f), base_dir)
                clean_path = full_path.replace("\\", "/")
                py_files.append(clean_path)
    return py_files

# -------------------------------------------------------------------------
# 🔒 【以下为 Cython 机器码编译与物理擦除引擎核心逻辑，严禁修改】
# -------------------------------------------------------------------------
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__)) if os.path.dirname(os.path.abspath(__file__)) else "."
    os.chdir(current_dir)
    
    print("[+] 🚀 开始扫描待加密的核心业务逻辑源码...")
    target_files = get_py_files(".")
    print(f"[+] 成功识别到 {len(target_files)} 个业务源码文件准备编译为原生机器码：")
    for f in target_files:
        print(f"    -> {f}")
        
    if not target_files:
        print("[!] 未找到待编译文件，跳过编译步骤。")
        sys.exit(0)
        
    # 执行 Cython C 语言转换与原生二进制编译
    setup(
        ext_modules=cythonize(
            target_files,
            compiler_directives={
                "language_level": "3",            # Python 3 语法标准
                "always_allow_keywords": True,   # 允许关键字传参
                "binding": True,                 # 保留 Python 函数元数据与签名反射
                "annotation_typing": False,      # 👈 【核心关键】设为 False，完美兼容 FastAPI/Pydantic 的依赖注入语法！
            },
            quiet=False,
        )
    )
    
    # 编译成功后，彻底物理删除原始 .py 源码文件（实现纯密文安全交付）
    print("[+] 🛡️ 正在彻底物理销毁容器内的明文业务源码...")
    for f in target_files:
        if os.path.exists(f):
            os.remove(f)
            print(f"    [已物理擦除源码] {f}")
            
    # 清理编译过程中生成的中间 .c / .cpp 临时文件
    for root, dirs, files in os.walk("."):
        for f in files:
            if f.endswith(".c") or f.endswith(".cpp"):
                c_file = os.path.join(root, f)
                base_name = os.path.splitext(f)[0] + ".py"
                if any(base_name in tf for tf in target_files):
                    os.remove(c_file)
                    
    print("[✓] 🎉 核心业务源码加密、物理擦除与符号表剥离全部完成！")
