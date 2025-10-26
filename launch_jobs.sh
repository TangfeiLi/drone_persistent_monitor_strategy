#!/bin/bash

# ============================================================================
# 无人机持久监控策略 - 批量实验执行脚本
# 功能：递归遍历算例文件（支持子目录），调用求解器，跳过已求解的算例
# 用法：./launch_jobs.sh [文件名前缀]
#       ./launch_jobs.sh C1    # 处理所有C1开头的算例（所有子目录）
#       ./launch_jobs.sh       # 处理所有算例（递归搜索所有子目录）
#
# 目录结构支持：
#   data/input/*.txt          - 扁平结构（直接在input下）
#   data/input/C1/*.txt       - 分层结构（按类型分子目录）
#   data/input/*/*.txt        - 自动递归搜索所有子目录
# ============================================================================

# 设置错误时不自动退出（允许继续处理下一个算例）
set +e

# 记录脚本开始时间（用于统计总耗时）
SCRIPT_START_TIME=$(date +%s)

# ============================================================================
# 步骤 1: 自动检测项目根目录（脚本所在目录）
# ============================================================================
# 说明：使用bash内置变量自动定位，无需手动配置路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}"

echo "================================================"
echo "项目根目录: ${ROOT_DIR}"
echo "================================================"

# ============================================================================
# 步骤 2: 定义所有需要的路径（基于根目录的相对路径）
# ============================================================================
DATA_DIR="${ROOT_DIR}/data"
INPUT_DIR="${DATA_DIR}/input"
RESULT_DIR="${DATA_DIR}/result"
LOG_OUT_DIR="${DATA_DIR}/.out"
LOG_ERR_DIR="${DATA_DIR}/.err"
SOLVED_LIST="${DATA_DIR}/solved_instances.txt"
EXE_PATH="${ROOT_DIR}/Drone_discrete_strategy.exe"
CONFIG_PATH="${ROOT_DIR}/infor.json"
RESULTS_FILE="${RESULT_DIR}/results.txt"
DETAIL_RESULTS_FILE="${RESULT_DIR}/detail_results.txt"

# ============================================================================
# 步骤 3: 验证必要文件和目录是否存在
# ============================================================================
echo ""
echo "检查必要文件和目录..."

# 检查可执行文件
if [ ! -f "${EXE_PATH}" ]; then
    echo " 错误: 找不到可执行文件: ${EXE_PATH}"
    echo "   请确保 Drone_discrete_strategy.exe 在项目根目录下"
    exit 1
fi
echo "✓ 可执行文件存在: ${EXE_PATH}"

# 检查配置文件
if [ ! -f "${CONFIG_PATH}" ]; then
    echo " 错误: 找不到配置文件: ${CONFIG_PATH}"
    echo "   请确保 infor.json 在项目根目录下"
    exit 1
fi
echo "✓ 配置文件存在: ${CONFIG_PATH}"

# 检查输入目录
if [ ! -d "${INPUT_DIR}" ]; then
    echo " 错误: 找不到输入目录: ${INPUT_DIR}"
    echo "   请确保 data/input/ 目录存在且包含算例文件"
    exit 1
fi
echo "✓ 输入目录存在: ${INPUT_DIR}"

# ============================================================================
# 步骤 4: 创建输出目录（如果不存在）
# ============================================================================
mkdir -p "${RESULT_DIR}" 2>/dev/null
mkdir -p "${LOG_OUT_DIR}" 2>/dev/null
mkdir -p "${LOG_ERR_DIR}" 2>/dev/null

echo "✓ 输出目录已就绪"
echo "  - 结果目录: ${RESULT_DIR}"
echo "  - 日志目录: ${LOG_OUT_DIR}, ${LOG_ERR_DIR}"

# 创建 solved_instances.txt（如果不存在）
if [ ! -f "${SOLVED_LIST}" ]; then
    touch "${SOLVED_LIST}"
    echo "✓ 创建已求解列表: ${SOLVED_LIST}"
fi

# ============================================================================
# 步骤 5: 处理命令行参数（文件名匹配模式）
# ============================================================================
# 说明：构建 find 命令需要的文件名模式（用于递归搜索所有子目录）
if [ -z "$1" ]; then
  # 没有参数：匹配所有文件
  NAME_PATTERN="*.txt"
  DISPLAY_PATTERN="*.txt (所有子目录)"
else
  # 有参数：匹配指定前缀的文件
  NAME_PATTERN="$1*.txt"
  DISPLAY_PATTERN="${1}*.txt (所有子目录)"
fi

echo ""
echo "================================================"
echo "开始处理算例: ${DISPLAY_PATTERN}"
echo "================================================"

# ============================================================================
# 步骤 5.5: 扫描并统计文件总数
# ============================================================================
echo ""
echo "正在扫描文件..."
TOTAL_FILES=$(find "${INPUT_DIR}" -type f -name "${NAME_PATTERN}" 2>/dev/null | wc -l)

echo "找到 ${TOTAL_FILES} 个匹配的算例文件"

