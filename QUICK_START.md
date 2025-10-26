# 🚀 快速开始指南

## 给其他人的简明使用说明

### ⚡ 5分钟上手

#### 步骤 1: 解压项目
将收到的项目文件解压到任意位置，比如：
- Windows: `C:\Users\YourName\experiment\`
- Linux/Mac: `~/experiment/`

**重要**：项目可以放在任何位置，无需修改任何配置！

#### 步骤 2: 准备算例文件
确保 `data/input/` 目录下有 `.txt` 格式的算例文件。

#### 步骤 3: 运行脚本

**Windows (Git Bash)**:
```bash
cd /c/Users/YourName/experiment/drone_persistent_monitor_strategy
./launch_jobs.sh
```

**Linux/Mac**:
```bash
cd ~/experiment/drone_persistent_monitor_strategy
chmod +x launch_jobs.sh
./launch_jobs.sh
```

#### 步骤 4: 等待完成
脚本会自动：
- ✓ 检查所需文件
- ✓ 创建输出目录
- ✓ 逐个求解算例
- ✓ 跳过已完成的算例
- ✓ 保存结果和日志

#### 步骤 5: 查看结果
结果保存在：
- `data/result/results.txt` - 汇总结果
- `data/result/detail_results.txt` - 详细结果

---

## 🎨 运行示例

### 示例输出

```
================================================
项目根目录: /home/user/experiment/drone_persistent_monitor_strategy
================================================

检查必要文件和目录...
✓ 可执行文件存在: /home/user/.../Drone_discrete_strategy.exe
✓ 配置文件存在: /home/user/.../infor.json
✓ 输入目录存在: /home/user/.../data/input
✓ 输出目录已就绪

================================================
开始处理算例: *.txt
================================================

----------------------------------------
[1] 处理: C1N10D20T12V1.txt
→ 状态: 未求解，开始执行...
✓ 求解成功 (耗时: 15秒)

----------------------------------------
[2] 处理: C1N15D20T12V13.txt
→ 状态: 已求解，跳过

...

================================================
执行完成！摘要统计：
================================================
总算例数:   10
已求解:     5 (新完成)
已跳过:     5 (之前已完成)
失败:       0
================================================
```

---

## 💡 常用命令

```bash
# 处理所有算例
./launch_jobs.sh

# 只处理 C1 类型
./launch_jobs.sh C1

# 只处理 R1 类型
./launch_jobs.sh R1

# 后台运行（长时间实验）
nohup ./launch_jobs.sh > run.log 2>&1 &

# 查看后台进程
ps aux | grep launch_jobs

# 查看实时日志
tail -f run.log
```

---

## ❓ 常见问题

### Q1: 可以中断后继续吗？
**答**: 可以！按 `Ctrl+C` 中断，再次运行会自动跳过已完成的算例。

### Q2: 如何重新运行某个算例？
**答**: 从 `data/solved_instances.txt` 中删除对应的行即可。

### Q3: 运行失败怎么办？
**答**: 查看 `data/.err/[算例名].err` 文件中的错误信息。

### Q4: 可以同时运行多个脚本吗？
**答**: 可以，在不同终端运行不同类型的算例：
```bash
# 终端1: ./launch_jobs.sh C1
# 终端2: ./launch_jobs.sh R1
```

### Q5: Windows 上无法运行？
**答**: 
1. 安装 Git for Windows（包含 Git Bash）
2. 在 Git Bash 中运行，不要用 CMD 或 PowerShell
3. 下载地址：https://git-scm.com/download/win

---

## 📋 检查清单

在运行前，确保：
- [ ] 项目已完整解压
- [ ] `Drone_discrete_strategy.exe` 存在
- [ ] `infor.json` 存在
- [ ] `data/input/` 目录有算例文件
- [ ] （Linux/Mac）已赋予执行权限: `chmod +x launch_jobs.sh`

---

## 🎉 就这么简单！

无需关心：
- ❌ 绝对路径
- ❌ 配置文件
- ❌ 环境变量
- ❌ 路径修改

只需：
- ✅ 解压
- ✅ 运行
- ✅ 完成

---

**遇到问题？** 查看详细文档：`README_LAUNCH_JOBS.md`

