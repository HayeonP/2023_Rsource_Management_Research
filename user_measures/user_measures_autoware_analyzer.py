import csv
import yaml
import json
import matplotlib.pyplot as plt

import os
import time
import scripts.autoware_analyzer_lib as aa
import numpy as np
import copy
from tqdm import tqdm


configs = {}

def profile_response_time(dir_path, output_title, first_node, last_node, start_instance, end_instance, is_collapsed, is_matching_failed, filter=1.0):
    _profile_response_time(dir_path, output_title, first_node, last_node, start_instance, end_instance, is_collapsed, is_matching_failed, 'shortest', filter)
    # _profile_response_time(dir_path, output_title, first_node, last_node, start_instance, end_instance, is_collapsed, is_matching_failed, 'longest', filter)
    return

def _profile_response_time(dir_path, output_title, first_node, last_node, start_instance, end_instance, is_collapsed, is_matching_failed, type, filter=1.0):
    if type == 'shortest': label = 'Shortest'
    elif type == 'longest': label = 'Longest'
    else: 
        print('[ERROR] Invalidate type:', type)
        exit()

    first_node_path = dir_path + '/' + first_node + '.csv'
    last_node_path = dir_path + '/' + last_node + '.csv'

    E2E_response_time, max_E2E_response_time, avg_E2E_response_time \
                = aa.get_E2E_response_time(first_node_path, last_node_path, start_instance, end_instance, online_profiling, type=type)

    exp_title = dir_path.split('/')[-3]
    exp_id = dir_path.split('/')[-2]

    output_dir_path = f"analyzation/{output_title}/E2E"
    if not os.path.exists(output_dir_path): os.system('mkdir -p ' + output_dir_path)

    # Plot graph
    x_data = list(E2E_response_time.keys()) # Instance IDs
    y_data = list(E2E_response_time.values()) # E2E response time(ms)
    if not is_collapsed:
        x_data = x_data[:int(len(x_data) * filter)]
        y_data = y_data[:int(len(y_data) * filter)]

    plot_path = f"{output_dir_path}/E2E_plot_v{exp_id}.png"

    plt.plot(x_data, y_data)
    plt.axhline(y = max_E2E_response_time, color = 'r', linestyle = ':', label='Max')
    plt.axhline(y = avg_E2E_response_time, color = 'b', linestyle = ':', label='Avg')    
    plt.legend()
    plt.ylim(0, 1000)
    plt.xlabel('Instance ID')
    plt.ylabel(label + ' E2E Response Time (ms)')
    plt.yticks(np.arange(0,1000,100))
    plt.title('E2E during avoidance\nis_collapsed='+str(is_collapsed) + '/ is_matching_failed='+str(is_matching_failed))
    plt.savefig(plot_path)
    plt.close()

    e2e_path = f"{output_dir_path}/E2E_list_v{exp_id}.yaml"
    with open(e2e_path, "w") as f:
        e2e_data = {"instance_id": x_data, "e2e_response_time": y_data}
        json.dump(e2e_data, f, indent=4)
        

    return

def profile_response_time_for_experiment(source_path, output_title, first_node, last_node, is_collapsed_list, is_matching_failed_list, x_range=[0.0, 0.0], filter=1.0, deadline=450.0):    
    exp_title = dir_path.split('/')[-3]
    
    _profile_response_time_for_experiment(source_path, output_title, first_node, last_node, exp_title, is_collapsed_list, is_matching_failed_list, deadline, type='shortest', mode='total', x_range=x_range, filter=filter)
    _profile_response_time_for_experiment(source_path, output_title, first_node, last_node, exp_title, is_collapsed_list, is_matching_failed_list, deadline, type='shortest', mode='normal', x_range=x_range, filter=filter)
    _profile_response_time_for_experiment(source_path, output_title, first_node, last_node, exp_title, is_collapsed_list, is_matching_failed_list, deadline, type='shortest', mode='collision', x_range=x_range, filter=filter)
    _profile_response_time_for_experiment(source_path, output_title, first_node, last_node, exp_title, is_collapsed_list, is_matching_failed_list, deadline, type='shortest', mode='matching_failed', x_range=x_range, filter=filter)

    return

