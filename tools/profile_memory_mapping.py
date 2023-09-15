import os
import time
import datetime

PS_INFO_PATH='data/a.txt' # Output of ps -eLf. LWP is tid
SLEEP_DURATION=0.05

def parse_item(line):    
    line = line.split(' ')
    item_list = [item for item in line if item != '']
    item_list[-1] = item_list[-1][:-1]
    return item_list

def parse_ps_line(line, item_list):
    output = {}
    line = line.split(' ')
    parsed_line = [item for item in line if item != '']
    
    for i, item in enumerate(item_list):
        if item == 'CMD':
            cmd = ''
            for j in range(i,len(parsed_line)): cmd = cmd + parsed_line[j]
            output[item] = cmd[:-1] # Remove \n
        else:
            output[item] = parsed_line[i]
        
    return output

def profile_ps_info():
    current_datetime = datetime.datetime.now().strftime('%y%m%d')
    os.system('mkdir data/'+current_datetime)
    path = 'data/'+current_datetime+'/ps_info.txt'
    os.system('ps -eLF > '+path)

    with open(path, 'r') as f:
        data = f.readlines()
    
    item_list = []
    ps_info = []
    for i, line in enumerate(data):
        if i == 0:
            item_list = parse_item(line)
            continue
        parsed_line = parse_ps_line(line, item_list)
        ps_info.append(parsed_line)
    
    return ps_info

def get_task_info_by_name(name, ps_info):
    task_info = []

    for line in ps_info:
        if name in line['CMD']: task_info.append({'PID': line['PID'], 'TID': line['LWP']})

    return task_info

def sec_to_iter(sec):
    return sec / SLEEP_DURATION

if __name__ == '__main__':        
    ps_info = profile_ps_info()    
    
    name_list = [
        'rosmaster',
        'rosout',
        'rubis_autorunner',
        'static_transform_publisher',
        'vector_map_loader',
        'points_map_loader',
        'svl_sensing',
        'voxel_grid_filter',
        'ndt_matching',
        'autoware_config_msgs',
        'ray_ground_filter',
        'lidar_euclidean_cluster_detect',
        'visualize_detected_objects',
        'op_global_planner',
        'op_common_params',
        'op_trajectory_generator',
        'op_behavior_selector',
        'pure_pursuit',
        'twist_filter'
    ]

    task_info = {}
    for name in name_list:
        task_info[name] = get_task_info_by_name(name, ps_info)

    pid_list = []
    tid_list = []
    for key in task_info:
        for info in task_info[key]:
            if info['PID'] not in pid_list: pid_list.append(info['PID'])
            if info['TID'] not in tid_list: tid_list.append(info['TID'])

    current_datetime = datetime.datetime.now().strftime('%y%m%d')
    os.system('rm -r pmap_log/*')
    os.system('mkdir -p pmap_log/' + str(current_datetime))
    
    iter = 0
    max_iter = sec_to_iter(5)
    start_time = time.time()
    while True:
        for pid in pid_list:
            path = 'pmap_log/' + current_datetime + '/pid-' + str(pid) + '_iter-' + str(iter) + '.txt'
            with open(path, 'w') as f:                
                f.write(str(time.time()) + '\n')    
            os.system('pmap -X ' + str(pid) + ' >> ' + path + '&')
        for tid in tid_list:
            path = 'pmap_log/' + current_datetime + '/tid-' + str(tid) + '_iter-' + str(iter) + '.txt'
            with open(path, 'w') as f:                
                f.write(str(time.time()) + '\n')
            os.system('pmap -X ' + str(tid) + ' >> ' + path + '&')
        
        time.sleep(SLEEP_DURATION)

        iter = iter + 1
        if iter >= max_iter: break
    end_time = time.time()

    print('Profiling duration:',end_time - start_time)

