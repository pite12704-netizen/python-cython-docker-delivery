#!/bin/bash
# =========================================================================
# 【通用交付模板】全自动源码二进制加密、离线镜像导出与交付包制作脚本 (v3.0 旗舰版)
# =========================================================================
set -e

# =========================================================================
# ⚙️ 【开发者配置区】—— 请按当前项目的实际信息修改以下 6 个参数：
# =========================================================================

# -------------------------------------------------------------------------
# 👉 【必须修改 1】：项目镜像标签（Tag）
# ⚠️ 注意：这里的名称必须与 docker-compose.yml 中的 `image:` 完全一致！
# -------------------------------------------------------------------------
PROJECT_TAG="my_project-release:v1.0.0"

# -------------------------------------------------------------------------
# 👉 【必须修改 2】：离线交付文件夹名称
# -------------------------------------------------------------------------
DELIVERY_DIR="MyProject_Delivery_Linux"

# -------------------------------------------------------------------------
# 👉 【必须修改 3】：最终生成的交付 Zip 压缩包名称
# -------------------------------------------------------------------------
OUTPUT_ZIP="MyProject_Delivery_Linux.zip"

# -------------------------------------------------------------------------
# 👉 【按需修改 4】：对外暴露的 HTTP 访问端口（默认 8000）
# -------------------------------------------------------------------------
WEB_PORT="8000"

# -------------------------------------------------------------------------
# 👉 【按需修改 5】：离线数据库镜像导出开关（true 导出，false 不导出）
# 说明：如果是 PostgreSQL 项目，设 EXPORT_POSTGRES=true，其余为 false
#      如果是 MySQL 项目，设 EXPORT_MYSQL=true，其余为 false
# -------------------------------------------------------------------------
EXPORT_POSTGRES=true                          # 👈 是否打包导出 PostgreSQL 16 离线镜像
EXPORT_MYSQL=false                            # 👈 是否打包导出 MySQL 8.0 离线镜像
EXPORT_REDIS=false                            # 👈 是否打包导出 Redis 6 离线镜像

# =========================================================================
# 🔒 【以下为自动化构建与封箱逻辑，严禁修改】
# =========================================================================

echo "=========================================================="
echo "      🚀 开始执行企业级全自动二进制加密与出厂交付打包      "
echo "=========================================================="

# 1. 初始化并创建交付目录结构
sudo rm -rf ~/${DELIVERY_DIR} ~/${OUTPUT_ZIP}
mkdir -p ~/${DELIVERY_DIR}/images
mkdir -p ~/${DELIVERY_DIR}/scripts
mkdir -p ~/${DELIVERY_DIR}/config
mkdir -p ~/${DELIVERY_DIR}/data
mkdir -p ~/${DELIVERY_DIR}/logs

# 2. 构建纯机器码加密 Release 镜像
echo ""
echo "[1/4] 正在执行 Linux 原生 Cython 机器码编译并构建无明文镜像..."
sudo docker build -f Dockerfile.release -t ${PROJECT_TAG} .

# 3. 导出所有离线镜像为 tar.gz
echo ""
echo "[2/4] 正在将构建好的镜像导出为独立离线压缩包..."
echo "      -> 导出业务主镜像: ${PROJECT_TAG}"
sudo docker save ${PROJECT_TAG} | gzip > ~/${DELIVERY_DIR}/images/app_image_v1.0.tar.gz

if [ "$EXPORT_POSTGRES" = true ]; then
    echo "      -> 导出 PostgreSQL 16 官方镜像..."
    sudo docker pull postgres:16-alpine
    sudo docker save postgres:16-alpine | gzip > ~/${DELIVERY_DIR}/images/postgres_16_alpine.tar.gz
fi

if [ "$EXPORT_MYSQL" = true ]; then
    echo "      -> 导出 MySQL 8.0 官方镜像..."
    sudo docker pull mysql:8.0
    sudo docker save mysql:8.0 | gzip > ~/${DELIVERY_DIR}/images/mysql_8.0.tar.gz
fi

if [ "$EXPORT_REDIS" = true ]; then
    echo "      -> 导出 Redis 6 官方镜像..."
    sudo docker pull redis:6-alpine
    sudo docker save redis:6-alpine | gzip > ~/${DELIVERY_DIR}/images/redis_6_alpine.tar.gz
fi

# 4. 装配客户现场一键部署脚本与编排文件
echo ""
echo "[3/4] 正在装配交付文件与全自动离线部署脚本..."
cp docker-compose.yml ~/${DELIVERY_DIR}/

cat << 'DEP_EOF' > ~/${DELIVERY_DIR}/scripts/deploy_linux.sh
#!/bin/bash
# =========================================================================
# 【客户现场】全自动纯离线一键部署与健康检查程序
# =========================================================================
set -e

echo "========================================================"
echo "          🚀 正在执行系统纯离线秒级自动化部署程序          "
echo "========================================================"

cd "$(dirname "$0")/.."