def _profile_response_time_for_experiment(source_path, output_title, first_node, last_node, exp_title, is_collapsed_list, is_matching_failed_list, deadline, type, mode, x_range=[0.0, 0.0], filter=1.0):
    if type == 'shortest':
        label = 'Shortest'
    elif type == 'longest':
        label = 'Longest'
    else:
        print('[ERROR] Invalid mode:', label)
    
    available_mode = ['total', 'normal', 'collision', 'matching_failed']
    if mode not in available_mode:
        print('[ERROR] Invalidate mode:', mode)
        exit()

    n = len(is_collapsed_list)
    collision_cnt = sum(is_collapsed_list)
    sum_of_deadilne_miss_ratio = 0

    target_experiment_idx_list = []
    if mode == 'total': target_experiment_idx_list = range(n)
    elif mode == 'collision': target_experiment_idx_list = aa.get_idices_of_one_from_list(is_collapsed_list)
    elif mode == 'matching_failed': target_experiment_idx_list = aa.get_idices_of_one_from_list(is_matching_failed_list)        
    elif mode == 'normal':
        target_experiment_idx_list = list(range(n))
        merged_indices = aa.merge_binary_list_to_idx_list(is_collapsed_list, is_matching_failed_list)        
        for remove_target in merged_indices:
            target_experiment_idx_list.remove(remove_target)
    
    all_E2E_response_time_list = []
    max_E2E_response_time_list = []
    leakage_ratio_list = []
    x_data = []
    for idx in target_experiment_idx_list:
        is_collapsed = is_collapsed_list[idx]        
        response_time_path = source_path + '/' + str(idx) + '/response_time'
        center_offset_path = source_path + '/' + str(idx) + '/center_offset.csv'
        first_node_path = response_time_path + '/' + first_node + '.csv'
        last_node_path = response_time_path + '/' + last_node + '.csv'
        start_instance, end_instance = aa.get_instance_pair(center_offset_path, x_range[0], x_range[1], configs['simulator'])
        if start_instance < 0: continue

        E2E_response_time, _, _ \
            = aa.get_E2E_response_time(first_node_path, last_node_path, start_instance, end_instance, online_profiling, type)        

        # Profile instance leakge ratio
        instance_list = list(E2E_response_time.keys())
        leakage_cnt = 0
        for i, instance in enumerate(instance_list):
            if i == 0: continue
            if instance_list[i] - instance_list[i-1] != 1: leakage_cnt = leakage_cnt + 1     
        leakage_ratio = float(leakage_cnt) / float(instance_list[-1] - instance_list[0])
        leakage_ratio_list.append(leakage_ratio)

        x_data = list(E2E_response_time.keys()) # Instance IDs
        y_data = list(E2E_response_time.values()) # E2E response time(ms)
        if not is_collapsed:
            x_data = x_data[:int(len(x_data) * filter)]
            y_data = y_data[:int(len(y_data) * filter)]
        if(len(y_data) > 0):
            all_E2E_response_time_list.extend(y_data)
            max_E2E_response_time_list.append(max(y_data))        

        # Validate miss deadline during avoidance
        deadline_miss_cnt = 0
        for instance in x_data:
            if not instance in E2E_response_time.keys(): continue
            if E2E_response_time[instance] >= deadline:
                deadline_miss_cnt = deadline_miss_cnt + 1
        
        if len(x_data) == 0:
            sum_of_deadilne_miss_ratio    
        else:
            sum_of_deadilne_miss_ratio = sum_of_deadilne_miss_ratio + float(deadline_miss_cnt)/float(len(x_data))

        color = 'b'
        if is_collapsed_list[idx] == 1: color = 'r' 

        plt.plot(x_data, y_data, color, linewidth=1.0)

    # Statistics
    if len(all_E2E_response_time_list) == 0:
        max_E2E_response_time = 0    
        avg_E2E_response_time = 0
        var_E2E_response_time = 0
        avg_max_E2E_response_time = 0
        percentile_99 = 0
    else:
        max_E2E_response_time = max(all_E2E_response_time_list)    
        avg_E2E_response_time = sum(all_E2E_response_time_list) / len(all_E2E_response_time_list)
        percentile_99 = float(round(np.percentile(all_E2E_response_time_list, 99),2))
        var_E2E_response_time = float(np.var(all_E2E_response_time_list))
        avg_max_E2E_response_time = sum(max_E2E_response_time_list) / len(max_E2E_response_time_list)
    
    if mode == "total":
        E2E_response_time_info_path = f"analyzation/{output_title}/{mode}_E2E_info.yaml"
    else:
        E2E_response_time_info_fname = f"{mode}_E2E_info.yaml"
        E2E_response_time_info_fpath = f"analyzation/{output_title}/summary/"
        if not os.path.exists(E2E_response_time_info_fpath):
            os.system(f"mkdir {E2E_response_time_info_fpath}")
        E2E_response_time_info_path = f"{E2E_response_time_info_fpath}{E2E_response_time_info_fname}"
        
    E2E_response_time_info = {}
    E2E_response_time_info['deadline_ms'] = deadline
    E2E_response_time_info['max'] = max_E2E_response_time
    E2E_response_time_info['avg'] = avg_E2E_response_time
    E2E_response_time_info['percentile_99'] = percentile_99
    E2E_response_time_info['var'] = var_E2E_response_time
    E2E_response_time_info['avg_max'] = avg_max_E2E_response_time    
    
    if collision_cnt != 0 and len(target_experiment_idx_list) != 0:
        E2E_response_time_info['avg_miss_ratio'] =  float(sum_of_deadilne_miss_ratio) / float(len(target_experiment_idx_list))
    else:
        E2E_response_time_info['avg_miss_ratio'] = 0.0    

    if len(leakage_ratio_list) == 0:
        E2E_response_time_info['avg_leakage_ratio'] = 0.0
    else:
        E2E_response_time_info['avg_leakage_ratio'] = float(sum(leakage_ratio_list)) / float(len(target_experiment_idx_list))

    with open(E2E_response_time_info_path, 'w') as f: yaml.dump(E2E_response_time_info, f, default_flow_style=False)

    if len(is_collapsed_list) == 0: collision_ratio = 0
    else: collision_ratio = sum(is_collapsed_list)/len(is_collapsed_list)

    if len(is_matching_failed_list) == 0: matching_failure_ratio = 0
    else: matching_failure_ratio = sum(is_matching_failed_list)/len(is_matching_failed_list)

    # Plot
    if mode == "total":
        plot_path = f"analyzation/{output_title}/{mode}_E2E_plot.png"
    else:
        plot_fname = f"{mode}_E2E_plot.png"
        plot_fpath = f"analyzation/{output_title}/summary/"
        if not os.path.exists(plot_fpath): os.system(f"mkdir {plot_fpath}")
        plot_path = f"{plot_fpath}{plot_fname}"

    plt.legend()    
    plt.xlabel('Instance ID')
    plt.ylabel(label + ' E2E Response Time (ms)')
    plt.ylim(0, 1000)
    plt.yticks(np.arange(0,1000,100))
    if len(x_data) != 0:
        plt.text(min(x_data)+2, 950, 'max: ' + str(max_E2E_response_time))
        plt.text(min(x_data)+2, 900, 'avg: ' + str(avg_E2E_response_time))
        plt.text(min(x_data)+2, 850, 'var: ' + str(var_E2E_response_time))
        plt.text(min(x_data)+2, 800, 'avg_miss_ratio: ' + str(E2E_response_time_info['avg_miss_ratio']))
    plt.title('Iteration: ' + str(n) \
            + ' / Collision ratio: ' + str(collision_ratio) \
            + ' / Matching failure ratio: '+ str(matching_failure_ratio))
    plt.savefig(plot_path)
    plt.close()
    
    # Distribution
    if mode == "total":
        distribution_path = f"analyzation/{output_title}/{mode}_E2E_distribution.png"
    else:
        distribution_fname = f"{mode}_E2E_distribution.png"
        distribution_fpath = f"analyzation/{output_title}/summary/"
        if not os.path.exists: os.system(f"mkdir {distribution_fpath}")
        distribution_path = f"{distribution_fpath}{distribution_fname}"
    
    plt.hist(all_E2E_response_time_list, bins=50, density = True, color='c')
    plt.axvline(avg_E2E_response_time, color="r", linestyle="--", label=f"Avg E2E: {round(avg_E2E_response_time,2)}ms")
    
    if len(all_E2E_response_time_list) > 0:
        percentile_99 = round(np.percentile(all_E2E_response_time_list, 99),2)
        plt.axvline(percentile_99, color="b", linestyle="--", label=f"99 percentile: {round(percentile_99,2)}ms")

        percentile_99_9 = round(np.percentile(all_E2E_response_time_list, 99.9), 2)
        plt.axvline(percentile_99_9, color="g", linestyle="--", label=f"99.9 percentile: {round(percentile_99_9,2)}ms")
    
    if len(max_E2E_response_time_list) > 0:
        plt.axvline(max(max_E2E_response_time_list), color="k", linestyle="--", label=f"Max E2E: {round(max(max_E2E_response_time_list),2)}ms")
    
    plt.ylim(0, 0.015)
    plt.xlabel("E2E")
    plt.ylabel("Density")
    plt.legend(loc="lower center", bbox_to_anchor=(0.5,1.02), ncol=2)    
    plt.tight_layout()
    
    plt.savefig(distribution_path)
    plt.close()
    

    return

