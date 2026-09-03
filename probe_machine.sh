#!/bin/bash
# =========================================================================
# 【宿主机硬件指纹提取探针】(与容器内部 license.py 100% 对齐版)
# 兼容 Intel / AMD / 国产海光 Hygon / 鲲鹏 / 飞腾
# =========================================================================
set -e

# 1. 优先读取主板 UUID，无 DMI 则回退到 /etc/machine-id
BOARD_UUID=$(cat /sys/class/dmi/id/product_uuid 2>/dev/null || cat /etc/machine-id 2>/dev/null || echo "BOARD-DEFAULT-NODE")
BOARD_UUID=$(echo "${BOARD_UUID}" | tr -d ' \t\r\n')

# 2. 提取完整 CPU 核心序列特征 (使用 cut -d: -f2- 完整保留海光等自带冒号的型号)
CPU_INFO=$(grep -m 1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2- | xargs || echo "CPU-GENERIC")
CPU_INFO=$(echo "${CPU_INFO}" | tr -d '\r\n')

# 3. 严格计算统一 32 位 (4 段式) 抗碰撞机器指纹码
RAW_STR="BOARD=${BOARD_UUID};CPU=${CPU_INFO}"
MACHINE_CODE=$(echo -n "${RAW_STR}" | sha256sum | awk '{print $1}' | tr 'a-z' 'A-Z' | cut -c 1-32 | fold -w 8 | paste -sd '-' -)

echo "========================================================"
echo "    🔑 您的目标服务器机器码: "
echo "        ${MACHINE_CODE}"
echo "========================================================"
echo "👉 请将上方机器码复制并发送给软件提供商，以申请授权文件 license.lic"
echo "========================================================"
