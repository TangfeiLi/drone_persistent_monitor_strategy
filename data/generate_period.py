"""
无人机持续监控问题实例生成器

本模块基于 Solomon VRPTW 基准数据集生成无人机周期性监控问题的测试实例。
主要功能：
- 从 Solomon 数据集中提取节点坐标信息
- 计算节点间的欧几里得距离
- 为每个目标点随机分配监控周期
- 生成符合特定格式的实例文件用于求解器测试

适用场景：
- 无人机路径规划研究
- 周期性监控问题的算法测试
- 基于 Solomon 基准的扩展实验

"""

import pandas as pd
import numpy as np
import warnings
import random
import math
import os

warnings.filterwarnings('ignore')

# ==================== 常量定义 ====================
# 表示无限大的距离值，用于对角线元素（自身到自身的距离）
INFINITY_DISTANCE = 10000000

# 表示起点的无限大监控周期（起点不需要被监控）
INFINITY_PERIOD = 100000

# ==================== 路径配置 ====================
# 获取脚本所在目录的绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Solomon 原始数据集目录
SOLOMON_DIR = os.path.join(SCRIPT_DIR, 'solomon')

# 生成的实例文件输出目录（默认）
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'input')

def generate_period_v1(data_path, ins_type, version, drone_num = 30, period_list = [1,6,12]):
    """
    生成周期性监控实例 - 版本1 (已废弃)
    
    警告：此函数已废弃，请使用 generate_period_v2() 代替。
    该版本存在路径硬编码、功能受限等问题，仅保留用于向后兼容。
    
    Args:
        data_path (str): 输入数据文件路径
        ins_type (str): 实例类型标识（如 'C1', 'R1', 'RC1'）
        version (str): 版本号标识
        drone_num (int): 无人机数量，默认 30
        period_list (list): 可选的监控周期列表，默认 [1,6,12]
    
    Returns:
        str: 生成的实例名称
        
    Deprecated:
        已废弃
    """
    # 发出废弃警告
    warnings.warn(
        "generate_period_v1 已废弃，请使用 generate_period_v2 代替",
        DeprecationWarning,
        stacklevel=2
    )
    
    f = open(data_path)
    txt = []
    for line in f:
        txt.append(line.strip())

    data_list = []
    for i in range(len(txt)):
        if i == 1:
            ans = [int(j) for j in txt[i].split('\t')]
            target_num = ans[1]
            ans[-1] = drone_num
        elif i in [0, 2, 3]:
            ans = [j for j in txt[i].split('\t')]
        else:
            ans = [int(j) for j in txt[i].split('\t')]
            ans[-1] = random.choice(period_list)
        data_list.append(ans)   
    
    instance_name = f'{ins_type}N{target_num}D{drone_num}V{version}'
    
    # 注意：此处路径硬编码是该版本的主要问题之一
    output_path = f'dataset_distance/{ins_type}/instance/{ins_type}N{target_num}D{drone_num}V{version}.txt'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w+') as f:
        for i in data_list:
            for j in i:
                f.write(f'{j}\t')
            f.write('\n')
    
    return instance_name

def cal_distance(position_data):
    """
    计算节点间的欧几里得距离矩阵
    
    根据节点的二维坐标计算任意两点之间的欧几里得距离，生成对称的距离矩阵。
    对角线元素（节点到自身的距离）设置为无限大值。
    
    Args:
        position_data (list): 节点位置列表，每个元素为 [x, y] 坐标
            例如: [[0, 0], [1, 2], [3, 4]]
    
    Returns:
        list: 二维距离矩阵，distance_vec[i][j] 表示节点 i 到节点 j 的距离
            - 对角线元素（i==j）为 INFINITY_DISTANCE
            - 其他元素为欧几里得距离，保留两位小数
    
    Example:
        >>> positions = [[0, 0], [3, 4], [1, 1]]
        >>> distances = cal_distance(positions)
        >>> distances[0][1]  # 节点0到节点1的距离
        5.0
    """
    distance_vec = []
    
    for i in range(len(position_data)):
        row_vec = []
        for j in range(len(position_data)):
            x = position_data[i]  # 起点坐标
            y = position_data[j]  # 终点坐标
            
            if (i == j):
                # 节点到自身的距离设为无限大
                row_vec.append(INFINITY_DISTANCE)
            else:
                # 计算欧几里得距离: sqrt((x1-x2)^2 + (y1-y2)^2)
                euclidean_dist = math.sqrt(
                    math.pow(x[0] - y[0], 2) + math.pow(x[1] - y[1], 2)
                )
                row_vec.append(round(euclidean_dist, 2))
        
        distance_vec.append(row_vec)
    
    return distance_vec