def profile_center_offset(dir_path, output_title, center_offset, max_center_offset, avg_center_offset, is_collapsed):
    exp_title = dir_path.split('/')[-3]
    exp_id = dir_path.split('/')[-2]
    output_dir_path = 'analyzation/' + output_title + '/center_offset'
    if not os.path.exists(output_dir_path): os.system('mkdir -p ' + output_dir_path)

    # Plot graph
    center_offset = {x:center_offset[x] for x in center_offset if x < 1000}
    x_data = list(center_offset.keys()) # Instance IDs
    y_data = list(center_offset.values()) # Center offset(m)

    plot_path = f"{output_dir_path}/center_offset_v{exp_id}.png"
    center_offset_info_path = f"{output_dir_path}/center_offset_info_v{exp_id}.yaml"
    center_offset_dict = {}
    center_offset_dict['center_offset'] = y_data
    with open(f'{center_offset_info_path}', 'w') as f:
        yaml.dump(center_offset_dict, f, default_flow_style=False)

    plt.plot(x_data, y_data)
    plt.axhline(y = max_center_offset, color = 'r', linestyle = ':', label='Max')
    plt.axhline(y = avg_center_offset, color = 'b', linestyle = ':', label='Avg')    
    plt.legend()    
    plt.xlabel('Instance ID')
    plt.ylabel('Center offset(m)')
    plt.title('is_collapsed='+str(is_collapsed))
    plt.savefig(plot_path)
    plt.close()

def profile_avg_center_offset_for_experiment(source_path, is_matching_failed_list):
    target_experiment_idx_list = aa.get_idices_of_one_from_list(is_matching_failed_list)

    all_center_offset = []
    for idx in range(len(target_experiment_idx_list)):
        center_offset_path = source_path + '/' + str(idx) + '/center_offset.csv'
        center_offset, _, _ = aa.get_center_offset(center_offset_path)
        all_center_offset.extend(center_offset)
    avg = 0
    if len(all_center_offset) != 0:
        avg = float(sum(all_center_offset)) / float(len(all_center_offset))
    
    return avg

