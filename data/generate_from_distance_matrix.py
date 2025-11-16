"""
基于距离矩阵的无人机持续监控问题实例生成器

本模块从预先计算好的距离矩阵文件生成无人机周期性监控问题的测试实例。
主要功能：
- 从距离矩阵文件中读取节点间距离信息
- 应用时间缩放逻辑将距离转换为时间
- 为每个目标点随机分配监控周期
- 生成符合特定格式的实例文件用于求解器测试

适用场景：
- 已有实际地理距离数据的场景

与 generate_period.py 的区别：
- 输入：距离矩阵（而非节点坐标）
- 跳过距离计算步骤
- 保持相同的时间缩放和周期分配逻辑
"""

import random
import math
import os

# ==================== 常量定义 ====================
# 表示无限大的距离值，对应距离矩阵中的对角线元素
INFINITY_DISTANCE = 10000000

# 表示起点的无限大监控周期（起点不需要被监控）
INFINITY_PERIOD = 100000

# 距离矩阵中对角线的标识值（来自苏州姑苏区数据）
DIAGONAL_MARKER = 1111112


# ==================== 路径配置 ====================
# 获取脚本所在目录的绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 默认输出目录
DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'input')


def read_distance_matrix(file_path):
    """
    从文件中读取距离矩阵
    
    读取制表符分隔的距离矩阵文件，第一行为表头，后续每行第一列为节点ID，
    其余列为到各节点的距离。对角线值（DIAGONAL_MARKER）会被识别并处理。
    
    Args:
        file_path (str): 距离矩阵文件路径
    
    Returns:
        list: 二维距离矩阵 distance_matrix[i][j] 表示节点 i 到节点 j 的距离
            - 对角线元素为 DIAGONAL_MARKER（将在后续处理中转为 INFINITY_DISTANCE）
            - 索引从 0 开始（文件中的节点1对应索引0）
    
    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件格式不正确
    
    Example:
        >>> matrix = read_distance_matrix('distance_matrix_suzhou_gusu.txt')
        >>> len(matrix)  # 节点数量
        20
        >>> matrix[0][1]  # 节点0到节点1的距离
        2081
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"距离矩阵文件不存在: {file_path}")
    
    distance_matrix = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        if len(lines) < 2:
            raise ValueError("距离矩阵文件格式错误：至少需要表头和一行数据")
        
        # 跳过第一行表头（id 1 2 3 ...）
        for i, line in enumerate(lines[1:], start=1):
            line = line.strip()
            
            # 跳过空行
            if not line:
                continue
            
            # 解析距离数据（制表符分隔）
            parts = line.split('\t')
            
            # 第一列是节点ID，后续列是距离值
            if len(parts) < 2:
                continue  # 跳过格式不正确的行
            
            # 提取距离值（跳过第一列的节点ID）
            try:
                distances = [int(d) for d in parts[1:] if d.strip()]
                distance_matrix.append(distances)
            except ValueError as e:
                raise ValueError(f"第 {i+1} 行数据格式错误: {e}")
    
    # 验证矩阵是方阵
    n = len(distance_matrix)
    if n == 0:
        raise ValueError("距离矩阵为空")
    
    for i, row in enumerate(distance_matrix):
        if len(row) != n:
            raise ValueError(f"距离矩阵不是方阵：第 {i+1} 行有 {len(row)} 列，期望 {n} 列")
    
    print(f"✓ 成功读取距离矩阵: {n} × {n}")
    
    return distance_matrix


def generate_case_from_distance_matrix(
    distance_matrix_path,
    output_dir,
    instance_name='SZ_Gusu',
    version='1p',
    base_time_horizon=108,
    base_drone_time=90,
    time_num=12,
    drone_num=30,
    period_list=[3, 6, 12, 18, 24]
):
    """
    基于距离矩阵生成无人机监控实例
    
    从距离矩阵文件读取节点间距离，应用时间缩放逻辑，为每个目标点分配监控周期，
    并生成格式化的实例文件。缩放逻辑与 generate_period_v2 保持一致。
    
    主要步骤：
    1. 读取距离矩阵文件
    2. 计算时间缩放因子 (multiplier = time_num / base_time_horizon)
    3. 将距离缩放为时间 (travel_time = ceil(distance * multiplier))
    4. 为每个目标点随机分配监控周期（需满足周期 > 到起点的时间）
    5. 生成格式化的实例文件
    
    Args:
        distance_matrix_path (str): 距离矩阵文件路径
        output_dir (str): 输出目录路径
        instance_name (str): 实例标识名称，默认 'SZ_Gusu'
        version (str): 版本号，用于区分不同的随机实例，默认 '1p'
        base_time_horizon (int): 基准时间窗口（距离矩阵对应的原始时间尺度），默认 108
        base_drone_time (int): 基准无人机续航时间（原始时间尺度下），默认 90
        time_num (int): 目标规划时间范围（缩放后），默认 12
        drone_num (int): 可用无人机数量，默认 30
        period_list (list): 可选的监控周期列表，默认 [3, 6, 12, 18, 24]
    
    Returns:
        str: 生成的实例文件名（不含路径）
    
    输出文件格式：
        第1行: 列标题（numNode, numCus, ID_Depot, Mile(min), Begin, End, numUAV）
        第2行: 基本参数值
        第3行: 数据标题（time_vec & deta1 & deta2:）
        后续行: 每个节点的数据（节点ID + 到各节点的时间 + 监控开始时间 + 监控周期）
    
    Example:
        >>> instance = generate_case_from_distance_matrix(
        ...     'solomon/distance_matrix_suzhou_gusu.txt',
        ...     'input',
        ...     instance_name='SZ_Gusu',
        ...     version='1p',
        ...     time_num=12,
        ...     drone_num=30
        ... )
        >>> print(instance)
        SZ_GusuN19D30T12V1p
    
    Notes:
        - 节点0默认为起点（仓库），监控周期设置为无限大
        - 距离矩阵对角线值 DIAGONAL_MARKER 会被转换为 INFINITY_DISTANCE
        - 时间缩放逻辑与 Solomon 数据集处理方式一致
        - 监控周期必须大于从起点到该节点的飞行时间
    """
    print("\n" + "=" * 60)
    print("开始生成实例...")
    print("=" * 60)
    
    # ========== 1. 读取距离矩阵 ==========
    print(f"\n[步骤 1/6] 读取距离矩阵: {os.path.basename(distance_matrix_path)}")
    distance_matrix = read_distance_matrix(distance_matrix_path)
    node_num = len(distance_matrix)
    target_num = node_num - 1  # 目标数 = 节点数 - 起点
    
    print(f"  - 节点总数: {node_num}")
    print(f"  - 目标点数: {target_num}")
    print(f"  - 起点索引: 0")
    
    # ========== 2. 计算时间缩放因子 ==========
    print(f"\n[步骤 2/6] 计算时间缩放因子")
    multiplier = time_num / base_time_horizon
    print(f"  - 基准时间窗口: {base_time_horizon}")
    print(f"  - 目标时间范围: {time_num}")
    print(f"  - 缩放因子: {multiplier:.6f}")
    
    # 计算缩放后的无人机续航时间
    scaled_drone_time = int(base_drone_time * multiplier)
    scaled_time_horizon = int(base_time_horizon * multiplier)  # 应等于 time_num
    print(f"  - 无人机续航: {base_drone_time} → {scaled_drone_time}")
    print(f"  - 时间窗口: {base_time_horizon} → {scaled_time_horizon}")
    
    # ========== 3. 距离转换为时间 ==========
    print(f"\n[步骤 3/6] 转换距离为时间")
    
    # 过滤出不超过 time_num 的监控周期选项
    valid_period_list = [p for p in period_list if p <= time_num]
    if not valid_period_list:
        raise ValueError(f"没有有效的监控周期选项（所有周期都大于 time_num={time_num}）")
    
    print(f"  - 原始周期选项: {period_list}")
    print(f"  - 有效周期选项: {valid_period_list}")
    
    # 构建时间矩阵和节点数据
    target_data = []
    
    for i in range(node_num):
        node_row = [i]  # 节点ID
        
        # 转换距离为时间
        for j in range(node_num):
            distance = distance_matrix[i][j]
            
            # 处理对角线（自身到自身）
            if distance == DIAGONAL_MARKER or i == j:
                travel_time = INFINITY_DISTANCE
            else:
                # 距离 * 缩放因子 = 时间（向上取整）
                travel_time = math.ceil(distance * multiplier)
            
            node_row.append(travel_time)
        
        # 添加监控开始时间（固定为0）
        node_row.append(0)
        
        # ========== 4. 分配监控周期 ==========
        if i == 0:
            # 起点（仓库）不需要被监控
            assigned_period = INFINITY_PERIOD
        else:
            # 获取从起点到当前节点的时间（索引1对应起点0）
            time_to_depot = node_row[1]
            
            # 筛选满足条件的周期：周期 > 到起点的时间
            # 这确保无人机有足够时间飞到目标点并返回
            filtered_periods = [p for p in valid_period_list if p > time_to_depot]
            
            if not filtered_periods:
                # 如果没有满足条件的周期，使用最大的可用周期
                filtered_periods = [max(valid_period_list)]
                print(f"  ⚠ 节点 {i}: 到起点时间={time_to_depot}，使用最大周期 {filtered_periods[0]}")
            
            # 随机选择一个周期
            assigned_period = random.choice(filtered_periods)
        
        node_row.append(assigned_period)
        target_data.append(node_row)
    
    print(f"  - 已为 {node_num} 个节点分配时间和周期")
    
    # ========== 5. 准备输出数据 ==========
    print(f"\n[步骤 4/6] 准备输出数据")
    
    # 基本数据：节点数, 目标数, 仓库ID, 无人机续航, 开始时间, 结束时间, 无人机数
    basic_data = [
        node_num,           # 节点总数
        target_num,         # 目标点数（不包括起点）
        0,                  # 仓库ID（固定为节点0）
        scaled_drone_time,  # 无人机续航时间（缩放后）
        0,                  # 规划开始时间
        scaled_time_horizon, # 规划结束时间（缩放后）
        drone_num           # 无人机数量
    ]
    
    print(f"  - 基本参数: {basic_data}")
    
    # ========== 6. 写入实例文件 ==========
    print(f"\n[步骤 5/6] 生成实例文件")
    
    # 构建实例文件名
    instance_filename = f'{instance_name}N{target_num}D{drone_num}T{time_num}V{version}'
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 输出文件路径
    output_file = os.path.join(output_dir, f'{instance_filename}.txt')
    
    with open(output_file, 'w+', encoding='utf-8') as f:
        # 写入列标题
        f.write('numNode\tnumCus\tID_Depot\tMile(min)\tBegin\tEnd\tnumUAV\n')
        
        # 写入基本数据行
        for item in basic_data:
            f.write(f'{item}\t')
        f.write('\n')
        
        # 写入节点数据标题
        f.write('time_vec & deta1 & deta2:\n')
        
        # 写入每个节点的数据
        for node_data in target_data:
            for value in node_data:
                f.write(f'{value}\t')
            f.write('\n')
    
    print(f"  - 输出路径: {output_file}")
    print(f"  - 实例名称: {instance_filename}")
    
    # ========== 7. 生成摘要信息 ==========
    print(f"\n[步骤 6/6] 生成摘要")
    
    # 统计周期分布
    period_distribution = {}
    for i, node_data in enumerate(target_data):
        if i == 0:  # 跳过起点
            continue
        period = node_data[-1]
        period_distribution[period] = period_distribution.get(period, 0) + 1
    
    print(f"  - 监控周期分布:")
    for period in sorted(period_distribution.keys()):
        count = period_distribution[period]
        print(f"    * 周期 {period}: {count} 个节点")
    
    print("\n" + "=" * 60)
    print(f"✓ 实例生成完成: {instance_filename}")
    print("=" * 60)
    
    return instance_filename


if __name__ == '__main__':
    """
    主程序：批量生成基于距离矩阵的无人机监控实例
    
    配置说明：
    - distance_matrix_path: 距离矩阵文件路径
    - instance_name: 实例名称标识
    - time_num: 规划时间范围
    - drone_num: 无人机数量
    - period_list: 可选的监控周期列表
    - version_range: 版本号范围，用于生成多个随机实例
    """
    
    # ========== 配置参数 ==========
    # 距离矩阵文件路径（相对于脚本目录）
    distance_matrix_file = os.path.join(SCRIPT_DIR, 'solomon', 'distance_matrix_suzhou_gusu_10.txt')
    
    # 实例名称
    instance_name = 'SZ_Gusu'
    
    # 时间和周期参数
    time_num = 12           # 规划时间范围
    period_list = [3, 6, 12, 18, 24]  # 可选监控周期
    
    # 无人机参数
    drone_num = 50          # 无人机数量
    
    # 时间尺度参数（类比 Solomon C1 类实例）
    base_time_horizon = 21600  # 基准时间窗口
    base_drone_time = 18000     # 基准无人机续航
    
    # 输出目录
    output_directory = DEFAULT_OUTPUT_DIR
    
    # 生成的版本数量
    version_range = range(1, 6)  # 生成版本 1p 到 5p
    
    # ========== 打印配置信息 ==========
    print("\n" + "=" * 60)
    print("基于距离矩阵的无人机监控实例生成器")
    print("=" * 60)
    print(f"配置参数:")
    print(f"  - 距离矩阵: {os.path.basename(distance_matrix_file)}")
    print(f"  - 实例名称: {instance_name}")
    print(f"  - 时间范围: {time_num}")
    print(f"  - 监控周期选项: {period_list}")
    print(f"  - 无人机数量: {drone_num}")
    print(f"  - 基准时间窗口: {base_time_horizon}")
    print(f"  - 基准无人机续航: {base_drone_time}")
    print(f"  - 输出目录: {output_directory}")
    print(f"  - 生成版本: {list(version_range)}")
    print("=" * 60)
    
    # ========== 检查文件是否存在 ==========
    if not os.path.exists(distance_matrix_file):
        print(f"\n✗ 错误: 距离矩阵文件不存在: {distance_matrix_file}")
        print("请检查文件路径是否正确")
        exit(1)
    
    # ========== 批量生成实例 ==========
    generated_instances = []
    
    for i in version_range:
        version = f'{i}p'
        
        try:
            instance = generate_case_from_distance_matrix(
                distance_matrix_path=distance_matrix_file,
                output_dir=output_directory,
                instance_name=instance_name,
                version=version,
                base_time_horizon=base_time_horizon,
                base_drone_time=base_drone_time,
                time_num=time_num,
                drone_num=drone_num,
                period_list=period_list
            )
            generated_instances.append(instance)
            
        except Exception as e:
            print(f"\n✗ 生成失败 (版本 {version}): {str(e)}")
            import traceback
            traceback.print_exc()
    
    # ========== 生成完成摘要 ==========
    print("\n" + "=" * 60)
    print(f"所有实例生成完成！共生成 {len(generated_instances)} 个实例:")
    print("=" * 60)
    for idx, inst in enumerate(generated_instances, 1):
        print(f"  {idx}. {inst}")
    print("=" * 60)
    print(f"输出目录: {os.path.abspath(output_directory)}")
    print("=" * 60 + "\n")