def generate_period_v2(data_path, ins_type, version, instance_pos, target_num = 25, 
                       drone_num = 30, period_list = [1,3,6,12,18,24], time_num = 12):
    """
    生成周期性监控实例 - 版本2（推荐使用）
    
    从 Solomon VRPTW 数据集中提取节点坐标，计算节点间距离，为每个目标点随机分配
    监控周期，并生成格式化的实例文件用于求解器测试。
    
    主要步骤：
    1. 读取 Solomon 数据文件，跳过前9行头信息
    2. 提取指定数量的节点坐标（第一个节点为起点/仓库）
    3. 计算节点间欧几里得距离并转换为时间单位
    4. 为每个目标点（非起点）随机分配监控周期
    5. 生成格式化的实例文件
    
    Args:
        data_path (str): Solomon 数据文件路径
        ins_type (str): 实例类型标识，如 'C1', 'C2', 'R1', 'R2', 'RC1', 'RC2'
        version (str): 版本号标识，用于区分不同的随机实例
        instance_pos (str): 输出文件的基础目录路径
        target_num (int): 目标点数量（不包括起点），默认 25
        drone_num (int): 可用无人机数量，默认 30
        period_list (list): 可选的监控周期列表（时间单位），默认 [1,3,6,12,18,24]
        time_num (int): 规划时间范围（时间单位），默认 12
    
    Returns:
        str: 生成的实例文件名（不含路径），格式为 '{ins_type}N{target_num}D{drone_num}T{time_num}V{version}'
    
    输出文件格式：
        第1行: 列标题（numNode, numCus, ID_Depot, Mile(min), Begin, End, numUAV）
        第2行: 基本参数值
        第3行: 数据标题（time_vec & deta1 & deta2:）
        后续行: 每个节点的数据（节点ID + 到各节点的时间 + 监控开始时间 + 监控周期）
    
    Example:
        >>> instance = generate_period_v2(
        ...     'solomon/c101.txt', 'C1', '1p', 'input', 
        ...     target_num=10, drone_num=20, time_num=12
        ... )
        >>> print(instance)
        C1N10D20T12V1p
    
    Notes:
        - Solomon 数据文件格式要求节点坐标用 6 个空格分隔
        - 起点（节点0）的监控周期设置为无限大（不需要被监控）
        - 时间缩放因子根据 time_num 和预定义的 time_horizon 计算
        - 监控周期的分配考虑了节点到起点的时间约束
    """
    # ========== 1. 读取 Solomon 数据文件 ==========
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Solomon 数据文件不存在: {data_path}")
    
    f = open(data_path)
    txt = []
    i = 0
    for line in f:
        i += 1
        if (i <= 9):
            # 跳过 Solomon 文件的前 9 行头信息
            continue
        txt.append(line.strip())
    f.close()

    # ========== 2. 提取节点位置信息 ==========
    position_data = []
    target_start = 0  # 固定起点为第一个节点（索引0）
    
    for i in range(len(txt)):
        if (i < target_start): 
            continue
        if (i - target_start > target_num):
            # 提取 target_num+1 个节点（包括起点）
            break
        
        # Solomon 格式：节点数据用 6 个空格分隔
        # 格式：节点编号(6空格)X坐标(6空格)Y坐标(6空格)需求量...
        ans = [int(j) for j in txt[i].split('      ')]
        # 提取 X 和 Y 坐标（索引1和2）
        position_data.append([ans[j] for j in range(1, 3)])       

    # ========== 3. 获取时间参数并计算缩放因子 ==========
    # 无人机单次飞行的续航时间（基于原始 Solomon 时间尺度）
    drone_time = drone_time_dict[ins_type]
    
    # 规划时间窗口长度（基于原始 Solomon 时间尺度）
    planning_horizon = time_horizon_dict[ins_type]

    # 时间缩放因子：将原始时间尺度转换为新的时间单位
    # 例如：planning_horizon=108, time_num=12, 则 multiplier=12/108≈0.111
    multiplier = time_num / planning_horizon

    # ========== 4. 计算距离并转换为时间 ==========
    # 过滤出不超过 time_num 的监控周期选项
    new_period_list = [i for i in period_list if i <= time_num]
    
    # 计算节点间的欧几里得距离矩阵
    distance_data = cal_distance(position_data)
    
    # 构建每个节点的完整数据
    target_data = []
    for i in range(len(distance_data)):
        ans = [i]  # 节点ID
        
        # 将距离转换为时间（向上取整）并添加到各节点的时间
        for j in range(len(distance_data[i])):
            travel_time = math.ceil(distance_data[i][j] * multiplier)
            ans.append(travel_time)
        
        # 监控开始时间（固定为0）
        ans.append(0)
        
        # 分配监控周期
        if i == 0:
            # 起点（仓库）不需要被监控，周期设为无限大
            ans.append(INFINITY_PERIOD)
        else:
            # 为目标点分配监控周期
            # 周期必须大于从起点到该点的飞行时间（ans[1]是到起点的时间）
            filtered_period_list = [p for p in new_period_list if p > ans[1]]
            
            if not filtered_period_list:
                # 如果没有合适的周期，使用最大可用周期
                filtered_period_list = [max(new_period_list)]
            
            ans.append(random.choice(filtered_period_list))
        
        target_data.append(ans)

    # ========== 5. 准备输出数据 ==========
    node_num = len(target_data)
    # 基本数据：节点数, 目标数, 仓库ID, 无人机续航, 开始时间, 结束时间, 无人机数
    basic_data = [
        node_num, 
        target_num, 
        0,  # 仓库ID（固定为0）
        int(drone_time * multiplier),  # 无人机续航时间（缩放后）
        0,  # 规划开始时间
        int(planning_horizon * multiplier),  # 规划结束时间（缩放后）
        drone_num
    ]

    # ========== 6. 写入实例文件 ==========
    instance_name = f'{ins_type}N{target_num}D{drone_num}T{time_num}V{version}'
    
    # 构建输出路径：instance_pos/ins_type/文件名.txt
    output_dir = os.path.join(instance_pos, ins_type)
    os.makedirs(output_dir, exist_ok=True)  # 自动创建目录
    
    output_file = os.path.join(output_dir, f'{instance_name}.txt')
    
    with open(output_file, 'w+') as f:
        # 写入列标题
        f.write('numNode\tnumCus\tID_Depot\tMile(min)\tBegin\tEnd\tnumUAV\n')
        
        # 写入基本数据行
        for i in basic_data:
            f.write(f'{i}\t')
        f.write('\n')

        # 写入节点数据标题
        f.write('time_vec & deta1 & deta2:\n')
        
        # 写入每个节点的数据
        for i in target_data:
            for j in i:
                f.write(f'{j}\t')
            f.write('\n')
    
    print(f"✓ 已生成实例: {instance_name}")
    
    return instance_name