def profile_waypoints(dir_path, output_title, is_collapsed, is_matching_failed):
    exp_title = dir_path.split('/')[-3]
    exp_id = dir_path.split('/')[-2]
    output_dir_path = 'analyzation/' + output_title + '/trajectories'
    if not os.path.exists(output_dir_path): os.system('mkdir -p ' + output_dir_path)

    # Centerline
    center_line_path = dir_path + '/center_line.csv'
    center_line = aa.get_center_line(center_line_path)
    center_line_x = []
    center_line_y = []
    
    for center_line_point in center_line:
        center_line_x.append(float(center_line_point[0]))
        center_line_y.append(float(center_line_point[1]))  

    plt.plot(center_line_x, center_line_y, 'k', label='Center line')

    # Waypoints
    exp_title = dir_path.split('/')[-2]
    exp_id = dir_path.split('/')[-1]

    center_offset_path = dir_path + '/center_offset.csv'
    waypoints = aa.get_waypoints(center_offset_path, configs['simulator'])
    time_stamp = []
    waypoints_x = []
    waypoints_y = []
    
    for waypoint in waypoints:
        waypoints_x.append(float(waypoint[0]))
        waypoints_y.append(float(waypoint[1]))
        time_stamp.append(float(waypoint[2]))

    color = 'b'
    if is_collapsed: color = 'r'
    
    plt.plot(waypoints_x, waypoints_y, color, linewidth=1.0)

    if configs['simulator'] == 'old':
        # Objects
        npc1_x = [6, 6, -1, -1, 6]
        npc1_y = [51, 48, 48, 51, 51]
        npc2_x = [6, 6, -1, -1, 6]
        npc2_y = [55, 52, 52, 55, 55]
        plt.plot(npc1_x, npc1_y, 'k')
        plt.plot(npc2_x, npc2_y, 'k')
    elif configs['simulator'] == 'carla' or configs['simulator'] == 'svl':
        pass

    # Plot
    plot_path = f"{output_dir_path}/waypoints_v{exp_id}.png"    
            
    plt.xlabel('x (m)')
    plt.ylabel('y (m)')
    plt.title('is_collapsed='+str(is_collapsed) + '/ is_matching_failed='+str(is_matching_failed))
    plt.legend()
    plt.savefig(plot_path)

    plt.close()
    
    # info
    info_path = f"{output_dir_path}/waypoints_info_v{exp_id}.yaml"
    info_dict = {}
    info_dict["waypoints"] = [{"time_stamp": time_stamp[i], "x": waypoints_x[i], "y": waypoints_y[i]} for i in range(len(time_stamp))]
    with open(f"{info_path}", "w") as f:
        yaml.dump(info_dict, f, default_flow_style=False)
    
    return

def profile_waypoints_for_experiment(source_path, output_title, is_collapsed_list, is_matching_failed_list):
    _profile_waypoints_for_experiment(source_path, output_title, is_collapsed_list, is_matching_failed_list, mode='total')
    _profile_waypoints_for_experiment(source_path, output_title, is_collapsed_list, is_matching_failed_list, mode='normal')
    _profile_waypoints_for_experiment(source_path, output_title, is_collapsed_list, is_matching_failed_list, mode='collision')
    _profile_waypoints_for_experiment(source_path, output_title, is_collapsed_list, is_matching_failed_list, mode='matching_failed')

def _profile_waypoints_for_experiment(source_path, output_title, is_collapsed_list, is_matching_failed_list, mode='total'):
    available_mode = ['total', 'normal', 'collision', 'matching_failed']
    if mode not in available_mode:
        print('[ERROR] Invalidate mode:', mode)
        exit()
    
    n = len(is_collapsed_list)

    # Centerline
    center_line_path = source_path + '/0/center_line.csv'
    center_line = aa.get_center_line(center_line_path)
    center_line_x = []
    center_line_y = []
    
    for center_line_point in center_line:
        center_line_x.append(float(center_line_point[0]))
        center_line_y.append(float(center_line_point[1]))  

    plt.plot(center_line_x, center_line_y, 'k', label='Center line')
    
    target_experiment_idx_list = []
    if mode == 'total': target_experiment_idx_list = range(n)
    elif mode == 'collision':
        target_experiment_idx_list = aa.get_idices_of_one_from_list(is_collapsed_list)
    elif mode == 'matching_failed': target_experiment_idx_list = aa.get_idices_of_one_from_list(is_matching_failed_list)
    else:
        target_experiment_idx_list = list(range(n))        
        merged_indices = aa.merge_binary_list_to_idx_list(is_collapsed_list, is_matching_failed_list)
        for remove_target in merged_indices:
            target_experiment_idx_list.remove(remove_target)

    exp_title = dir_path.split('/')[-3]

    # Waypoints
    for idx in target_experiment_idx_list:        
        exp_id = str(idx)
        label = exp_title + '_' + exp_id

        center_offset_path = source_path + '/' + str(idx) + '/center_offset.csv'
        waypoints = aa.get_waypoints(center_offset_path, configs['simulator'])
        waypoints_x = []
        waypoints_y = []
        
        for waypoint in waypoints:
            waypoints_x.append(float(waypoint[0]))
            waypoints_y.append(float(waypoint[1]))

        color = 'b'
        if is_collapsed_list[idx] == 1: color = 'r' 

        plt.plot(waypoints_x, waypoints_y, color, linewidth=1.0)


    if configs['simulator'] == 'old':
        # Objects
        npc1_x = [6, 6, -1, -1, 6]
        npc1_y = [51, 48, 48, 51, 51]
        npc2_x = [6, 6, -1, -1, 6]
        npc2_y = [55, 52, 52, 55, 55]
        plt.plot(npc1_x, npc1_y, 'k')
        plt.plot(npc2_x, npc2_y, 'k')
    elif configs['simulator'] == 'carla' or configs['simulator'] == 'svl':
        pass

    if len(is_collapsed_list) == 0: collision_ratio = 0
    else: collision_ratio = sum(is_collapsed_list)/len(is_collapsed_list)

    if len(is_matching_failed_list) == 0: matching_failure_ratio = 0
    else: matching_failure_ratio = sum(is_matching_failed_list)/len(is_matching_failed_list)

    # Plot
    if mode == "total":
        plot_path = f"analyzation/{output_title}/{mode}_waypoints.png"
    else:
        plot_fname = f"{mode}_waypoints.png"
        plot_fpath = f"analyzation/{output_title}/summary/"
        
        if not os.path.exists(plot_fpath):
            os.system(f"mkdir {plot_fpath}")
        plot_path = f"{plot_fpath}{plot_fname}"
    
    if configs['simulator'] == 'old':
        plt.xlim(-70, 40)
        plt.ylim(20,75)
    elif configs['simulator'] == 'carla' or configs['simulator'] == 'svl':
        pass
    plt.xlabel('x (m)')
    plt.ylabel('y (m)')
    plt.title('Iteration: ' + str(n) \
            + ' / Collision ratio: ' + str(collision_ratio) \
            + ' / Matching failure ratio: '+ str(matching_failure_ratio))
    plt.savefig(plot_path)

    plt.close()

