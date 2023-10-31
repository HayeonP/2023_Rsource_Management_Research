import os
import yaml
import csv
import sys
import subprocess

def profile_memory_bandwidth():
    if mode == 'frequency':
        os.system(f'perf record --cpu {target_cores} -e l3d_cache_refill -F {target_frequency} sleep {duration} > /dev/null')
    elif mode == 'threshold':
        os.system(f'perf record --cpu {target_cores} -e l3d_cache_refill -c {target_threshold} sleep {duration} > /dev/null')
    os.system(f'sleep 2')
    # print('finish')
    # sys.stdout.flush()
    for i in range(3):
        os.system(f'perf script > {file_path} < /dev/null 2> /dev/null')
        if is_profile_correct():
            break
    # os.system(f'perf script > {file_path} < /dev/null')
    # print('finish2')
    # sys.stdout.flush()

def is_profile_correct():
    fetch_list = []
    with open(file_path, 'r') as temp:
        reader = csv.reader(temp)

        for i, line in enumerate(reader):
            if line[0].split()[1].split(':')[0] == 'K' or line[0].split()[1].split(':')[0] == 'U':
                fetch_count = float(line[0].split()[3])
            else:
                fetch_count = float(line[0].split()[2])

            if i > 500:
                break
            fetch_list.append(fetch_count)

        temp.close()
        if not any(fetch_list):
            return False
        return True

if __name__ == '__main__':
    with open('configs/bw_profiler.yaml', 'r') as f:
        configs = yaml.safe_load(f)

    label = configs['label']
    duration = configs['duration']
    target_cores = configs['target_cores']
    mode = configs['mode']
    target_frequency = configs['target_frequency']
    target_threshold = configs['target_threshold']
    dir_path = f'bw_profiler/{label}'
    file_path = f'{dir_path}/{label}.dat'
    file_name = f'{label}.dat'

    if label != 'test' and os.path.exists(f'{file_path}'):
        print('[ERROR] Same name of log already exists')
        exit()

    if not os.path.exists(dir_path):
        os.system(f'mkdir -p {dir_path}')
        
    print(f'Test CPU: {target_cores}')
    print(f'Experiment name: {label}')
    
    while True:
        profile_memory_bandwidth()
        if is_profile_correct():
            break
    f.close()
    os.system(f'cp configs/bw_profiler.yaml {dir_path}')

    print(f'{label}: Finish Profile Bandwidth')
