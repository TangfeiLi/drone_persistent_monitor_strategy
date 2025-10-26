import pandas as pd
import numpy as np
import warnings
import random
import math
import os

warnings.filterwarnings('ignore')
# random.seed(0)

def generate_period_v1(data_path, ins_type, version, drone_num = 30, period_list = [1,6,12]):
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
    
    # print(data_list)

    instance_name = f'{ins_type}N{target_num}D{drone_num}V{version}'
    with open(f'dataset_distance/{ins_type}/instance/{ins_type}N{target_num}D{drone_num}V{version}.txt', 'w+') as f:
        for i in data_list:
            for j in i:
                f.write(f'{j}\t')
            f.write('\n')
    
    return instance_name

def cal_distance(position_data):
    distance_vec = []
    k = 0
    for i in range(len(position_data)):
        row_vec = []
        for j in range(len(position_data)):
            x = position_data[i]; y = position_data[j]
            if (i == j):
                row_vec.append(10000000)
            else:
                row_vec.append(round(math.sqrt(math.pow(x[0]-y[0],2)+math.pow(x[1]-y[1],2)),2))
        distance_vec.append(row_vec)
    return distance_vec

def generate_period_v2(data_path, ins_type, version, instance_pos, target_num = 25, drone_num = 30, period_list = [1,3,6,12,18,24], time_num = 12):
    f = open(data_path)
    txt = []
    i = 0
    for line in f:
        i += 1
        if (i<=9):
            continue
        txt.append(line.strip())

    #获取位置信息
    position_data = []
    target_start = 0 #固定起点
    for i in range(len(txt)):
        if (i < target_start): 
            continue
        if (i-target_start>target_num):
            break
        ans = [int(j) for j in txt[i].split('      ')]
        position_data.append([ans[j] for j in range(1,3)])       

    drone_time = drone_time_dict[ins_type] #可以调整
    # planning_horizon = random.randint(drone_time+3, drone_time+9) #可以调整
    planning_horizon = time_horizon_dict[ins_type] #可以调整

    multiplier = time_num/planning_horizon

    #获取距离信息
    new_period_list = [i for i in period_list if i<=time_num]
    distance_data = cal_distance(position_data)
    target_data = []
    for i in range(len(distance_data)):
        ans = [i]
        for j in range(len(distance_data[i])):
            ans.append(math.ceil(distance_data[i][j]*multiplier))
        ans.append(0)
        if i == 0:
            ans.append(100000)
        else:
            filtered_period_list = [i for i in new_period_list if i>ans[1]]
            ans.append(random.choice(filtered_period_list))
        target_data.append(ans)

    node_num = len(target_data)
    basic_data = [node_num, target_num, 0, int(drone_time*multiplier), 0, int(planning_horizon*multiplier), drone_num]

    instance_name = f'{ins_type}N{target_num}D{drone_num}T{time_num}V{version}'
    # with open(f'dataset_distance/{ins_type}/instance/{ins_type}N{target_num}D{drone_num}V{version}.txt', 'w+') as f:
    with open(f'{instance_pos}/{ins_type}/{ins_type}N{target_num}D{drone_num}T{time_num}V{version}.txt', 'w+') as f:
        f.write('numNode\tnumCus\tID_Depot\tMile(min)\tBegin\tEnd\tnumUAV\n')
        for i in basic_data:
            f.write(f'{i}\t')
        f.write('\n')

        f.write('time_vec & deta1 & deta2:\n')
        for i in target_data:
            for j in i:
                f.write(f'{j}\t')
            f.write('\n')
    
    return instance_name

def get_file_name(folder_path):
    for root, dirs, files_ in os.walk(folder_path, topdown=False):
        files = files_

    names = []
    for file in files:
        names.append(f"{file[:-4]}")
    print(names)


if __name__ == '__main__':
    instance_dict = {'C1':'c101', 'C2':'c201', 'R1':'r102', 'RC1':'rc101'}
    period_list = [3,6,12,18,24]

    drone_time_dict = {'C1': 90, 'C2':90, 'R1':90, 'RC1':110}
    time_horizon_dict = {'C1': 108, 'C2':108, 'R1':108, 'RC1':132}

    for key, val in instance_dict.items():
        # if key not in ('RC1'):
        #     continue

        print('算例:', key)
        data_path = 'solomon/' + val + '.txt'

        instance_list = []

        for i in range(30,35):
            version = f'{i}p'
            # new_instance = generate_period_v1(data_path, key, version, 30, period_list)
            # new_instance = generate_period_v2(data_path, key, version, 'extend_customers', 35, 50, period_list, 12)
            new_instance = generate_period_v2(data_path, key, version, 'input', 35, 100, period_list, 18)
            instance_list.append(new_instance)

        print('new instance:\n', instance_list)