def profile_analyzation_info(source_path, output_title, avg_center_offset, is_collapsed_list, is_matching_failed_list, max_miss_alignment_delay_list, avg_miss_alignment_delay_list, perf_info = {}):    
    analyzation_info = {}
    collision_index_list = aa.get_idices_of_one_from_list(is_collapsed_list)
    matching_failure_index_list = aa.get_idices_of_one_from_list(is_matching_failed_list)
    
    if len(is_collapsed_list) == 0: collision_ratio = 0
    else: collision_ratio = sum(is_collapsed_list)/len(is_collapsed_list)

    if len(is_matching_failed_list) == 0: matching_failure_ratio = 0
    else: matching_failure_ratio = sum(is_matching_failed_list)/len(is_matching_failed_list)

    analyzation_info['result'] = {}
    analyzation_info['resource_usage'] = {}

    analyzation_info['result']['avg_center_offset'] = avg_center_offset
    analyzation_info['result']['collision_index'] = collision_index_list
    analyzation_info['result']['collision_ratio'] = collision_ratio
    analyzation_info['result']['matching_failure_index'] = matching_failure_index_list
    analyzation_info['result']['matching_failure_ratio'] = matching_failure_ratio
    analyzation_info['result']['max_miss_alignment_delay'] = max(max_miss_alignment_delay_list)
    analyzation_info['result']['avg_miss_alignment_delay'] = sum(avg_miss_alignment_delay_list)/len(avg_miss_alignment_delay_list)

    for key in list(perf_info.keys()):
        analyzation_info['resource_usage'][key] = perf_info[key]

    analyzation_info_path = f"analyzation/analyzation_info.yaml"
    with open(analyzation_info_path, 'w') as f: yaml.dump(analyzation_info, f, default_flow_style=False)

    return

def profile_miss_alignment_delay(dir_path, output_title, chain_info, start_instance, end_instance, is_collapsed, filter=1.0):
    exp_title = dir_path.split('/')[-3]
    exp_id = dir_path.split('/')[-2]

    first_node_path = dir_path + '/' + chain_info[0] + '.csv'
    last_node_path = dir_path + '/' + chain_info[-1] + '.csv'
    
    E2E_response_time, _, _ = aa.get_E2E_response_time(first_node_path, last_node_path, start_instance, end_instance, online_profiling, type='shortest')

    node_response_time_list = []
    for node in chain_info:        
        if node == "voxel_grid_filter" and not os.path.exists(dir_path + '/' + node + '.csv'):
            node = "voexl_grid_filter"

        node_path = dir_path + '/' + node + '.csv'
        node_response_time, _, _ = aa.get_E2E_response_time(node_path, node_path, start_instance, end_instance, online_profiling, type='shortest')
        node_response_time_list.append(node_response_time)
    miss_alignment_delay = copy.deepcopy(E2E_response_time)

    for node_response_time in node_response_time_list:
        miss_alignment_delay = aa.subsctract_dicts(miss_alignment_delay, node_response_time)    
    
    # Plot graph
    output_dir_path = 'analyzation/' + output_title + '/' + 'miss_alignment_delay'
    if not os.path.exists(output_dir_path): os.system('mkdir -p ' + output_dir_path)

    x_miss_alignment_delay_data = list(miss_alignment_delay.keys()) # Instance IDs
    y_miss_alignment_delay_data = list(miss_alignment_delay.values()) # E2E response time(ms)

    if not is_collapsed:
        x_miss_alignment_delay_data = x_miss_alignment_delay_data[:int(len(x_miss_alignment_delay_data) * filter)]
        y_miss_alignment_delay_data = y_miss_alignment_delay_data[:int(len(y_miss_alignment_delay_data) * filter)]
    plt.plot(x_miss_alignment_delay_data, y_miss_alignment_delay_data, color = 'g', label = 'Miss alignment delay')
    max_miss_alignment_delay = max(y_miss_alignment_delay_data)
    avg_miss_alignment_delay = sum(y_miss_alignment_delay_data)/len(y_miss_alignment_delay_data)

    x_E2E_data = list(E2E_response_time.keys()) # Instance IDs
    y_E2E_data = list(E2E_response_time.values()) # E2E response time(ms)
    color = 'r'
    if not is_collapsed:
        x_E2E_data = x_E2E_data[:int(len(x_E2E_data) * filter)]
        y_E2E_data = y_E2E_data[:int(len(y_E2E_data) * filter)]
        color = 'b'
    
    plt.plot(x_E2E_data, y_E2E_data, color = color, label = 'E2E')

    plot_path = f"{output_dir_path}/miss_alignment_delay_v{exp_id}_plot.png"
           
    plt.legend()
    plt.ylim(0, 1000)
    plt.xlabel('Instance ID')
    plt.ylabel('Time (ms)')
    plt.yticks(np.arange(0,1000,100))
    plt.title('is_collapsed='+str(is_collapsed) + '/ is_matching_failed='+str(is_matching_failed))
    plt.savefig(plot_path)
    plt.close()

    return max_miss_alignment_delay, avg_miss_alignment_delay

