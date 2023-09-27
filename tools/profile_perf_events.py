import os
import time
import yaml

if __name__ == '__main__':
    with open('configs/perf_events.yaml', 'r') as f:
        configs = yaml.safe_load(f)
    
    label = configs['label']
    duration = configs['duration']
    target_cores = configs['target_cores']
    target_events = configs['target_events']

    os.system('mkdir -p perf_events_log')
    if os.path.exists(f'perf_events_log/{label}.txt'):
        print('[ERROR] Same name of log already exists.')
        exit()

    target_events_str = ''
    for i, event in enumerate(target_events):
        target_events_str = target_events_str + event
        if i+1 != len(target_events): target_events_str = target_events_str + ','
    
    os.system(f'perf stat --timeout {duration} -C {target_cores} -e {target_events_str} -o perf_events_log/{label}.txt')

    