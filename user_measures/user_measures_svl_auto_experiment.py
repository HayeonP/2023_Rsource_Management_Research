import os
import subprocess
import threading
import time
import rospy
import yaml
from sensor_msgs.msg import Imu
from geometry_msgs.msg import TwistStamped
from autoware_msgs.msg import NDTStat
from autoware_msgs.msg import VehicleCmd
import scripts.slack_library as slack_library
import scripts.svl_scenario as svl
import signal
import multiprocessing


is_experiment_running = threading.Event()
is_scenario_started = threading.Event()
is_autorunner_started = threading.Event()
is_autorunner_killed = threading.Event()
is_sensing_to_detection_autorunner_started = threading.Event()
is_experiment_finished = threading.Event()
barrier = threading.Barrier(2)

configs = {}
target_environment = 'null'
slack_webhook = 'null'

def autorunner():
    while True:
        if is_experiment_running.is_set(): break
    while True:
        time.sleep(1)
        if is_scenario_started.is_set():
            if target_environment == 'exynos':
                if configs['autorunner_mode'] == 'LKAS': 
                    os.system('ssh root@' + configs[target_environment]['target_ip'] + ' \"lxc-attach -n linux1 -- /home/root/scripts/cubetown_lkas_autorunner.sh\"')
                elif configs['autorunner_mode'] == 'FULL': 
                    os.system('ssh root@' + configs[target_environment]['target_ip'] + ' \"lxc-attach -n linux1 -- /home/root/scripts/_cubetown_autorunner_4_planning.sh\" &')
                    os.system('ssh root@' + configs[target_environment]['target_ip'] + ' \"lxc-attach -n linux1 -- /home/root/scripts/_cubetown_autorunner_5_control.sh\" &')
                    # os.system('ssh root@' + configs[target_environment]['target_ip'] + ' \"lxc-attach -n linux1 -- /home/root/scripts/cubetown_full_autorunner.sh\"')
                else:
                    print('Invalidate mode:', configs['autorunner_mode'])
            elif target_environment == 'desktop':
                if configs['autorunner_mode'] == 'LKAS': 
                    os.system('roslaunch rubis_autorunner cubetown_lkas_autorunner.launch')                                                
                elif configs['autorunner_mode'] == 'FULL':
                    os.system('roslaunch rubis_autorunner cubetown_full_autorunner.launch')
                else:
                    print('Invalidate mode:', configs['autorunner_mode'])
            else:
                print('Wrong target environment: ', target_environment)
                exit()
            print('- Autorunner: Start Autorunner')
        else:
            continue
        if not is_experiment_running.is_set(): break
        print('- Autorunner: Unlock barrier')
        barrier.wait()
        print('- Autorunner: barrier is passed')

    print('- Autorunner: Turn off Autorunner thread')

    return

def save_result(iter, experiment_info):
    # Response time
    output_path = 'results/'+configs['experiment_title']+'/'+str(iter)
    os.system('mkdir '+output_path)
    if configs['target_environment'] == 'desktop':
        os.system('cp -r '+configs[target_environment]['response_time_path']+ ' ' + output_path)
    elif configs['target_environment'] == 'exynos':
        os.system('scp -r root@' + configs[target_environment]['target_ip'] +':'+configs[target_environment]['response_time_path']+ ' ' + output_path)
    else:
        print('[Error] Invalid target environment:',configs['target_envirnment'])

    # Center line
    os.system('mv ./center_line.csv ' + output_path)
    
    # Center offset
    os.system('mv ./center_offset.csv ' + output_path)
    
    # Experiment info
    experiment_info_path = output_path + '/experiment_info.yaml'
    with open(experiment_info_path, 'w') as f: yaml.dump(experiment_info, f, default_flow_style=False)

    return