def profile_perf_info_for_experiment(source_path):
    n = 0
    for path in os.listdir(source_path):
        if not os.path.isfile(os.path.join(source_path, path)): n = n + 1

    avg_memory_bandwidth_list = [] # GB/s
    l3d_cache_refill_event_cnt_of_ADAS_cores_list = []
    l3d_cache_refill_event_cnt_of_all_cores_list = []
    n = n - 1
    for idx in range(n):
        experiment_info_path = f"{source_path}/{str(idx)}/experiment_info.yaml"
        with open(experiment_info_path) as f:
            experiment_info = yaml.load(f, Loader=yaml.FullLoader)
            if 'l3d_cache_refill_event_cnt_of_ADAS_cores(per sec)' not in experiment_info \
                or 'avg_total_memory_bandwidth_usage(GB/s)' not in experiment_info \
                or 'l3d_cache_refill_event_cnt_of_all_cores(per sec)' not in experiment_info:
                return {}
            l3d_cache_refill_event_cnt_of_ADAS_cores_list.append(float(experiment_info['l3d_cache_refill_event_cnt_of_ADAS_cores(per sec)']))
            l3d_cache_refill_event_cnt_of_all_cores_list.append(float(experiment_info['l3d_cache_refill_event_cnt_of_all_cores(per sec)']))
            avg_memory_bandwidth_list.append(float(experiment_info['avg_total_memory_bandwidth_usage(GB/s)']))
    
    avg_l3d_cache_refill_event_cnt_of_ADAS_cores = sum(l3d_cache_refill_event_cnt_of_ADAS_cores_list)/len(l3d_cache_refill_event_cnt_of_ADAS_cores_list)
    avg_l3d_cache_refill_event_cnt_of_all_cores = sum(l3d_cache_refill_event_cnt_of_all_cores_list)/len(l3d_cache_refill_event_cnt_of_all_cores_list)
    avg_memory_bandwidth = sum(avg_memory_bandwidth_list)/len(avg_memory_bandwidth_list)
    
    perf_info = {}
    perf_info['avg_l3d_cache_refill_event_cnt_of_ADAS_cores(per sec)'] = avg_l3d_cache_refill_event_cnt_of_ADAS_cores
    perf_info['avg_l3d_cache_refill_event_cnt_of_all_cores(per sec)'] = avg_l3d_cache_refill_event_cnt_of_all_cores
    perf_info['avg_total_memory_bandwidth_usage'] = avg_memory_bandwidth

    return perf_info

def get_current_experiment_output():
    cur_dir_output_path = 'results/cur_adas/0'
    os.system(f'mkdir -p {cur_dir_output_path}')
    os.system(f'mkdir -p {cur_dir_output_path}/../configs')
    os.system(f'scp -r root@192.168.0.11:/var/lib/lxc/linux1/rootfs/home/root/Documents/profiling/response_time {cur_dir_output_path}')
    os.system(f'cp ./center_line.csv {cur_dir_output_path}')
    os.system(f'cp ./center_offset.csv {cur_dir_output_path}')
    empty_experiment_info = {}
    empty_experiment_info['avg_total_memory_bandwidth_usage(GB/s)'] = 1.0
    empty_experiment_info['collapsed_position'] = []
    empty_experiment_info['is_collaped'] = False
    empty_experiment_info['l3d_cache_refill_event_cnt_of_ADAS_cores(per sec)'] = 1.1
    empty_experiment_info['l3d_cache_refill_event_cnt_of_all_cores(per sec)'] = 1.1
    with open(f'{cur_dir_output_path}/experiment_info.yaml', 'w') as f: yaml.dump(empty_experiment_info, f, default_flow_style=False)
    # if configs["experiment_title"][0] != 'cur_adas':
    #     os.system(f'cp -r results/cur_adas results/{configs["experiment_title"][0]}')

def get_recent_data():
    center_offset_path = 'results/cur_adas/0/center_offset.csv'
    aa.center_offset_to_recent_data(center_offset_path, online_profiling_duration)

