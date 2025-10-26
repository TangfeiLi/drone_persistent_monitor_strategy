# Launch Jobs 脚本使用说明

## 📋 概述

`launch_jobs.sh` 是一个自动化批量实验执行脚本，用于无人机持久监控策略优化问题的求解。

## ✨ 主要特性

- ✅ **零配置**：自动检测项目路径，无需手动修改
- ✅ **智能跳过**：自动跳过已求解的算例，避免重复计算
- ✅ **错误处理**：单个算例失败不影响后续执行
- ✅ **进度追踪**：实时显示执行状态和统计信息
- ✅ **日志管理**：自动保存标准输出和错误日志
- ✅ **跨平台**：支持 Linux/Mac/Windows Git Bash

## 📁 项目结构要求

确保你的项目结构如下：

```
drone_persistent_monitor_strategy/
├── launch_jobs.sh              ← 本脚本
├── Drone_discrete_strategy.exe ← 求解器程序
├── infor.json                  ← 配置文件
└── data/
    ├── input/                  ← 算例输入文件（*.txt）
    ├── result/                 ← 结果输出目录
    │   ├── results.txt
    │   └── detail_results.txt
    ├── .out/                   ← 标准输出日志
    ├── .err/                   ← 错误日志
    └── solved_instances.txt    ← 已求解算例列表
```

## 🚀 使用方法

### 基本用法

```bash
# 1. 赋予执行权限（首次使用）
chmod +x launch_jobs.sh

# 2. 处理所有算例
./launch_jobs.sh

# 3. 只处理特定类型的算例（如 C1 开头）
./launch_jobs.sh C1

# 4. 处理 R1 开头的算例
./launch_jobs.sh R1
```

### 算例命名规则

算例文件名格式：`C1N10D20T12V1.txt`
- **C1/C2/R1/RC1**: 算例类型
- **N10**: 10个监控目标点
- **D20**: 20架无人机
- **T12**: 规划时间范围
- **V1**: 版本号

### 使用示例

```bash
# 示例 1: 处理所有 C1 类型算例
./launch_jobs.sh C1

# 示例 2: 处理所有 R1 类型算例
./launch_jobs.sh R1

# 示例 3: 处理所有算例
./launch_jobs.sh
```

## 📊 执行过程说明

### 1. 初始化阶段
脚本会自动：
- 检测项目根目录
- 验证必要文件是否存在
- 创建输出目录（如果不存在）

### 2. 处理阶段
对每个算例文件：
- 检查是否已求解（查询 `solved_instances.txt`）
- 如果未求解：调用求解器
- 如果已求解：跳过

### 3. 完成阶段
显示执行摘要：
- 总算例数
- 新求解数
- 跳过数
- 失败数

## 📝 输出文件说明

### 结果文件
- `data/result/results.txt` - 汇总结果
- `data/result/detail_results.txt` - 详细结果

### 日志文件
- `data/.out/[算例名].out` - 标准输出日志
- `data/.err/[算例名].err` - 错误日志

### 追踪文件
- `data/solved_instances.txt` - 已成功求解的算例列表

## 🔧 故障排除

### 问题 1: 找不到可执行文件
```
❌ 错误: 找不到可执行文件
```
**解决方案**：确保 `Drone_discrete_strategy.exe` 在项目根目录

### 问题 2: 找不到输入目录
```
❌ 错误: 找不到输入目录
```
**解决方案**：确保 `data/input/` 目录存在且包含 `.txt` 算例文件

### 问题 3: 权限不足
```
Permission denied
```
**解决方案**：
```bash
chmod +x launch_jobs.sh
```

### 问题 4: 算例求解失败
查看对应的错误日志：
```bash
cat data/.err/[算例名].err
```

## 🎯 高级用法

### 重新求解已完成的算例

如果需要重新求解某个算例：

```bash
# 方法 1: 从 solved_instances.txt 中删除对应行
vim data/solved_instances.txt

# 方法 2: 清空所有记录（重新求解全部）
> data/solved_instances.txt
```

### 并行执行

可以在不同终端窗口同时运行不同类型的算例：

```bash
# 终端 1
./launch_jobs.sh C1

# 终端 2
./launch_jobs.sh R1

# 终端 3
./launch_jobs.sh RC1
```

### 后台运行

对于长时间运行的实验：

```bash
# 后台运行并保存日志
nohup ./launch_jobs.sh > launch.log 2>&1 &

# 查看进度
tail -f launch.log
```

## 📤 分享给他人

### 打包项目

```bash
# 方法 1: 使用 zip
zip -r experiment_package.zip . -x "*.out" -x "*.err" -x "data/result/*"

# 方法 2: 使用 tar
tar -czf experiment_package.tar.gz \
    --exclude='*.out' \
    --exclude='*.err' \
    --exclude='data/result/*' \
    .
```

### 其他人使用步骤

1. 解压文件到任意目录
2. 将算例文件放入 `data/input/`
3. 运行 `./launch_jobs.sh`

**无需任何路径修改！** 🎉

## 🐛 调试模式

如果遇到问题，可以启用调试模式：

```bash
# 启用详细调试信息
bash -x ./launch_jobs.sh C1
```

## 📮 技术支持

如有问题，请检查：
1. 项目结构是否正确
2. 文件权限是否足够
3. 错误日志内容
4. 可执行文件是否损坏

---

**版本**: 2.0  
**最后更新**: 2025-10-25  
**兼容性**: Linux, macOS, Windows Git Bash

