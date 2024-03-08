import yaml
import os
import subprocess
import multiprocessing
import time
from tqdm import tqdm
import rospy
from autoware_msgs.msg import VehicleCmd
import rospy


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

def update_adas_config(label, user_measure):
    # update svl auto experiment confis
    with open("yaml/svl_auto_experiment_configs.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    config["experiment_title"] = label
    config["max_iteration"] = adas_iteration
    # select user measure scenario
    config["svl_cfg_path"] = config["svl_cfg_path"].split("svl_scenario")[0] + "svl_scenario_" + user_measure + ".yaml"
    if user_measure == 'handling':
        config["duration"] = 100
    else:
        config["duration"] = 20

    with open("yaml/svl_auto_experiment_configs.yaml", "w") as f:
        yaml.dump(config, f)

    # update autoware analyzer config
    with open("yaml/autoware_analyzer.yaml", "r") as f:
        analyzer_config = yaml.load(f, Loader=yaml.FullLoader)

    analyzer_config["experiment_title"] = [label]
    analyzer_config["output_title"] = [label]

    with open("yaml/autoware_analyzer.yaml", "w") as f:
        yaml.dump(analyzer_config, f)

def profile_bandwidth(label, adas_iteration, adas_budget):
    rospy.init_node('profiling_bandwidth_for_clguard_experiment_node')

    for i in range(adas_iteration):
        bw_profiler_title = f'{label}_it{i}'
        os.system(f'sed -i \'/profiling_duration:/ c\profiling_duration: 80\' {host_bandwidth_profiler_dir}/configs/bw_profiler.yaml')
        os.system(f'sed -i \'/label:/ c\label: {bw_profiler_title}\' {host_bandwidth_profiler_dir}/configs/bw_profiler.yaml')
        os.system(f'sed -i \'/profiling_frequency:/ c\profiling_frequency: 200\' {host_bandwidth_profiler_dir}/configs/bw_profiler.yaml')
        os.system(f'sed -i \'/target_cores:/ c\\target_cores: 4-7\' {host_bandwidth_profiler_dir}/configs/bw_profiler.yaml')
        os.system(f'sed -i \'/budget:/ c\\budget: {adas_budget}\' {host_bandwidth_profiler_dir}/configs/bw_profiler.yaml')

        rospy.wait_for_message('/vehicle_cmd', VehicleCmd, timeout=None)

        while not rospy.is_shutdown():
            # rubis_current_pose_twist_msg = rospy.wait_for_message('/rubis_current_pose_twist', PoseTwistStamped, timeout=None)
            # current_velocity = rubis_current_pose_twist_msg.twist.twist.linear.x
            # if current_velocity > 20: continue
            current_vehicle_cmd = rospy.wait_for_message('/vehicle_cmd', VehicleCmd, timeout=None)
            if current_vehicle_cmd.ctrl_cmd.linear_velocity < 1: continue
            result = subprocess.check_output("ssh root@192.168.0.11 'cat /sys/kernel/debug/clguard1/config'", shell=True, universal_newlines=True)
            with open(f'results/{label}/configs/it{i}_clguard_config_start.txt', 'w') as f:
                f.write(result)
            os.system(f'cd {host_bandwidth_profiler_dir} && sh profile_bandwidth.sh')
            break
        
        while True:
            try:
                current_vehicle_cmd = rospy.wait_for_message('/vehicle_cmd', VehicleCmd, timeout=5)
            except:
                break
        print("@@@@ rospy.spin is over")
        result = subprocess.check_output("ssh root@192.168.0.11 'cat /sys/kernel/debug/clguard1/config'", shell=True, universal_newlines=True)
        with open(f'results/{label}/configs/it{i}_clguard_config_end.txt', 'w') as f:
            f.write(result)

    print('code_end')


def start_experiment(measure, adas_budget, seqwr_budget, seqwr_clguard):
    # clguard1: ADAS, clguard2: SeqWr
    if is_clguard_installed():
        rmmod_clguard('clguard1')
        rmmod_clguard('clguard2')
    # if is_seqwr_executed():
    #     terminate_seqwr()
    
    # ADAS only (w/o Clguard)
    if not adas_budget and not seqwr_budget:
        label = f'{experiment_tag}_{measure}_b{adas_budget}_adas_only'
        update_adas_config(label, measure)

        bw_profiling_process = multiprocessing.Process(target=profile_bandwidth, args=(label, adas_iteration, adas_budget,))
        bw_profiling_process.start()

        os.system(f'python3 user_measures_svl_auto_experiment.py')

        bw_profiling_process.terminate()
        bw_profiling_process.join()

        time.sleep(1)
        os.system(f'python3 user_measures_autoware_analyzer.py')

    # ADAS only (w/ Clguard)
    elif adas_budget and not seqwr_budget:
        # Setup ADAS budget to clguard
        insmod_clguard('clguard1', '4-7', adas_budget)
        
        label = f'{experiment_tag}_{measure}_b{adas_budget}_adas_only'
        update_adas_config(label, measure)

        bw_profiling_process = multiprocessing.Process(target=profile_bandwidth, args=(label, adas_iteration, adas_budget,))
        bw_profiling_process.start()

        os.system(f'python3 user_measures_svl_auto_experiment.py')

        seqwr_process.terminate()
        bw_profiling_process.terminate()
        seqwr_process.join()
        bw_profiling_process.join()
        terminate_seqwr()

        os.system(f'python3 user_measures_autoware_analyzer.py')

        rmmod_clguard('clguard1')

    # ADAS (w/ Clguard) + Seqwr (w/ Clguard)
    elif adas_budget and seqwr_budget and seqwr_clguard == 'y':
        # Setup ADAS budget to clguard
        insmod_clguard('clguard1', '4-7', adas_budget)
        # Setup SeqWr budget to Clguard
        insmod_clguard('clguard2', '1-3', seqwr_budget)

        label = f'{experiment_tag}_{measure}_b{adas_budget}_adas_b{seqwr_budget}_seqwr'
        update_adas_config(label, measure)

        seqwr_process = multiprocessing.Process(target=seqwr_workload, args=(1, 204800,))
        bw_profiling_process = multiprocessing.Process(target=profile_bandwidth, args=(label, adas_iteration, adas_budget,))
        seqwr_process.start()
        bw_profiling_process.start()

        os.system(f'python3 user_measures_svl_auto_experiment.py')

        seqwr_process.terminate()
        bw_profiling_process.terminate()
        seqwr_process.join()
        bw_profiling_process.join()
        terminate_seqwr()

        os.system(f'python3 user_measures_autoware_analyzer.py')
    
        rmmod_clguard('clguard1')
        rmmod_clguard('clguard2')
    
    # ADAS (w/ Clguard) + Seqwr (w/o Clguard)
    elif adas_budget and seqwr_budget and seqwr_clguard == 'n':
        # Setup ADAS budget to clguard
        insmod_clguard('clguard1', '4-7', adas_budget)
        
        label = f'{experiment_tag}_{measure}_b{adas_budget}_adas_seqwr{seqwr_budget}'
        update_adas_config(label, measure)

        seqwr_process = multiprocessing.Process(target=seqwr_workload, args=(1, seqwr_budget,))
        bw_profiling_process = multiprocessing.Process(target=profile_bandwidth, args=(label, adas_iteration, adas_budget,))
        seqwr_process.start()
        bw_profiling_process.start()

        os.system(f'python3 user_measures_svl_auto_experiment.py')

        seqwr_process.terminate()
        bw_profiling_process.terminate()
        seqwr_process.join()
        bw_profiling_process.join()
        terminate_seqwr()

        os.system(f'python3 user_measures_autoware_analyzer.py')

        rmmod_clguard('clguard1')


if __name__ == '__main__':
    with open('yaml/user_measures_auto_experiment.yaml') as f:
        configs = yaml.load(f, Loader=yaml.FullLoader)

    adas_iteration = configs['adas_iteration']
    ssh_address = configs['ssh_address']
    exynos_clguard_dir = configs['exynos_clguard_dir']
    clguard_limit_dir = configs['clguard_limit_dir']
    experiment_tag = configs['experiment_tag']
    host_bandwidth_profiler_dir = configs['host_bandwidth_profiler_dir']

    adas_budget_list = configs['adas_budget']
    seqwr_budget_list = configs['seqwr_budget']
    seqwr_clguard = configs['seqwr_clguard']

    scenario_list = configs['user_measure_scenario']
    seqwr_clguard = configs['seqwr_clguard']
    
    for scenario in scenario_list:
        for i in range(len(adas_budget_list)):
            adas_budget = adas_budget_list[i]
            seqwr_budget = seqwr_budget_list[i]
            start_experiment(scenario, adas_budget, seqwr_budget, seqwr_clguard)