def get_user_measures(output_title):
    if "handling" in output_title:
        scenario = "handling"
    elif "braking" in output_title:
        scenario = "braking"
    elif "lane_change" in output_title:
        scenario = "lane_change"
    else:
        print(f"[ERROR] Cannot detect scenario from experiment path: {output_title}")
        exit()
    
    def get_handling_user_measure(output_title):
        center_offset_fpath = f"analyzation/{output_title}/center_offset/"
        fnames = os.listdir(center_offset_fpath)
        max_center_offset = 0.0
        avg_center_offset = 0.0
        n = 0.0
        
        for fname in fnames:
            if ".yaml" not in fname: continue
            with open(f"{center_offset_fpath}{fname}", "r") as f:
                data = yaml.safe_load(f)
                if len(data["center_offset"]) < 1: continue
                if max(data["center_offset"]) > max_center_offset:
                    max_center_offset = max(data["center_offset"])
                n += len(data["center_offset"])
                avg_center_offset += sum(data["center_offset"])
        avg_center_offset = avg_center_offset / n

        return max_center_offset, avg_center_offset
    
    def get_braking_user_measure(output_title):
        waypoints_fpath = f"analyzation/{output_title}/trajectories/"
        fnames = os.listdir(waypoints_fpath)
        distance_to_obstacle_list = []
        
        obstacle_x = -20
        front_length = 4.5
        
        for fname in fnames:
            if ".yaml" not in fname: continue
            with open(f"{waypoints_fpath}{fname}", "r") as f:
                data = yaml.safe_load(f)
                if len(data["waypoints"]) < 1: continue                
                last_x = data["waypoints"][-1]["x"]
                # distance = last_x - 5 - 4.5 # Hard coding (5: end of obstacle, 4.5: base_link to front)
                distance = last_x - obstacle_x - front_length # obstacles moved to -25
                distance_to_obstacle_list.append(distance)
        
        if len(distance_to_obstacle_list) != 0:
            min_distance_to_obstacle = min(distance_to_obstacle_list)
            avg_distance_to_obstacle = sum(distance_to_obstacle_list)/len(distance_to_obstacle_list)
        else:
            min_distance_to_obstacle = -1.0
            avg_distance_to_obstacle = -1.0
            
        return min_distance_to_obstacle, avg_distance_to_obstacle
    
    def get_lane_change_user_measure(output_title):
        with open(f"results/{output_title}/0/experiment_info.yaml", "r") as f:
            experiment_info = yaml.safe_load(f)
        scenario = experiment_info["scenario"]
        
        waypoints_fpath = f"analyzation/{output_title}/trajectories/"
        fnames = os.listdir(waypoints_fpath)
               
        obstacle_x = -7.5
        front_length = 4.5
        center_line_y = 57.0
        left_line_y = 52.0
        
        """
                                   (start)-------------------- <- y: 57
                                  /
        (end) -----------(finish)/ <- y: 52
        """
        
        lane_change_duration_list = []
        distance_to_obstacle_at_start_list = []
        for fname in fnames:
            lane_change_duration = 0.0
            start_idx = -1
            finish_idx = -1
            end_idx = -1
            
            if ".yaml" not in fname: continue
            with open(f"{waypoints_fpath}{fname}", "r") as f:
                data = yaml.safe_load(f)
                waypoints = data["waypoints"]
                if len(waypoints) < 1: continue
                
                idx_line_map = {}
                
                # Get idx-line map and end idx
                for i in range(len(waypoints)):
                    cur_x = float(waypoints[i]["x"])
                    cur_y = float(waypoints[i]["y"])
                    
                    # Skip start
                    if cur_x > 40:
                        continue
                    
                    if abs(cur_y - center_line_y) < 1.0: idx_line_map[i] = "center"
                    elif abs(cur_y - left_line_y) < 1.0: idx_line_map[i] = "left"
                    else: idx_line_map[i] = "change"
                    
                    # End idx
                    if cur_x < -40 or i == len(waypoints)-1:
                        end_idx = i
                        break
        
                # Find start and finish idx
                prev_line = "None"
                for idx in idx_line_map:
                    line = idx_line_map[idx]
                    if prev_line == "None":
                        prev_line = line
                        continue
                    
                    if start_idx == -1 and line == "change": start_idx = idx
                    if start_idx == -1 and line != "change": start_idx = -1
                    
                    if finish_idx == -1 and line == "left": finish_idx = idx
                    if finish_idx != -1 and line != "left": finish_idx = -1
                    
                    prev_line = line
            
            lane_change_duration = float(waypoints[end_idx]["time_stamp"]) - float(waypoints[start_idx]["time_stamp"])
            lane_change_duration_list.append(lane_change_duration)
            distance_to_obstacle_at_start_list.append(float(waypoints[start_idx]["x"]) - obstacle_x - front_length)
    
        if len(lane_change_duration_list) != 0:
            max_lane_change_duration = max(lane_change_duration_list)
            avg_lane_change_duration = sum(lane_change_duration_list)/len(lane_change_duration_list)
            max_distance_to_obstacle_at_start = max(distance_to_obstacle_at_start_list)
            avg_distance_to_obstacle_at_start = sum(distance_to_obstacle_at_start_list)/len(distance_to_obstacle_at_start_list)
        else:
            max_lane_change_duration = -1.0
            avg_lane_change_duration = -1.0
            max_distance_to_obstacle_at_start = -1.0
            avg_distance_to_obstacle_at_start = -1.0

        return max_lane_change_duration, avg_lane_change_duration, max_distance_to_obstacle_at_start, avg_distance_to_obstacle_at_start
    
    user_measure_info = {"scenario": scenario}
    if scenario == "handling":
        max_center_offset, avg_center_offset = get_handling_user_measure(output_title)    
        user_measure_info["center_offset"] = {"max": max_center_offset, "avg": avg_center_offset}
    elif scenario == "braking":
        min_distance_to_obstacle, avg_distance_to_obstacle = get_braking_user_measure(output_title)
        user_measure_info["distance_to_obstacle"] = {"min": min_distance_to_obstacle, "avg": avg_distance_to_obstacle}
    elif scenario == "lane_change":
        max_lane_change_duration, avg_lane_change_duration, max_distance_to_obstacle_at_start, avg_distance_to_obstacle_at_start = get_lane_change_user_measure(output_title)
        user_measure_info["lane_change_duration"] = {"max": max_lane_change_duration, "avg": avg_lane_change_duration}
        user_measure_info["distance_to_obstacle_at_start"] = {"max": max_distance_to_obstacle_at_start, "avg": avg_distance_to_obstacle_at_start}
    
    with open(f"analyzation/{output_title}/user_measure.yaml", "w") as f:
        yaml.dump(user_measure_info, f)
    
    
    return

