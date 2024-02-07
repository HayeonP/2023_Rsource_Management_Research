import yaml
import os
import subprocess
import multiprocessing
import time
from tqdm import tqdm


# perf-based table
budget_to_target_convert_table = {
    1000: 1000,
    2000: 2000,
    3000: 3150,
    4000: 4280,
    5000: 5440,
    6000: 6640,
    7000: 7880,
    204800: 204800,
}

def terminate_seqwr():
    cmd = "ssh root@192.168.0.11 \"ps -ax\" | grep sequential_write"

    while True:
        while True:
            try:
                result = subprocess.check_output(cmd, shell=True, universal_newlines=True)
                result = result.strip()
                result = result.split("\n")
                break
            except subprocess.CalledProcessError as e:
                if e.stderr is None: 
                    result = []
                    break
                print(f"Error: {e}")

        ps_info_list = []
        for line in result:
            ps_info = line.split(' ')
            ps_info = [v for v in ps_info if v != '']
            ps_info_list.append(ps_info)

        if len(ps_info_list) == 0: break

        for ps_info in ps_info_list:
            if len(ps_info) == 0: continue
            pid = ps_info[0]
            os.system(f"ssh root@192.168.0.11 \"kill -9 {pid}\"")

    return

def is_seqwr_executed():
    cmd = "ssh root@192.168.0.11 'ps -ax' | grep sequential_write"
    while True:
        try:
            result = subprocess.check_output(cmd, shell=True, universal_newlines=True)
            result = result.strip()
            result = result.split("\n")
            break
        except:
            time.sleep(1)
            continue
        
    if len(result) > 0:
        return True
    return False

def seqwr_workload(core, budget):
    os.system(f"ssh {ssh_address} \"taskset -c {core} /var/lib/lxc/linux1/rootfs/home/root/mg/tools/source/sequential_write -b {budget_to_target_convert_table[budget]} -s 64\" > /dev/null")
    time.sleep(1)
    return

def is_clguard_installed():
    kernel_module_list = str(os.popen(f'ssh {ssh_address} "lsmod"').read())
    kernel_module_list = kernel_module_list.split('\n')
    for kernel_module in kernel_module_list:
        if 'clguard' in kernel_module:
            return True
    return False

def insmod_clguard(clguard_name, target_cores, budget):
    # os.system(f'ssh {ssh_address} "sed -i \'6s/.*/BUDGET={budget}/g\' {exynos_clguard_dir}/run_{clguard_name}.sh"')
    os.system(f'ssh {ssh_address} "sed -i \'/TARGET_CORES=/ c\TARGET_CORES={target_cores}\' {exynos_clguard_dir}/run_{clguard_name}.sh"')
    os.system(f'ssh {ssh_address} "sed -i \'/BUDGET=/ c\BUDGET={budget}\' {exynos_clguard_dir}/run_{clguard_name}.sh"')
    os.system(f'ssh {ssh_address} "cd {exynos_clguard_dir} && sh run_{clguard_name}.sh"')
    time.sleep(1)

def rmmod_clguard(clguard_name):
    os.system(f'ssh {ssh_address} "cd {exynos_clguard_dir} && rmmod {clguard_name}.ko"')

def set_clguard_limit(label, target_cores, target_bandwidth):
    os.system(f'ssh {ssh_address} "echo set {label} {target_bandwidth} {target_cores} > {clguard_limit_dir}"')
    time.sleep(1)

def rm_clguard_limit(label):
    os.system(f'ssh {ssh_address} "echo rm {label} > {clguard_limit_dir}"')
    time.sleep(1)

def update_adas_config(label):
    # update svl auto experiment confis
    with open("yaml/svl_auto_experiment_configs.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    config["experiment_title"] = label
    config["max_iteration"] = adas_iteration
    config["duration"] = adas_duration

    with open("yaml/svl_auto_experiment_configs.yaml", "w") as f:
        yaml.dump(config, f)

    # update autoware analyzer config
    with open("yaml/autoware_analyzer.yaml", "r") as f:
        analyzer_config = yaml.load(f, Loader=yaml.FullLoader)

    analyzer_config["experiment_title"] = [label]
    analyzer_config["output_title"] = [label]

    with open("yaml/autoware_analyzer.yaml", "w") as f:
        yaml.dump(analyzer_config, f)


def adas_experiment(adas_budget, seqwr_budget):
    # clguard1: ADAS, clguard2: SeqWr
    if is_clguard_installed():
        rmmod_clguard('clguard1')
        rmmod_clguard('clguard2')
    # if is_seqwr_executed():
    #     terminate_seqwr()

    # Setup ADAS budget to clguard
    insmod_clguard('clguard1', '4-7', adas_budget)

    # ADAS (w/ Clguard) only
    label = f'{experiment_tag}_b{adas_budget}_adas_MP5000'
    update_adas_config(label)
    os.system(f'python3 svl_auto_experiment.py')
    time.sleep(1)
    os.system(f'python3 autoware_analyzer.py')

    # # ADAS (w/ Clguard) + Seqwr (w/o Clguard)
    # label = f'{experiment_tag}_b{adas_budget}_adas_seqwr{seqwr_budget}'
    # update_adas_config(label)

    # seqwr_process = multiprocessing.Process(target=seqwr_workload, args=(1, seqwr_budget,))
    # seqwr_process.start()

    # os.system(f'python3 svl_auto_experiment.py')

    # seqwr_process.terminate()
    # seqwr_process.join()
    # terminate_seqwr()

    # os.system(f'python3 autoware_analyzer.py')

    # # Setup SeqWr budget to Clguard
    # insmod_clguard('clguard2', '1-3', seqwr_budget)

    # # ADAS (w/ Clguard) + Seqwr (w/ Clguard)
    # label = f'{experiment_tag}_b{adas_budget}_adas_b{seqwr_budget}_seqwr'
    # update_adas_config(label)

    # seqwr_process = multiprocessing.Process(target=seqwr_workload, args=(1, 204800,))
    # seqwr_process.start()

    # os.system(f'python3 svl_auto_experiment.py')

    # seqwr_process.terminate()
    # seqwr_process.join()
    # terminate_seqwr()

    # os.system(f'python3 autoware_analyzer.py')

    rmmod_clguard('clguard1')
    # rmmod_clguard('clguard2')

if __name__ == '__main__':
    with open('yaml/clguard_auto_experiment.yaml') as f:
        configs = yaml.load(f, Loader=yaml.FullLoader)

    adas_iteration = configs['adas_iteration']
    adas_duration = configs['adas_duration']
    ssh_address = configs['ssh_address']
    exynos_clguard_dir = configs['exynos_clguard_dir']
    clguard_limit_dir = configs['clguard_limit_dir']
    experiment_tag = configs['experiment_tag']

    adas_budget_list = configs['adas_budget']
    seqwr_budget_list = configs['seqwr_budget']

    # for i in range(len(adas_budget_list)):
    #     adas_budget = adas_budget_list[i]
    #     seqwr_budget = seqwr_budget_list[i]
    for adas_budget in adas_budget_list:
        # for seqwr_budget in seqwr_budget_list:
        adas_experiment(adas_budget, 1000)