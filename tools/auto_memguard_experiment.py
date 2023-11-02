import os
import sys
import yaml
import subprocess
import time

# worklaod 수와 core수를 조절한다.

def is_memguard_installed():
    output = str(os.popen(f'ssh {ssh_address} "lsmod"').read())
    output = output.split('\n')
    for line in output:
        if 'memguard' in line:
            return True
    return False

def build_memguard():
    os.system(f'cd {host_memguard_directory} && sh make_memguard.sh')

def build_sequential_write():
    os.system(f'cd {cur_dir} && sh make_sequential_write.sh')
    # print(cur_dir)

def insmod_memguard():
    os.system(f'ssh {ssh_address} "cd {exynos_memguard_directory} && insmod memguard.ko"')

def rmmod_memguard():
    os.system(f'ssh {ssh_address} "cd {exynos_memguard_directory} && rmmod memguard.ko"')

def set_memguard_limit(target_cores, target_bandwidth):
    # echo set {cluster명} {bandwidth (MB/s)} {target core} > /sys/kernel/debug/memguard/containers
    # 예시: echo set num1 8192 4-7 > /sys/kernel/debug/memguard/containers
    # print(f'ssh {ssh_address} "echo set {label} {target_bandwidth} {target_cores} > {memguard_limit_directory}"')
    os.system(f'ssh {ssh_address} "echo set {label} {target_bandwidth} {target_cores} > {memguard_limit_directory}"')

def rm_memguard_limit():
    os.system(f'ssh {ssh_address} "echo rm {label} > {memguard_limit_directory}"')

def run_sequential_write(sequential_write_cnt):
    sequential_write_process_list = []
    test = None
    try:
        for i in range(sequential_write_cnt):
            core_num = 4 + i
            # os.system(f'ssh {ssh_address} "cd {target_project_dir} && taskset -c {core_num} ./a.out > /dev/null" &')
            # sequential_write_process = subprocess.Popen([ssh, ssh_address])
            ssh_command = f'ssh {ssh_address} "cd {target_project_dir} && taskset -c {core_num} ./a.out > /dev/null &"'
            # subprocess.run(ssh_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process = subprocess.Popen(ssh_command, shell=True)
            sequential_write_process_list.append(process)
            # process.terminate()
    except:
        os.system(f'ssh {ssh_address} "killall -9 a.out"')
        print(f'[ERROR] Error occur when execute sequential write')
        exit(1)
    return sequential_write_process_list

def terminate_sequential_write(sequential_write_process_list):
    for process in sequential_write_process_list:
        process.terminate()
        process.kill()
    
    os.system(f'ssh {ssh_address} "killall -9 a.out"')
    time.sleep(2)

def change_bw_profiler_title(new_title, target_cores):
    file_path = f'{cur_dir}/configs/bw_profiler.yaml'
    fr = open(file_path, 'r')
    lines = fr.readlines()
    fr.close()
    
    # 실험명, 코어정보 변경
    fw = open(file_path, 'w')
    for line in lines:
        if 'label' in line and not '#' in line:
            line.replace(' ', '')
            components = line.split(':')
            components[1] = new_title
            line = components[0] + ": " + components[1] + "\n"
            # print(components)
        if 'target_cores' in line and not '#' in line:
            line.replace(' ', '')
            components = line.split(':')
            components[1] = target_cores
            line = components[0] + ": " + components[1] + "\n"

        fw.write(line)
    fw.close()

def profile_bandwidth_usage(workload, bandwidth, target_cores):
    bw_profiler_title = f'{label}_{workload}_{bandwidth}'
    change_bw_profiler_title(bw_profiler_title, target_cores)
    os.system(f'cd {cur_dir} && sh profile_bandwidth.sh')
    os.system(f'mv {cur_dir}/bw_profiler/{bw_profiler_title} {dir_path}')

def main():
    # memguard 설치 여부 확인
    if is_memguard_installed():
        rmmod_memguard()

    # memguard 빌드
    build_memguard()

    # sequential write 빌드
    build_sequential_write()

    # memguard insmod
    # insmod_memguard()

    for workload in target_workload:
        for bandwidth in target_bandwidth:
            insmod_memguard()
            core_cnt = int(workload[0])
            sequential_write_cnt = int(workload[-2])
            target_cores = f'{4}-{3+core_cnt}'
            if bandwidth != 'no_limit':
                # memguard limit 설정
                set_memguard_limit(target_cores, bandwidth)


            # sequential write 실행
            sequential_write_process_list = run_sequential_write(sequential_write_cnt)

            # profiling
            profile_bandwidth_usage(workload, bandwidth, target_cores)

            # sequential write 종료
            terminate_sequential_write(sequential_write_process_list)

            # memguard limit 해제
            rm_memguard_limit()
            rmmod_memguard()

    # memguard rmmod
    # rmmod_memguard()

    # 종료


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
        os.system(f'cd {dir_path} && rm -rf *')

    if not os.path.exists(dir_path):
        os.system(f'mkdir -p {dir_path}')

    main()