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
    for i in range(10):
        try:
            result = subprocess.check_output(cmd, shell=True, universal_newlines=True)
            result = result.strip()
            result = result.split("\n")
            break
        except:
            result = []
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
    for i in range(10):
        try:
            kernel_module_list = str(os.popen(f'ssh {ssh_address} "lsmod"').read())
            kernel_module_list = kernel_module_list.split('\n')
            for kernel_module in kernel_module_list:
                if 'clguard' in kernel_module:
                    return True
        except:
            time.sleep(1)
            continue

    return False

def set_clguard_parameters(clguard_name, manager_period, profiling_period, target_cores, budget):
    try:
        # Setup MP, PP, TARGET_CORES, BUDGET
        os.system(f'ssh {ssh_address} "sed -i \'/MP=/ c\MP={manager_period}\' {exynos_clguard_dir}/run_{clguard_name}.sh"')
        os.system(f'ssh {ssh_address} "sed -i \'/PP=/ c\PP={profiling_period}\' {exynos_clguard_dir}/run_{clguard_name}.sh"')
        os.system(f'ssh {ssh_address} "sed -i \'/TARGET_CORES=/ c\TARGET_CORES={target_cores}\' {exynos_clguard_dir}/run_{clguard_name}.sh"')
        os.system(f'ssh {ssh_address} "sed -i \'/BUDGET=/ c\BUDGET={budget}\' {exynos_clguard_dir}/run_{clguard_name}.sh"')

        return True
    except:
        return False

def insmod_clguard(clguard_name):
    os.system(f'ssh {ssh_address} "cd {exynos_clguard_dir} && sh run_{clguard_name}.sh"')
    time.sleep(1)

def rmmod_clguard(clguard_name):
    os.system(f'ssh {ssh_address} "cd {exynos_clguard_dir} && rmmod {clguard_name}.ko"')

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


def adas_experiment():
    # Clean up Modules
    if is_clguard_installed():
        rmmod_clguard('clguard1')
        rmmod_clguard('clguard2')
    if is_seqwr_executed():
        terminate_seqwr()

    # insert clguard1 module
    if run_clguard1:
        set_clguard_parameters('clguard1', clguard1_mp, clguard1_pp, clguard1_target_cores, clguard1_budget)
        insmod_clguard('clguard1')

    # insert clguard2 module
    if run_clguard2:
        set_clguard_parameters('clguard2', clguard2_mp, clguard2_pp, clguard2_target_cores, clguard2_budget)
        insmod_clguard('clguard2')

    # run sequential write
    seqwr_process_list = []
    if run_seqwr:
        for i, core in enumerate(seqwr_core_list):
            seqwr_process = multiprocessing.Process(target=seqwr_workload, args=(core, seqwr_budget_list[i],))
            seqwr_process.start()
    
    update_adas_config(experiment_title)
    os.system(f'python3 svl_auto_experiment.py')

    if run_seqwr:
        for seqwr_process in seqwr_process_list:
            seqwr_process.terminate()
            seqwr_process.join()
        terminate_seqwr()

    os.system(f'python3 autoware_analyzer.py')

    # Clean up Modules
    if run_clguard1:
        rmmod_clguard('clguard1')
    if run_clguard2:
        rmmod_clguard('clguard2')

if __name__ == '__main__':
    with open('yaml/clguard_single_exp.yaml') as f:
        configs = yaml.load(f, Loader=yaml.FullLoader)

    adas_iteration = configs['adas_iteration']
    adas_duration = configs['adas_duration']
    ssh_address = configs['ssh_address']
    exynos_clguard_dir = configs['exynos_clguard_dir']
    experiment_title = configs['experiment_title']

    run_seqwr = configs['run_seqwr']
    seqwr_core_list = configs['seqwr_core_list']
    seqwr_budget_list = configs['seqwr_budget_list']

    run_clguard1 = configs['run_clguard1']
    clguard1_target_cores = configs['clguard1_target_cores']
    clguard1_budget = configs['clguard1_budget']
    clguard1_mp = configs['clguard1_mp']
    clguard1_pp = configs['clguard1_pp']

    run_clguard2 = configs['run_clguard2']
    clguard2_target_cores = configs['clguard2_target_cores']
    clguard2_budget = configs['clguard2_budget']
    clguard2_mp = configs['clguard2_mp']
    clguard2_pp = configs['clguard2_pp']

    adas_experiment()
