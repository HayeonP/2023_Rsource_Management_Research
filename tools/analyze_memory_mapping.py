import os
import yaml
from tqdm import tqdm
import matplotlib.pyplot as plt
import csv

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

def parse_pmap_line(line, item_list):
    output = {}
    line = line.split(' ')
    
    parsed_line = [item for item in line if item != '']

    for i, item in enumerate(item_list):
        if item == 'Mapping':
            cmd = ''
            for j in range(i,len(parsed_line)): cmd = cmd + parsed_line[j]
            output[item] = cmd[:-1] # Remove \n
        else:
            output[item] = parsed_line[i]
    
    return output

def profile_ps_info(path):

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

def get_pid_name_mapping_from_task_info(task_info):
    output = {}
    for key in task_info:
        for v in task_info[key]:
            if str(v['PID']) not in output: output[str(v['PID'])] = key 

    return output

def get_tid_name_mapping_from_task_info(task_info):
    output = {}
    for key in task_info:
        for v in task_info[key]:
            if str(v['TID']) not in output: output[str(v['TID'])] = key 

    return output

def get_tid_pid_mapping_from_task_info(task_info):
    output = {}
    for key in task_info:
        for v in task_info[key]:
            if str(v['TID']) not in output: output[str(v['TID'])] = str(v['PID'])

    return output

def analyze_pmap_data(data):
    output = {'time': 0.0, 'total':0, 'code':0, 'code_private': 0, 'static':0, 'static_private':0, 'heap':0, 'stack':0, 'anon': 0}

    for i, line in enumerate(data):
        if i == 0: output['time'] = float(line[:-1])
        elif i == 1: continue
        elif '====' in line: continue
        elif i == 2:
            item_list = parse_item(line)
            continue
        elif i == len(data)-1:
            line = line.split(' ')
            parsed_line = [item for item in line if item != '']
            output['total'] = output['total'] + int(parsed_line[0])
        else:
            pmap_line = parse_pmap_line(line, item_list)          
            if pmap_line['Mapping'] == '[heap]':
                output['heap'] = output['heap'] + int(pmap_line['Size'])
            elif pmap_line['Mapping'] == '[stack]':
                output['stack'] = output['stack'] + int(pmap_line['Size'])        
            elif pmap_line['Perm'] == 'r-x-':
                output['code'] = output['code'] + int(pmap_line['Size'])
            elif pmap_line['Perm'] == 'r-xp':
                output['code'] = output['code'] + int(pmap_line['Size'])
                output['code_private'] = output['code_private'] + int(pmap_line['Size'])
            else:                                 
                output['static'] = output['static'] + int(pmap_line['Size'])
                if 'p' in pmap_line['Perm']: output['static_private'] = output['static_private'] + int(pmap_line['Size'])

    return output

def analyze_pmap_from_pid(log_dir):
    output = {}

    # Get file list
    file_list = os.listdir(log_dir)
    file_list = [file for file in file_list if 'pid' in file and os.path.isfile(os.path.join(log_dir, file))]

    print('# Start analyzation of pmap from pid')
    for i in tqdm(range(len(file_list))):
        filename = file_list[i]
        pid = filename.split('-')[1].split('_')[0]
        iter = filename.split('-')[-1]
        if pid not in output: output[pid] = {}
        
        pmap_log_path = log_dir + '/' + filename
        with open(pmap_log_path, 'r') as f:
            pmap_data = f.readlines()       

        output[pid][iter] = analyze_pmap_data(pmap_data)

    return output

def analyze_pmap_from_tid(log_dir):
    output = {}

    # Get file list
    file_list = os.listdir(log_dir)
    file_list = [file for file in file_list if 'tid' in file and os.path.isfile(os.path.join(log_dir, file))]

    print('# Start analyzation pmap from tid')
    for i in tqdm(range(len(file_list))):
        filename = file_list[i]
        tid = filename.split('-')[1].split('_')[0]
        iter = filename.split('-')[-1]
        if tid not in output: output[tid] = {}
        
        pmap_log_path = log_dir + '/' + filename
        with open(pmap_log_path, 'r') as f:
            pmap_data = f.readlines()       

        output[tid][iter] = analyze_pmap_data(pmap_data)

    return output