def get_file_name(folder_path):
    """
    获取指定文件夹中所有文件的文件名（不含扩展名）
    
    注意：此函数当前未被使用，保留用于可能的工具用途。
    
    Args:
        folder_path (str): 文件夹路径
    
    Returns:
        list: 文件名列表（不含扩展名）
    
    Example:
        >>> names = get_file_name('solomon/')
        >>> print(names)
        ['c101', 'c201', 'r102', ...]
    """
    files = []
    for root, dirs, files_ in os.walk(folder_path, topdown=False):
        files = files_
        break  # 只处理第一级目录

    names = []
    for file in files:
        # 去除文件扩展名（最后4个字符，假设为 .txt）
        names.append(f"{file[:-4]}")
    
    return names


# ==================== 实例配置 ====================
# Solomon 实例类型映射（实例类型 -> Solomon 文件名）
instance_dict = {
    'C1': 'c101',   # Clustered customers, short scheduling horizon
    'C2': 'c201',   # Clustered customers, long scheduling horizon  
    'R1': 'r102',   # Random customers, short scheduling horizon
    'RC1': 'rc101'  # Random-Clustered customers, short scheduling horizon
}

# 无人机续航时间配置（基于原始 Solomon 时间尺度）
drone_time_dict = {
    'C1': 90,    # C1 类实例的无人机续航时间
    'C2': 90,    # C2 类实例的无人机续航时间
    'R1': 90,    # R1 类实例的无人机续航时间
    'RC1': 110   # RC1 类实例的无人机续航时间
}

