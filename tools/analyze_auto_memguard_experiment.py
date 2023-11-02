import os
import sys
import yaml
import time
import csv

def get_memory_bandwidth(exp_name):
    fb_file_path = f'{cur_dir}/memguard_experiment/{label}/{exp_name}/{exp_name}.info'
    fb = open(fb_file_path, 'r')
    lines = fb.readlines()
    for line in lines:
        if 'Memory bandwidth' in line and 'std' not in line:
            # line.replace(' ', '')
            components = line.split(' ')
            bandwidth_usage = components[3]
            break
    # print(bandwidth_usage)
    fb.close()
    return bandwidth_usage



def main():
    bw_list = {}
    for workload in target_workload:
        bw_list[workload] = []
        for bandwidth in target_bandwidth:
            exp_name = f'{label}_{workload}_{bandwidth}'
            bandwidth_usage = get_memory_bandwidth(exp_name)
            bw_list[workload].append(bandwidth_usage)

    output_file_path = f'{cur_dir}/memguard_experiment/{label}/summary.csv'
    fw = open(output_file_path, 'w')
    writer = csv.writer(fw)
    workload_list = ['bw/workload']
    workload_list.extend(target_workload)
    # print(workload_list)
    writer.writerow(workload_list)
    for i, bandwidth in enumerate(target_bandwidth):
        temp = [bandwidth]
        for workload in target_workload:
            temp.append(bw_list[workload][i])
        writer.writerow(temp)
    fw.close()
            



if __name__ == '__main__':
    with open('configs/auto_memguard_experiment.yaml', 'r') as f:
        configs = yaml.safe_load(f)

    label = configs['label']
    ssh_address = configs['ssh_address']
    profiling_duration = configs['profiling_duration']

    host_memguard_directory = configs['host_memguard_directory']
    exynos_memguard_directory = configs['exynos_memguard_directory']
    target_project_dir = configs['target_project_dir']
    memguard_limit_directory = configs['memguard_limit_directory']

    target_workload = configs['target_workload']
    target_bandwidth = configs['target_bandwidth']
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    dir_path = f'{cur_dir}/memguard_experiment/{label}'

    if label != 'test' and os.path.exists(f'{dir_path}'):
        print('[ERROR] Same name of log already exists')
        exit()
    
    if label == 'test':
        os.system(f'ssh {ssh_address} "cd {target_project_dir}/bw_profiler && rm -rf test_*"')
        os.system(f'cd {cur_dir} && rm -rf test')

    if not os.path.exists(dir_path):
        os.system(f'mkdir -p {dir_path}')

    main()