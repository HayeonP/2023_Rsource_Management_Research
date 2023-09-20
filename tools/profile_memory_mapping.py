import os
import time
import datetime

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

def profile_ps_info(label):
    output_dir = 'log/'+label
    os.system('mkdir -p ' + output_dir)
    path = output_dir +'/ps_info.txt'
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

def parse_configs(path):
    output = {}
    with open(path, 'r') as f:
        raw_data = f.readlines()
    
    for i, line in enumerate(raw_data):
        line = line.replace(' ', '')
        line = line.split('#')[0]

        if 'target_tasks:' in line:
            target_tasks = []
            for j in range(i, len(raw_data)):
                if j != i and ':' in raw_data[j]: break
                task_name = raw_data[j]
                task_name = task_name.split(':')[-1]
                task_name = task_name.replace(' ', '')
                task_name = task_name.split('#')[0]                
                task_name = task_name.replace('[', '')
                task_name = task_name.replace(']', '')
                task_name = task_name.replace('\n', '')
                task_name = task_name.split(',')

                task_name = [v for v in task_name if v != '']
                target_tasks.extend(task_name)
                

            output['target_tasks'] = target_tasks
        elif ':' in line:
            name = line.split(':')[0]
            name = name.replace('\"','')
            name = name.replace('\'','')
            value = line.split(':')[-1]
            value = value.split('\n')[0]
            value = value.replace('\"', '')
            value = value.replace('\'', '')
        output[name] = value

    return output

if __name__ == '__main__':
    configs = parse_configs('configs/memory_mapping.yaml')

    ps_info = profile_ps_info(configs['label'])    
    
    name_list = configs['target_tasks']

    task_info = {}
    for name in name_list:
        task_info[name] = get_task_info_by_name(name, ps_info)

    pid_list = []
    tid_list = []
    for key in task_info:
        for info in task_info[key]:
            if info['PID'] not in pid_list: pid_list.append(info['PID'])
            if info['TID'] not in tid_list: tid_list.append(info['TID'])

    os.system('rm -r pmap_log/*')
    os.system('mkdir -p pmap_log/' + configs['label'])
    
    iter = 0
    max_iter = int(configs['max_iter'])
    start_time = time.time()
    while True:
        for pid in pid_list:
            path = 'pmap_log/' + configs['label'] + '/pid-' + str(pid) + '_iter-' + str(iter) + '.txt'
            with open(path, 'w') as f:                
                f.write(str(time.time()) + '\n')    
            os.system('pmap -X ' + str(pid) + ' >> ' + path + '&')
        for tid in tid_list:
            path = 'pmap_log/' + configs['label'] + '/tid-' + str(tid) + '_iter-' + str(iter) + '.txt'
            with open(path, 'w') as f:                
                f.write(str(time.time()) + '\n')
            os.system('pmap -X ' + str(tid) + ' >> ' + path + '&')
        
        time.sleep(SLEEP_DURATION)

        iter = iter + 1
        if iter >= max_iter: break
    end_time = time.time()

    print('# Profiling duration:',end_time - start_time)