if __name__ == '__main__':
    with open('configs/memory_mapping.yaml', 'r') as f:
        configs = yaml.safe_load(f)

    ## TODO: Setup input file paths
    label = configs['label']
    ps_info_path = 'data/'+label+'/ps_info.txt'
    log_dir = 'pmap_log/'+label

    if not os.path.exists(ps_info_path):
        os.system('mkdir data/'+label)        
        os.system('scp '+configs['ssh_address']+':'+configs['target_project_dir']+'/log/'+label+'/ps_info.txt '+ps_info_path)
    if not os.path.exists(log_dir):
        os.system('mkdir -p '+log_dir)
        os.system('scp '+configs['ssh_address']+':'+configs['target_project_dir']+'/pmap_log/'+label+'/* '+log_dir) 

    target_tasks = configs['target_tasks']

    ps_info = profile_ps_info(ps_info_path)

    task_info = {}
    for name in target_tasks:
        task_info[name] = get_task_info_by_name(name, ps_info)

    pid_name_mapping = get_pid_name_mapping_from_task_info(task_info)
    tid_name_mapping = get_tid_name_mapping_from_task_info(task_info)
    tid_pid_mapping = get_tid_pid_mapping_from_task_info(task_info)

    # 코드, 동적(stack, heap), 정적 메모리, 토탈 메모리 사용량 확인
        # [pid][iter] = {total, code, static, stack, heap}
        # [tid][iter] = {total, code, static, stack, heap}
    
    cache_dir_path = 'cache/'+log_dir
    result_from_pid_cache_path = cache_dir_path+'/result_from_pid.yaml'
    result_from_tid_cache_path = cache_dir_path+'/result_from_tid.yaml'

    if not os.path.exists(cache_dir_path):
        os.system('mkdir -p '+cache_dir_path)

    if os.path.exists(result_from_pid_cache_path):
        print('# Load cache of result_from_pid')
        with open(result_from_pid_cache_path, 'r') as f:
            result_from_pid = yaml.safe_load(f)    
    else:
        result_from_pid = analyze_pmap_from_pid(log_dir)        
        with open(result_from_pid_cache_path, 'w') as f: yaml.dump(result_from_pid, f)

    if os.path.exists(result_from_tid_cache_path):
        print('# Load cache of result_from_tid')
        with open(result_from_tid_cache_path, 'r') as f:
            result_from_tid = yaml.safe_load(f)    
    else:
        result_from_tid = analyze_pmap_from_tid(log_dir)        
        with open(result_from_tid_cache_path, 'w') as f: yaml.dump(result_from_tid, f)

    result = {}
    for pid in result_from_pid:
        name = pid_name_mapping[pid]
        if name not in result:
            result[name] = {
                'time': [],
                'anon': [],
                'code': [],
                'heap': [],
                'stack': [],
                'static': [],
                'total': []
            }

        for iter in result_from_pid[pid]:
            result[name]['time'].append(result_from_pid[pid][iter]['time'])
            result[name]['anon'].append(result_from_pid[pid][iter]['anon']/1024.0)
            result[name]['code'].append(result_from_pid[pid][iter]['code']/1024.0)
            # result[name]['code_private'].append(result_from_pid[pid][iter]['code_private']/1024.0)
            result[name]['heap'].append(result_from_pid[pid][iter]['heap']/1024.0)
            result[name]['stack'].append(result_from_pid[pid][iter]['stack']/1024.0)
            result[name]['static'].append(result_from_pid[pid][iter]['static']/1024.0)
            # result[name]['static_private'].append(result_from_pid[pid][iter]['static_private']/1024.0)
            result[name]['total'].append(result_from_pid[pid][iter]['total']/1024.0)

    for tid in result_from_tid:
        name = tid_name_mapping[tid]
        if name not in result:
            result[name] = {
                'time': [],
                'anon': [],
                'code': [],
                'heap': [],
                'stack': [],
                'static': [],
                'total': []
            }

        for iter in result_from_tid[tid]:
            result[name]['time'].append(result_from_pid[pid][iter]['time'])
            result[name]['anon'].append(result_from_tid[tid][iter]['anon']/1024.0)
            result[name]['code'].append(result_from_tid[tid][iter]['code']/1024.0)
            # result[name]['code_private'].append(result_from_tid[tid][iter]['code_private']/1024.0)
            result[name]['heap'].append(result_from_tid[tid][iter]['heap']/1024.0)
            result[name]['stack'].append(result_from_tid[tid][iter]['stack']/1024.0)
            result[name]['static'].append(result_from_tid[tid][iter]['static']/1024.0)
            # result[name]['static_private'].append(result_from_tid[tid][iter]['static_private']/1024.0)
            result[name]['total'].append(result_from_tid[tid][iter]['total']/1024.0)
    
    # Save result
    if not os.path.exists('result/'+label): os.system('mkdir -p result/'+label)
    result_path = 'result/'+label+'/memory_mapping.csv'
    with open(result_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['task', 'total', 'anon', 'code', 'heap', 'stack', 'static'])
        for name in result:
            writer.writerow([name, max(result[name]['total']), max(result[name]['anon']), max(result[name]['code']), max(result[name]['heap']), max(result[name]['stack']), max(result[name]['static'])])

    # Save plot
    print('# Plot memory usage')
    if not os.path.exists('plots/'+label): os.system('mkdir -p plots/'+label)
    for name in result:
        # result[name] = result[name].sorted(result[name], key=lambda x: x['time'])
        for key in result[name]:
            if key == 'time': continue
            plt.scatter(result[name]['time'], result[name][key], label=key, s=0.5, marker='x')
            plot_path = 'plots/'+label+'/'+name+'.png'
        plt.legend()
        plt.xlabel('Time (s)')
        plt.ylabel('Size (MB)')
        plt.ylim([0,3000])
        plt.savefig(plot_path)
        plt.close()
    

    # result structure
    """
    result  --- pid1    |--- avg_diff_sum -- anon
                        |               |--- code
                        |               |--- code_private
                        |               |--- heap
                        |               |--- stack
                        |               |--- static
                        |               |--- static_private
                        |               |--- total
                        |                                    
                        |--- max_diff_sum -- anon
                        |               |--- code
                        |               |--- code_private
                        |               |--- heap
                        |               |--- stack
                        |               |--- static
                        |               |--- static_private
                        |               |--- total
                        |            
                        |--- iter1 --------- anon
                        |               |--- code
                        |               |--- code_private
                        |               |--- heap
                        |               |--- stack
                        |               |--- static
                        |               |--- static_private 
                        |               |--- total
                        |               |--- diff_sum ----------- anon
                        |                                   |--- code
                        |                                   |--- code_private
                        |                                   |--- heap
                        |                                   |--- stack
                        |                                   |--- static
                        |                                   |--- static_private
                        |                                   |--- total                        
                        |--- iter2 --- ....
                        |
                        |

    """

    """
    result = {}
    for tid in result_from_tid:
        pid = tid_pid_mapping[tid]
        name = pid_name_mapping[pid]
        if name not in result: result[name] = {}
        if pid not in result[name]:
            result[name][pid] = result_from_pid[pid]
            result[name][pid]
                
        for iter in result_from_tid[tid]:
            if 'diff_sum' not in result[name][pid][iter]: result[name][pid][iter]['diff_sum'] = {'anon':0, 'code':0, 'code_private':0, 'heap':0, 'stack':0, 'static':0, 'static_private':0, 'total':0}
            result[name][pid][iter]['diff_sum']['anon'] = result[name][pid][iter]['diff_sum']['anon'] + result[name][pid][iter]['anon'] - result_from_tid[tid][iter]['anon']
            result[name][pid][iter]['diff_sum']['code'] = result[name][pid][iter]['diff_sum']['code'] + result[name][pid][iter]['code'] - result_from_tid[tid][iter]['code']
            result[name][pid][iter]['diff_sum']['code_private'] = result[name][pid][iter]['diff_sum']['code_private'] + result[name][pid][iter]['code_private'] - result_from_tid[tid][iter]['code_private']
            result[name][pid][iter]['diff_sum']['heap'] = result[name][pid][iter]['diff_sum']['heap'] + result[name][pid][iter]['heap'] - result_from_tid[tid][iter]['heap']
            result[name][pid][iter]['diff_sum']['stack'] = result[name][pid][iter]['diff_sum']['stack'] + result[name][pid][iter]['stack'] - result_from_tid[tid][iter]['stack']
            result[name][pid][iter]['diff_sum']['static'] = result[name][pid][iter]['diff_sum']['static'] + result[name][pid][iter]['static'] - result_from_tid[tid][iter]['static']
            result[name][pid][iter]['diff_sum']['static_private'] = result[name][pid][iter]['diff_sum']['static_private'] + result[name][pid][iter]['static_private'] - result_from_tid[tid][iter]['static_private']
            result[name][pid][iter]['diff_sum']['total'] = result[name][pid][iter]['diff_sum']['total'] + result[name][pid][iter]['total'] - result_from_tid[tid][iter]['total']
    
    for name in result:
        print('> name:', name)
        for pid in result[name]:            
            avg_diff_sum = {'anon':0, 'code':0, 'code_private':0, 'heap':0, 'stack':0, 'static':0, 'static_private':0, 'total':0}
            max_diff_sum = {'anon':0, 'code':0, 'code_private':0, 'heap':0, 'stack':0, 'static':0, 'static_private':0, 'total':0}
            cnt = 0
            for iter in result[name][pid]:
                avg_diff_sum['anon'] = avg_diff_sum['anon'] + result[name][pid][iter]['diff_sum']['anon']
                avg_diff_sum['code'] = avg_diff_sum['code'] + result[name][pid][iter]['diff_sum']['code']
                avg_diff_sum['code_private'] = avg_diff_sum['code_private'] + result[name][pid][iter]['diff_sum']['code_private']
                avg_diff_sum['heap'] = avg_diff_sum['heap'] + result[name][pid][iter]['diff_sum']['heap']
                avg_diff_sum['stack'] = avg_diff_sum['stack'] + result[name][pid][iter]['diff_sum']['stack']
                avg_diff_sum['static'] = avg_diff_sum['static'] + result[name][pid][iter]['diff_sum']['static']
                avg_diff_sum['static_private'] = avg_diff_sum['static_private'] + result[name][pid][iter]['diff_sum']['static_private']
                avg_diff_sum['total'] = avg_diff_sum['total'] + result[name][pid][iter]['diff_sum']['total']

                if max_diff_sum['total'] < result[name][pid][iter]['diff_sum']['total']:
                    max_diff_sum['anon'] = result[name][pid][iter]['diff_sum']['anon']
                    max_diff_sum['code'] = result[name][pid][iter]['diff_sum']['code']
                    max_diff_sum['code_private'] = result[name][pid][iter]['diff_sum']['code_private']
                    max_diff_sum['heap'] = result[name][pid][iter]['diff_sum']['heap']
                    max_diff_sum['stack'] = result[name][pid][iter]['diff_sum']['stack']
                    max_diff_sum['static'] = result[name][pid][iter]['diff_sum']['static']
                    max_diff_sum['static_private'] = result[name][pid][iter]['diff_sum']['static_private']
                    max_diff_sum['total'] = result[name][pid][iter]['diff_sum']['total']

                cnt = cnt + 1

            avg_diff_sum['anon'] = avg_diff_sum['anon'] / cnt
            avg_diff_sum['code'] = avg_diff_sum['code'] / cnt
            avg_diff_sum['code_private'] = avg_diff_sum['code_private'] / cnt
            avg_diff_sum['heap'] = avg_diff_sum['heap'] / cnt
            avg_diff_sum['stack'] = avg_diff_sum['stack'] / cnt
            avg_diff_sum['static'] = avg_diff_sum['static'] / cnt
            avg_diff_sum['static_private'] = avg_diff_sum['static_private'] / cnt
            avg_diff_sum['total'] = avg_diff_sum['total'] / cnt
            
            result[name][pid]['max_diff_sum'] = max_diff_sum
            result[name][pid]['avg_diff_sum'] = avg_diff_sum

            print('>>> pid:', pid)
            print('>>>>>> max_diff_sum:', result[name][pid]['max_diff_sum'])
            print('>>>>>> avg_diff_sum:', result[name][pid]['avg_diff_sum'])
    """


    # 시간에 따른 동적 메모리 사용량 변화가 어떠한가?
    
