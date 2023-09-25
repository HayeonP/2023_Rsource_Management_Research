import os
import yaml

def is_matched(input, target):
    for v in input.split(' '):
        if v == target: return True
    return False

def get_counts(input):
    for v in input.split(' '):
        if v != '': return v
    return -1

def get_duration(input):
    return get_counts(input)

if __name__ == '__main__':
    with open('configs/perf_events.yaml', 'r') as f:
        configs = yaml.safe_load(f)

    label = configs['label']
    ssh_address = configs['ssh_address']
    target_project_dir = configs['target_project_dir']

    perf_events_log_path = f'perf_events_log/{label}.txt'

    if not os.path.exists(perf_events_log_path):
        os.system('mkdir perf_events_log')
        os.system(f'scp {ssh_address}:{target_project_dir}/perf_events_log/{label}.txt perf_events_log/{label}.txt')

    data = {}
    with open(perf_events_log_path, 'r') as f:
        input_data = f.read()
    input_data = input_data.split('\n')

    for i,line in enumerate(input_data):
        if 'Performance counter stats' in line: data['Target'] = line.split('\'')[1]
        elif is_matched(line,'instructions'): data['instructions'] = int(get_counts(line))        
        elif is_matched(line,'bus_access_rd'): data['bus_access_rd'] = int(get_counts(line))    
        elif is_matched(line,'bus_access_wr'): data['bus_access_wr'] = int(get_counts(line))
        elif is_matched(line,'bus_access'): data['bus_access'] = int(get_counts(line))      
        elif is_matched(line,'bus_cycles'): data['bus_cycles'] = int(get_counts(line))    
        elif is_matched(line,'l1d_cache'): data['l1d_cache'] = int(get_counts(line))    
        elif is_matched(line,'l1d_cache_refill'): data['l1d_cache_refill'] = int(get_counts(line))    
        elif is_matched(line,'l1d_cache_refill_rd'): data['l1d_cache_refill_rd'] = int(get_counts(line))    
        elif is_matched(line,'l1d_cache_refill_wr'): data['l1d_cache_refill_wr'] = int(get_counts(line))    
        elif is_matched(line,'l1d_cache_wb'): data['l1d_cache_wb'] = int(get_counts(line))    
        elif is_matched(line,'l1i_cache'): data['l1i_cache'] = int(get_counts(line))    
        elif is_matched(line,'l1i_cache_refill'): data['l1i_cache_refill'] = int(get_counts(line))    
        elif is_matched(line,'l2d_cache'): data['l2d_cache'] = int(get_counts(line))    
        elif is_matched(line,'l2d_cache_refill'): data['l2d_cache_refill'] = int(get_counts(line))    
        elif is_matched(line,'l2d_cache_refill_rd'): data['l2d_cache_refill_rd'] = int(get_counts(line))    
        elif is_matched(line,'l2d_cache_refill_wr'): data['l2d_cache_refill_wr'] = int(get_counts(line))    
        elif is_matched(line,'l2d_cache_wb'): data['l2d_cache_wb'] = int(get_counts(line))    
        elif is_matched(line,'l3d_cache'): data['l3d_cache'] = int(get_counts(line))    
        elif is_matched(line,'l3d_cache_rd'): data['l3d_cache_rd'] = int(get_counts(line))    
        elif is_matched(line,'l3d_cache_refill'): data['l3d_cache_refill'] = int(get_counts(line))    
        elif is_matched(line,'armv8_pmuv3/l3d_cache_wb/'): data['armv8_pmuv3/l3d_cache_wb/'] = int(get_counts(line))
        elif is_matched(line, 'elapsed'): data['duration'] = float(get_duration(line))

    result = {}

    
    try:
        result['l1d_hit_ratio'] = (data['l1d_cache'] - data['l1d_cache_refill']) / data['l1d_cache']
    except: pass
    try:
        result['l1i_hit_ratio'] = (data['l1i_cache'] - data['l1i_cache_refill']) / data['l1i_cache']
    except: pass
    try:
        result['l2d_hit_ratio'] = (data['l2d_cache'] - data['l2d_cache_refill']) / data['l2d_cache']
    except: pass
    try:
        result['l3d_hit_ratio'] = (data['l3d_cache'] - data['l3d_cache_refill']) / data['l3d_cache']        
    except: pass
    try:
        result['l1d_miss_ratio'] = 1.0 - result['l1d_hit_ratio']
    except: pass
    try:
        result['l1i_miss_ratio'] = 1.0 - result['l1i_hit_ratio']
    except: pass
    try:
        result['l2d_miss_ratio'] = 1.0 - result['l2d_hit_ratio']
    except: pass
    try:
        result['l3d_miss_ratio'] = 1.0 - result['l3d_hit_ratio']
    except: pass
    try:
        result['l1d_miss_per_sec(10^6)'] = data['l1d_cache_refill'] / data['duration']/1000000.0
    except: pass
    try:
        result['l1i_miss_per_sec(10^6)'] = data['l1i_cache_refill'] / data['duration']/1000000.0
    except: pass
    try:
        result['l2d_miss_per_sec(10^6)'] = data['l2d_cache_refill'] / data['duration']/1000000.0
    except: pass
    try:
        result['l3d_miss_per_sec(10^6)'] = data['l3d_cache_refill'] / data['duration']/1000000.0
    except: pass
    try:
        result['l1d_access_per_sec(10^6)'] = data['l1d_cache'] / data['duration']/1000000.0
    except: pass
    try:
        result['l1i_access_per_sec(10^6)'] = data['l1i_cache'] / data['duration']/1000000.0
    except: pass
    try:
        result['l2d_access_per_sec(10^6)'] = data['l2d_cache'] / data['duration']/1000000.0
    except: pass
    try:
        result['l3d_access_per_sec(10^6)'] = data['l3d_cache'] / data['duration']/1000000.0
    except: pass
    try:
        result['bus_access_per_sec(10^6)'] = data['bus_access'] / data['duration']/1000000.0
    except: pass
    try:
        result['-->l3d/l1d acess ratio'] = result['l3d_access_per_sec(10^6)']/result['l1d_access_per_sec(10^6)']
    except: pass
    

    for key in result:
        print(key, format(result[key], '.2f'))