# 如果没有找到文件，提前退出
if [ ${TOTAL_FILES} -eq 0 ]; then
    echo ""
    echo "⚠️  警告: 未找到匹配的算例文件"
    echo "   搜索目录: ${INPUT_DIR} (递归搜索所有子目录)"
    echo "   文件名模式: ${NAME_PATTERN}"
    echo ""
    echo "   提示：脚本会自动搜索所有子目录中的文件"
    echo "   请检查："
    echo "     - 文件是否存在于 ${INPUT_DIR}/ 或其子目录中"
    echo "     - 文件名是否匹配模式 ${NAME_PATTERN}"
    exit 0
fi

echo ""
echo "准备开始处理..."
echo ""

# ============================================================================
# 步骤 6: 统计信息初始化
# ============================================================================
TOTAL_COUNT=0
SKIPPED_COUNT=0
SOLVED_COUNT=0
FAILED_COUNT=0

# ============================================================================
# 步骤 7: 遍历算例文件并处理
# ============================================================================
# 说明：使用 find 命令递归搜索所有子目录中的算例文件
# 注意：使用进程替换 < <(...) 而不是管道 | ，避免子shell导致变量无法更新
while IFS= read -r file
do
  # 检查文件是否真实存在（避免边界情况）
  if [ ! -f "${file}" ]; then
    continue
  fi
  
  # 提取文件名（不含路径）和相对路径
  base_name=$(basename "${file}")
  rel_path="${file#${INPUT_DIR}/}"  # 计算相对于input目录的路径
  TOTAL_COUNT=$((TOTAL_COUNT + 1))
  
  echo ""
  echo "----------------------------------------"
  echo "[${TOTAL_COUNT}/${TOTAL_FILES}] 处理: ${rel_path}"
  
  # ============================================================================
  # 步骤 7.1: 检查是否已求解（查找完整行匹配）
  # ============================================================================
  grep -Fx "${base_name}" "${SOLVED_LIST}" > /dev/null 2>&1
  return_code=$?

  if [ "${return_code}" != "0" ]; then
    # ============================================================================
    # 步骤 7.2: 未求解 - 启动求解任务
    # ============================================================================
    echo "→ 状态: 未求解，开始执行..."
    echo "→ 命令: ${EXE_PATH}"
    echo "   参数1: ${CONFIG_PATH}"
    echo "   参数2: ${RESULTS_FILE}"
    echo "   参数3: ${DETAIL_RESULTS_FILE}"
    echo "   参数4: ${rel_path}"
    
    # 记录开始时间
    START_TIME=$(date +%s)
    
    # 调用求解器
    "${EXE_PATH}" \
      "${CONFIG_PATH}" \
      "${RESULTS_FILE}" \
      "${DETAIL_RESULTS_FILE}" \
      "${file}" \
      2> "${LOG_ERR_DIR}/${base_name}.err" \
      > "${LOG_OUT_DIR}/${base_name}.out"
    
    # 检查执行结果
    exit_code=$?
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    
    if [ ${exit_code} -eq 0 ]; then
      # 成功求解
      echo "✓ 求解成功 (耗时: ${ELAPSED}秒)"
      echo "${base_name}" >> "${SOLVED_LIST}"
      SOLVED_COUNT=$((SOLVED_COUNT + 1))
    else
      # 求解失败
      echo "✗ 求解失败 (退出码: ${exit_code}, 耗时: ${ELAPSED}秒)"
      echo "  错误日志: ${LOG_ERR_DIR}/${base_name}.err"
      FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
  else
    # ============================================================================
    # 步骤 7.3: 已求解 - 跳过
    # ============================================================================
    echo "→ 状态: 已求解，跳过"
    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
  fi
done < <(find "${INPUT_DIR}" -type f -name "${NAME_PATTERN}" 2>/dev/null | sort)

# ============================================================================
# 步骤 8: 显示执行摘要
# ============================================================================
# 计算总耗时
SCRIPT_END_TIME=$(date +%s)
SCRIPT_ELAPSED=$((SCRIPT_END_TIME - SCRIPT_START_TIME))
hours=$((SCRIPT_ELAPSED / 3600))
minutes=$(((SCRIPT_ELAPSED % 3600) / 60))
seconds=$((SCRIPT_ELAPSED % 60))

echo ""
echo "================================================"
echo "执行完成！摘要统计："
echo "================================================"
echo "总算例数:   ${TOTAL_COUNT}"
echo "已求解:     ${SOLVED_COUNT} (新完成)"
echo "已跳过:     ${SKIPPED_COUNT} (之前已完成)"
echo "失败:       ${FAILED_COUNT}"
echo "------------------------------------------------"
printf "总耗时:     "
if [ ${hours} -gt 0 ]; then
    printf "%d小时 " ${hours}
fi
if [ ${minutes} -gt 0 ] || [ ${hours} -gt 0 ]; then
    printf "%d分钟 " ${minutes}
fi
printf "%d秒\n" ${seconds}

# 计算平均时间（仅当有新求解的算例时）
if [ ${SOLVED_COUNT} -gt 0 ]; then
    avg_time=$((SCRIPT_ELAPSED / SOLVED_COUNT))
    echo "平均耗时:   ${avg_time}秒/个 (仅新求解)"
fi
echo "================================================"

echo ""
echo "结果文件位置:"
echo "  - 汇总结果: ${RESULTS_FILE}"
echo "  - 详细结果: ${DETAIL_RESULTS_FILE}"
echo "  - 已求解列表: ${SOLVED_LIST}"
echo "================================================"