def kill_autorunner(mode='full'):
    if mode == 'exception':
        cmd = configs[target_environment]['termination_cmd'].replace('terminate_exynos', 'terminate_partial_exynos')
        print(cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        p.wait()
        
        while True:
            time.sleep(1)
            _output = str(os.popen('rosnode list').read())
            if 'op_global_planner' not in _output: break

    else:
        p = subprocess.Popen(configs[target_environment]['termination_cmd'], shell=True, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        p.wait()
        
        while True:
            time.sleep(1)
            _output = str(os.popen('rosnode list').read())
            if 'ndt_matching' not in _output: break
    return

def imu_cb(msg):
    if is_experiment_running.is_set():
        is_scenario_started.set()
    else:
        is_scenario_started.clear()
    return

def vehicle_cmd_cb(msg):
    if is_experiment_running.is_set() and msg.twist_cmd.twist.linear.x > 0.0:
        is_autorunner_started.set()
    else:
        is_autorunner_started.clear()
    return

def perf_thread_main(type='all'):
    if target_environment == 'desktop': return
    elif target_environment == 'exynos':
        if type == 'all':
            os.system('ssh root@' + configs[target_environment]['target_ip'] +  ' \"perf stat -e l3d_cache_refill -C ' + configs['all_cores'] +' &> /home/root/perf_output.txt\"')
        elif type == 'ADAS':
            os.system('ssh root@' + configs[target_environment]['target_ip'] +  ' \"perf stat -e l3d_cache_refill -C ' + configs['ADAS_cores'] +' &> /home/root/perf_ADAS_output.txt\"')
        else:
            print('Wrong time is given to perf_thread_main(): ', type)
            exit()
    return

def parse_ps_output(ps_output):
    ps_info_list = []
    for line in ps_output:        
        ps_info = line.split(' ')
        ps_info = [v for v in ps_info if v != '']
        ps_info_list.append(ps_info)
    return ps_info_list


def kill_perf():    
    if target_environment == 'exynos':
        os.system('ssh root@' + configs[target_environment]['target_ip'] +  ' \"ps ax | grep perf > ps_output.txt\"')
        os.system('scp root@' + configs[target_environment]['target_ip'] + ':/home/root/ps_output.txt .')
        
        ps_output = str(os.popen('cat ps_output.txt').read()).split('\n')
        ps_info_list = parse_ps_output(ps_output)

        for ps_info in ps_info_list:
            if len(ps_info) == 0: continue
            pid = ps_info[0]
            os.system('ssh root@' + configs[target_environment]['target_ip'] +  ' \"kill -2 ' + pid + '\"')
        
        os.system('ssh root@' + configs[target_environment]['target_ip'] +  ' \"rm /home/root/ps_output.txt\"')        
        os.system('rm ps_output.txt')

def get_avg_perf_event_cnt_per_sec(event, type='all'):
    if target_environment != 'exynos': return
    path = 'none'
    if type == 'all':
        os.system('scp root@' + configs[target_environment]['target_ip'] + ':/home/root/perf_output.txt .')    
        os.system('ssh root@' + configs[target_environment]['target_ip'] +  ' \"rm /home/root/perf_output.txt\"')        
        path = 'perf_output.txt'
    elif type == 'ADAS':
        os.system('scp root@' + configs[target_environment]['target_ip'] + ':/home/root/perf_ADAS_output.txt .')    
        os.system('ssh root@' + configs[target_environment]['target_ip'] +  ' \"rm /home/root/perf_ADAS_output.txt\"')
        path = 'perf_ADAS_output.txt'
    else:
        print('Wrong type is given to get_perf_avg_event_cnt_per_sec(): ',type)
        exit()    

    event_output = []
    duration_output = []
    with open(path) as f:
        lines = f.readlines()
        for line in lines:            
            if event in line:
                event_output = line.split(' ')
            if 'seconds time elapsed' in line:
                duration_output = line.split(' ')

    event_cnt = -1        
    for v in event_output: 
        if v != '':            
            event_cnt = float(v.replace(',',''))
            break
    duration = -1.0
    for v in duration_output: 
        if v != '':
            duration = float(v)
            break

    avg_event_cnt = event_cnt / duration

    return avg_event_cnt

def calculate_avg_memory_bandwidth_usage(l3d_cache_refill_event_cnt_per_sec):
    cache_line_size = 64 # Bytes
    avg_memory_bandwidth_usage = l3d_cache_refill_event_cnt_per_sec * cache_line_size * 0.000000001
    return avg_memory_bandwidth_usage

def run_stream():
    os.system("ssh root@192.168.0.11 'taskset -c 1-3 /home/root/sdd/STREAM/STREAM_64MB_100000'")
    return

def kill_stream():
    cmd = "ssh root@192.168.0.11 \"ps -ax\" | grep STREAM_64MB_100000"

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

def experiment_manager(main_thread_pid):
    print('- Manager: Start manager')
    svl_scenario = svl.svl_scenario(configs['svl_cfg_path'])

    # print(configs[target_environment]['target_ip'])
    # exit(0)
    # os.system(f'scp -r exynos_scripts/* root@{configs[target_environment]['target_ip']}:/var/lib/lxc/linux1/rootfs/home/root/scripts')
    os.system('scp -r exynos_scripts/* root@192.168.0.11:/var/lib/lxc/linux1/rootfs/home/root/scripts')

    os.system('ssh root@' + configs[target_environment]['target_ip'] + ' \"lxc-attach -n linux1 -- /home/root/scripts/_cubetown_autorunner_1_sensing.sh\" &')
    os.system('ssh root@' + configs[target_environment]['target_ip'] + ' \"lxc-attach -n linux1 -- /home/root/scripts/_cubetown_autorunner_2_localization.sh\" &')
    os.system('ssh root@' + configs[target_environment]['target_ip'] + ' \"lxc-attach -n linux1 -- /home/root/scripts/_cubetown_autorunner_3_detection.sh\" &')
    print('hihi')

    # Threads
    autorunner_thread = threading.Thread(target=autorunner)
    autorunner_thread.start()
    # Check rosbridge is started
    while True:
        _output = str(os.popen('rosnode list').read())
        if 'rosbridge_websocket' in _output: break


    for i in range(configs['max_iteration']):
        experiment_info = {}
        is_collapsed = False        
        is_experiment_running.set()

        perf_thread_for_ADAS_profiling = threading.Thread(target=perf_thread_main, args=('ADAS',))
        perf_thread_for_profiling = threading.Thread(target=perf_thread_main, args=('all',))

        # Initialize SVL scenario
        print('- Manager: Init svl scenario')
        svl_scenario.init()
        while not is_autorunner_started.is_set():
            svl_scenario.run(timeout=1, is_init=True)
        
        # Start Experiment
        print('- Mnager: Start Experiment')
        if configs['run_stream']:
            stream_process = multiprocessing.Process(target=run_stream, args=())
            stream_process.start()
            time.sleep(5)
        start_writing_position_info()             
        perf_thread_for_ADAS_profiling.start()
        perf_thread_for_profiling.start()
        is_collapsed, collapsed_position = svl_scenario.run(timeout=configs['duration'], label='Iteration: ' + str(i+1)+'/'+str(configs['max_iteration']))        
        kill_perf()
        stop_writing_position_info()
        if configs['run_stream']:
            stream_process.terminate()
            # stream_process.join()
            kill_stream()
            time.sleep(2)

        # Terminate
        print('before terminate')
        kill_autorunner('exception')
        print('after terminate')
        perf_thread_for_ADAS_profiling.join()
        perf_thread_for_profiling.join()
        is_autorunner_started.clear()
        is_scenario_started.clear()
        
        # Get experiment_info
        experiment_info['is_collaped'] = is_collapsed
        experiment_info['collapsed_position'] = collapsed_position
        
        l3d_cache_refill_event_cnt_of_all_cores = get_avg_perf_event_cnt_per_sec('l3d_cache_refill', type='all')
        l3d_cache_refill_event_cnt_of_ADAS_cores = get_avg_perf_event_cnt_per_sec('l3d_cache_refill', type='ADAS')
        experiment_info['l3d_cache_refill_event_cnt_of_all_cores(per sec)'] = l3d_cache_refill_event_cnt_of_all_cores
        experiment_info['l3d_cache_refill_event_cnt_of_ADAS_cores(per sec)'] = l3d_cache_refill_event_cnt_of_ADAS_cores
        experiment_info['avg_total_memory_bandwidth_usage(GB/s)'] = calculate_avg_memory_bandwidth_usage(l3d_cache_refill_event_cnt_of_all_cores)

        print('- Manager: Save result')
        save_result(i, experiment_info) 
        # if not is_experiment_running.is_set():
        #     message = 'Experiment is finished: '+configs['experiment_title']
        #     payload = {"text": message}
        #     slack_library.send_slack_message(payload, slack_webhook)
        #     break
        
        if i+1 == int(configs['max_iteration']):
            is_experiment_running.clear()
            break
        
        print('- Manager: Unlock barrier')
        barrier.wait()
        print('- Manager: Barrier is passed')
        barrier.reset()
        time.sleep(3)  

    kill_autorunner()              

    return os.kill(main_thread_pid, signal.SIGQUIT)

def start_writing_position_info():
    subprocess.Popen('python3 scripts/write_position_info.py', shell=True, executable='/bin/bash')
    return

def stop_writing_position_info():
    _output = str(os.popen('ps au | grep center_offset').read())
    _output = _output.split('\n')
    for line in _output:    
        if not 'write_position_info.py' in line: continue
        pid = -1
        for v in line.split(' '):
            try: pid = int(v)
            except: continue
            break

        if pid != -1: os.kill(pid, signal.SIGINT)
    
    return

if __name__ == '__main__':
    main_thread_pid = os.getpid()

    # slack_webhook = slack_library.get_slack_webhook()    

    with open('yaml/svl_auto_experiment_configs.yaml') as f:
        configs = yaml.load(f, Loader=yaml.FullLoader)

    # Setup target environment
    target_environment = configs['target_environment']
    if target_environment not in ['desktop', 'exynos']:
        print('[Error] Invalid target environment')
        exit()

    experiment_title = configs['experiment_title']
    if target_environment != 'desktop': target_ip = configs[target_environment]['target_ip']

    # Setup ssh key of host to the exynos board
    if target_environment == 'exynos':
        os.system('bash scripts/setup_ssh_key_to_board.bash')

    # Create result dir
    does_dir_exist = os.path.exists('results/'+configs['experiment_title'])
    if configs['experiment_title'] == 'test':
        if does_dir_exist:
            os.system('rm -r results/'+configs['experiment_title'])
    else:
        if does_dir_exist:
            print('[Error] Experiment result exists already')
            exit()
    os.system('mkdir -p results/'+configs['experiment_title'])
    os.system('mkdir -p results/'+configs['experiment_title']+'/configs')
    
    # select params for the measure
    scenario = configs['svl_cfg_path'].split('svl_scenario_')[1]
    
    if scenario == 'handling.yaml':
        measure = '_handling'
    elif scenario == 'braking.yaml':
        measure = '_braking'
    elif scenario == 'lane_change.yaml':
        measure = '_lane_change'
    else:
        measure = ''
    
    # Move params to the target board ant backup it
    if target_environment == 'desktop':
        os.system(f'₩ㅌ yaml/cubetown_autorunner_params{measure}.yaml ~/rubis_ws/src/rubis_autorunner/cfg/cubetown_autorunner/cubetown_autorunner_params.yaml')
        os.system(f'cp yaml/cubetown_autorunner_params{measure}.yaml results/{experiment_title}/configs')
    elif target_environment == 'exynos':        
        os.system(f'scp -r yaml/cubetown_autorunner_params{measure}.yaml root@{target_ip}:/var/lib/lxc/linux1/rootfs/home/root/rubis_ws/src/rubis_autorunner/cfg/cubetown_autorunner/cubetown_autorunner_params.yaml')
        print(f'cp yaml/cubetown_autorunner_params{measure}.yaml results/{experiment_title}/configs')
        os.system(f'cp yaml/cubetown_autorunner_params{measure}.yaml results/{experiment_title}/configs')
    
    
    # Backup autoware params
    if target_environment == 'desktop':
        os.system(f'cp ~/rubis_ws/src/rubis_autorunner/cfg/cubetown_autorunner/cubetown_autorunner_params{measure}.yaml ' + 'results/'+configs['experiment_title']+'/configs')
    elif target_environment == 'exynos':
        os.system(f'scp -r root@' + configs[target_environment]['target_ip'] +':/var/lib/lxc/linux1/rootfs/home/root/rubis_ws/src/rubis_autorunner/cfg/cubetown_autorunner/cubetown_autorunner_params.yaml ' + 'results/'+configs['experiment_title']+'/configs')        
        # os.system('scp -r root@' + configs[target_environment]['target_ip'] +':/var/lib/lxc/linux1/rootfs/opt/ros/melodic/share/rubis_autorunner/cfg/cubetown_autorunner/cubetown_autorunner_params.yaml ' + 'results/'+configs['experiment_title']+'/configs')        

    # Backup svl scenario
    os.system(f'cp yaml/svl_scenario{measure}.yaml ' + 'results/'+configs['experiment_title']+'/configs')

    # Backup image name
    with open('results/'+configs['experiment_title']+'/configs/image.txt', 'w') as f:
        f.write(configs['adas_image_name'])      

    # Backup duration time
    with open('results/'+configs['experiment_title']+'/configs/duration.txt', 'w') as f:
        f.write(str(configs['duration']))  

    manager_thread = threading.Thread(target=experiment_manager, args=(main_thread_pid, ))    
    manager_thread.start()

    rospy.init_node('svl_auto_experiment', anonymous=True)
    rospy.Subscriber('imu_raw', Imu, imu_cb)
    rospy.Subscriber('vehicle_cmd', VehicleCmd, vehicle_cmd_cb)
    rospy.spin()