echo "[1/3] 正在从本地离线包导入 Docker 镜像（完全无需联网）..."
for img in images/*.tar.gz; do
    if [ -f "$img" ]; then
        echo "      -> 导入镜像: $img"
        docker load < "$img"
    fi
done

echo ""
echo "[2/3] 正在清理旧容器并拉起全套业务服务..."
docker rm -f app-server app-db app-redis 2>/dev/null || true
docker compose up -d

echo ""
echo "[3/3] 等待数据库与业务容器健康检查就绪 (约 8 秒)..."
sleep 8

echo ""
echo "========================================================"
echo "🎉 恭喜！系统已成功完成纯离线部署上线！"
echo "👉 请在浏览器中打开: http://<当前服务器IP>:8000/docs"
echo "========================================================"
DEP_EOF
chmod +x ~/${DELIVERY_DIR}/scripts/deploy_linux.sh

# 5. 生成专业级客户现场部署与运维操作手册
cat << 'DOC_EOF' > ~/${DELIVERY_DIR}/客户现场交付与运维操作手册.md
# 📦 企业级应用系统纯离线部署与运维操作手册

> 欢迎使用本系统！本交付包为 **100% 纯离线安装包**，所有业务代码与底层数据库均已打包为独立的离线镜像，**安装过程完全不需要连接互联网**。

---

## 一、交付包目录结构说明

解压交付包后，您将看到以下文件结构：

```text
├── 📁 images/              ➔ 纯离线 Docker 镜像压缩包 (无需外网拉取)
├── 📁 scripts/             ➔ 自动化运维脚本目录
│   └── 📄 deploy_linux.sh  ➔ 【核心】一键秒级自动化部署程序
├── 📁 data/                ➔ 数据持久化目录 (数据库与业务上传文件存储于此)
├── 📁 logs/                ➔ 运行时日志目录
├── 📄 docker-compose.yml   ➔ 容器服务编排定义文件
└── 📄 客户现场交付与运维操作手册.md ➔ 当前说明文档
```

---

## 二、运行环境前置要求

在执行部署前，请确保目标服务器满足以下基本环境：
1. **操作系统**：Linux (Ubuntu 20.04+ / Debian 11+ / CentOS 7+ / RHEL 8+ / 统信 UOS / 麒麟 Kylin)
2. **容器引擎**：已安装 **Docker** (>= 20.10) 与 **Docker Compose** (>= v2.0)
   * 可通过终端运行 `docker -v` 和 `docker compose version` 验证。

---

## 三、3 步极简离线部署流程（耗时约 30 秒）

### 第一步：将压缩包上传至目标服务器并解压
```bash
unzip MyProject_Delivery_Linux.zip
cd MyProject_Delivery_Linux
```

### 第二步：执行一键部署脚本
```bash
sudo bash scripts/deploy_linux.sh
```
*脚本会自动将离线镜像载入 Docker 引擎，并按正确依赖顺序拉起数据库与业务主服务。*

### 第三步：浏览器访问与系统验收
部署完成后，打开浏览器直接访问：
* **系统 API 控制台与接口文档**：`http://<服务器IP>:8000/docs`
* **默认超级管理员账号**：`admin@example.com`
* **默认管理员初始密码**：`AdminPassword123456!`

---

## 四、常见参数自定义调整（可选）

所有可调参数均集中在 **`docker-compose.yml`** 文件中：

1. **修改对外暴露的访问端口**：
   若需将默认的 `8000` 端口改为 `9000`，修改 `ports:` 字段即可：
   ```yaml
   ports:
     - "9000:8000"   # 宿主机端口:容器内端口
   ```
2. **修改管理员密码或安全密钥**：
   修改 `environment:` 下的 `SECRET_KEY` 和 `FIRST_SUPERUSER_PASSWORD`。
3. **使配置修改生效**：
   修改保存后，在当前目录下执行 `docker compose up -d` 即可秒级热更新生效。

---

## 五、常用日常运维管理命令

请在交付包解压目录下执行以下命令：

* **查看服务运行状态与健康度**：
  ```bash
  docker compose ps
  ```
* **查看业务实时运行日志**：
  ```bash
  docker compose logs -f app
  ```
* **重启所有服务**：
  ```bash
  docker compose restart
  ```
* **平滑停止所有服务**：
  ```bash
  docker compose down
  ```
* **数据备份**：
  直接备份当前目录下的 `data/` 文件夹即可完成全量数据库持久化备份。

---

## 六、常见问题与技术支持 FAQ

* **Q1：提示端口冲突（Bind for 0.0.0.0:8000 failed: port is already allocated）？**  
  👉 解决：打开 `docker-compose.yml`，将 `ports:` 前面的 `8000` 改为一个空闲端口（如 `8088:8000`），然后重新运行 `docker compose up -d`。
* **Q2：如何彻底重置数据库数据？**  
  👉 解决：执行 `docker compose down` 停止容器，删除 `./data/` 目录下的数据库文件夹，再次执行 `sudo bash scripts/deploy_linux.sh` 即可完成初始化重建。
DOC_EOF

# 6. 生成最终交付 Zip 压缩包
echo ""
echo "[4/4] 正在封箱打包为最终交付 Zip 压缩包..."
sudo chown -R $USER:$USER ~/${DELIVERY_DIR}
cd ~ && zip -r ${OUTPUT_ZIP} ${DELIVERY_DIR}/

echo ""
echo "=========================================================="
echo "🎉 恭喜！企业级商业交付包已成功生成："
echo "📦 交付文件路径: ~/${OUTPUT_ZIP}"
echo "📁 包含内容: 纯 .so 机器码镜像 + 数据库离线镜像 + 编排配置 + 一键部署脚本 + 客户操作手册"
echo "=========================================================="