# 规划时间窗口配置（基于原始 Solomon 时间尺度）
time_horizon_dict = {
    'C1': 108,   # C1 类实例的规划时间窗口
    'C2': 108,   # C2 类实例的规划时间窗口
    'R1': 108,   # R1 类实例的规划时间窗口
    'RC1': 132   # RC1 类实例的规划时间窗口
}


if __name__ == '__main__':
    """
    主程序：批量生成无人机监控实例
    
    配置说明：
    - target_num: 目标点数量（如 10, 15, 25, 30, 35）
    - drone_num: 无人机数量（如 20, 30, 50, 100）
    - time_num: 规划时间范围（如 6, 12, 18, 24）
    - period_list: 可选的监控周期列表
    - version_range: 版本号范围，用于生成多个随机实例
    """
    
    # ========== 生成参数配置 ==========
    period_list = [3, 6, 12, 18, 24]  # 可选的监控周期
    
    # 批量生成配置
    target_num = 35      # 目标点数量
    drone_num = 100      # 无人机数量
    time_num = 18        # 规划时间范围
    version_range = range(30, 35)  # 生成版本 30p 到 34p
    
    print("=" * 60)
    print("无人机持续监控实例生成器")
    print("=" * 60)
    print(f"配置参数:")
    print(f"  - 目标点数量: {target_num}")
    print(f"  - 无人机数量: {drone_num}")
    print(f"  - 时间范围: {time_num}")
    print(f"  - 监控周期选项: {period_list}")
    print(f"  - 输出目录: {OUTPUT_DIR}")
    print("=" * 60)
    
    # ========== 遍历各实例类型生成 ==========
    for key, val in instance_dict.items():
        # 可选：只生成特定类型的实例
        # if key not in ('C1', 'C2'):
        #     continue
        
        print(f"\n正在生成实例类型: {key}")
        print("-" * 60)
        
        # 构建 Solomon 数据文件路径（使用相对路径）
        data_path = os.path.join(SOLOMON_DIR, val + '.txt')
        
        # 检查数据文件是否存在
        if not os.path.exists(data_path):
            print(f"⚠ 警告: Solomon 数据文件不存在: {data_path}")
            continue
        
        instance_list = []
        
        # 生成多个版本的实例（用于随机性测试）
        for i in version_range:
            version = f'{i}p'
            
            try:
                # ========== 调用生成函数 ==========
                # 旧版本（已废弃）：
                # new_instance = generate_period_v1(data_path, key, version, 30, period_list)
                
                # 推荐版本：
                new_instance = generate_period_v2(
                    data_path=data_path,
                    ins_type=key,
                    version=version,
                    instance_pos=OUTPUT_DIR,
                    target_num=target_num,
                    drone_num=drone_num,
                    period_list=period_list,
                    time_num=time_num
                )
                instance_list.append(new_instance)
                
            except Exception as e:
                print(f"✗ 生成失败 (版本 {version}): {str(e)}")
        
        print(f"\n实例类型 {key} 生成完成，共 {len(instance_list)} 个实例:")
        for idx, inst in enumerate(instance_list, 1):
            print(f"  {idx}. {inst}")
    
    print("\n" + "=" * 60)
    print("所有实例生成完成！")
    print("=" * 60)