if __name__ == '__main__':
    with open('yaml/autoware_analyzer.yaml') as f:
        configs = yaml.load(f, Loader=yaml.FullLoader)

    chain_info = configs['node_chain']
    avoidance_x_range = configs['avoidnace_x_range']
    online_profiling = configs['online_profiling']
    if online_profiling:
        online_profiling_duration = configs['online_profiling_duration']
        sleep_bar = tqdm(range(online_profiling_duration))
        sleep_bar.set_description(f'Sleep during {online_profiling_duration} seconds')
        for sleep_tick in sleep_bar:
            time.sleep(1)
        get_current_experiment_output()
        get_recent_data()


    for i in range(len(configs['experiment_title'])):
        experiment_title = configs['experiment_title'][i]
        if online_profiling:
            experiment_title = 'cur_adas'
        output_title = configs['output_title'][i]
        first_node = configs['first_node'][i]
        last_node = configs['last_node'][i]
        deadline = configs['E2E_deadline'][i]        

        source_path = 'results/' + experiment_title

        n = aa.get_number_of_files(source_path) - 1
        is_collapsed_list = []
        is_matching_failed_list = []
        max_miss_alignment_delay_list = []
        avg_miss_alignment_delay_list = []
        pbar = tqdm(range(n))
        pbar.set_description(output_title)
        
        for idx in pbar:
            # Collision
            experiment_info_path = source_path + '/' + str(idx) + '/experiment_info.yaml'
            experiment_info = aa.get_experiment_info(experiment_info_path)
            is_collapsed = experiment_info['is_collaped']
            is_collapsed_list.append(is_collapsed)  

            # Center offset
            center_offset_path = source_path + '/' + str(idx) + '/center_offset.csv'
            center_offset, max_center_offset, avg_center_offset \
                = aa.get_center_offset(center_offset_path)
            start_instance = int(list(center_offset.keys())[0])
            end_instance = int(list(center_offset.keys())[-1])
            profile_center_offset(center_offset_path, output_title, center_offset, max_center_offset, avg_center_offset, is_collapsed)

            # Check matching is failed
            is_matching_failed = aa.check_matching_is_failed(center_offset_path, start_instance, end_instance, configs['simulator'])
            is_matching_failed_list.append(is_matching_failed)

            # E2E response time during avoidance
            avoidance_start_instnace, avoidance_end_instance = aa.get_instance_pair(center_offset_path, avoidance_x_range[0], avoidance_x_range[1], configs['simulator'])
            response_time_path = source_path + '/' + str(idx) + '/response_time'            
            profile_response_time(response_time_path, output_title, first_node, last_node, avoidance_start_instnace, avoidance_end_instance, is_collapsed, is_matching_failed)

            # Miss alignment delay for whole driving
            max_miss_alignment_delay, avg_miss_alignment_delay = profile_miss_alignment_delay(response_time_path, output_title, chain_info, start_instance, end_instance, is_collapsed)
            max_miss_alignment_delay_list.append(max_miss_alignment_delay)
            avg_miss_alignment_delay_list.append(avg_miss_alignment_delay)

            # Trajectories
            dir_path = source_path + '/' + str(idx)
            profile_waypoints(dir_path, output_title, is_collapsed_list[idx], is_matching_failed)            
        
        # Profile information from whole experiment
        is_collapsed_list = aa.convert_boolean_list_to_int_list(is_collapsed_list)        
        is_matching_failed = aa.convert_boolean_list_to_int_list(is_matching_failed_list) 
        avg_center_offset = profile_avg_center_offset_for_experiment(source_path, is_matching_failed_list)        
        perf_info = profile_perf_info_for_experiment(source_path) # Perf related info(memory bandwidth, l3d_cache_refill count)        
        profile_analyzation_info(source_path, output_title, avg_center_offset, is_collapsed_list, is_matching_failed_list, max_miss_alignment_delay_list, avg_miss_alignment_delay_list, perf_info)
        
        # Profile avoidnace response time
        profile_response_time_for_experiment(source_path, output_title, first_node, last_node, is_collapsed_list, is_matching_failed, x_range=avoidance_x_range, deadline=deadline)
        
        # Profile waypoints
        profile_waypoints_for_experiment(source_path, output_title, is_collapsed_list, is_matching_failed)

        # Get user measure
        get_user_measures(output_title)
