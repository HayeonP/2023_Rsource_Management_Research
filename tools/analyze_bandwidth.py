import yaml
import csv
import matplotlib.pyplot as plt
import sys
import os
import numpy

def plot_bandwidth_profile():

    with open('configs/bw_profiler.yaml') as f:
        configs = yaml.load(f, yaml.FullLoader)
    label = configs['label']
    xlim = configs['xlim']
    ylim = configs['ylim']
    ssh_address = configs['ssh_address']
    target_project_dir = configs['target_project_dir']
        
    exynos_bw_file_path = f'{target_project_dir}/bw_profiler/{label}/{label}.dat'
    host_bw_file_path = f'bw_profiler/{label}/'
    if not os.path.exists(host_bw_file_path):
        os.system(f'mkdir -p bw_profiler/{label}')
    os.system(f'scp -r {ssh_address}:{exynos_bw_file_path} {host_bw_file_path}')

    calibration = 0.0
    time_list = []
    fetch_list = []
    bw_list = []
    time_diff_list = []
    prev_time_list = {}
    time_diff_per_core_list = {}
    bw_per_core_list = {}
    time_per_core_list = {}
    total_fetch = 0.0
    bw_profile_path = host_bw_file_path + f'{label}.dat'
    plot_path = host_bw_file_path + f'{label}.png'
    info_path = host_bw_file_path + f'{label}.info'
    
        
    with open(bw_profile_path) as f:
        reader = csv.reader(f)
        
        for i, line in enumerate(reader):

            core_num = line[0].split()[0]

            if line[0].split()[1].split(':')[0] == 'K' or line[0].split()[1].split(':')[0] == 'U':
                if i == 0:
                    calibration = float(line[0].split()[2].split(':')[0])
                cur_time = float(line[0].split()[2].split(':')[0])
                time = cur_time - calibration
                fetch_count = float(line[0].split()[3])
            else:
                if i == 0:
                    calibration = float(line[0].split()[1].split(':')[0])
                cur_time = float(line[0].split()[1].split(':')[0])
                time = cur_time - calibration
                fetch_count = float(line[0].split()[2])


            if core_num not in prev_time_list:
                prev_time_list[core_num] = cur_time
                time_diff_per_core_list[core_num] = []
                bw_per_core_list[core_num] = []
                time_per_core_list[core_num] = []
                continue
            else:
                prev_time = prev_time_list[core_num]
                time_diff = cur_time - prev_time
                bw_count = fetch_count * 64 / time_diff / 1024.0 / 1024.0 / 1024.0

            if time <=0.0:
                continue


            total_fetch += fetch_count
            time_list.append(time)
            fetch_list.append(fetch_count)
            time_diff_list.append(time_diff)
            time_diff_per_core_list[core_num].append(time_diff)
            bw_list.append(bw_count)
            time_per_core_list[core_num].append(time)
            bw_per_core_list[core_num].append(bw_count)
            
            prev_time_list[core_num] = cur_time



    if not any(fetch_list):
        print(f'[Error] Zero Profiling Data')
        exit()
    
    bw_std = numpy.std(bw_list)
    cnt = 0
    bw_limit = 10
    over_bw_time = []

    new_bw_list = {time:0 for time in time_list}
    for time in new_bw_list:
        bw = 0
        for core in time_per_core_list:
            for i, per_core_time in enumerate(time_per_core_list[core]):
                if time <= per_core_time:
                    bw += bw_per_core_list[core][i]
                    # print(f'core: {core}, core bw: {bw_per_core_list[core][i]}, total bw: {bw}')
                    break

        new_bw_list[time] = bw
        if bw >= bw_limit:
            over_bw_time.append(time)
            cnt += 1
    # print(new_bw_list.keys())
    # print(new_bw_list.values())

    graph_area = 0
    for i, time in enumerate(time_list):
        if i == 0:
            continue
        bw = new_bw_list[time]
        time_delta = time_list[i] - time_list[i-1]
        graph_area += bw * time_delta

    over_graph_area = 0
    for i, time in enumerate(time_list):
        if i == 0:
            continue
        if time in over_bw_time:
            bw = new_bw_list[time]
            time_delta = time_list[i] - time_list[i-1]
            over_graph_area += (bw - bw_limit) * time_delta
            # seq wr. 6.2, 0.09     0.00029
            # ivi          0.013    0.003388

    print("Memory bandwidth : {:.3f} GB/s\n".format(total_fetch *64 /(time_list[len(time_list)-1]-time_list[0])/ 1024.0 / 1024.0 / 1024.0))
    # print(f"Memory bandwidth std: {bw_std}")
    # print(f'max time interval: {max(time_diff_list)}, min time interval: {min(time_diff_list[10:])}, time interval std: {numpy.std(time_diff_list)}')
    # print(f'new bandwidth: {sum(list(new_bw_list.values())) / len(list(new_bw_list.values()))}')
    # print(f'over {bw_limit}GB/s ratio: {cnt / len(list(new_bw_list.values()))}')
    # print(f'graph area: {graph_area}')
    # print(f'over {bw_limit}GB/s graph area: {over_graph_area}')
    # print(f'event fetch frequency: {len(time_list) / (time_list[-1] - time_list[0]) / len(time_per_core_list)}')
    # for core in time_per_core_list:
    #     print(f'core{core} event fetch frequency: {len(time_per_core_list[core]) / (time_per_core_list[core][-1] - time_per_core_list[core][0])}')

    f = open(info_path, 'w')
    f.write("Memory bandwidth : {:.3f} GB/s\n".format(total_fetch *64 /(time_list[len(time_list)-1]-time_list[0])/ 1024.0 / 1024.0 / 1024.0))
    f.write(f"Memory bandwidth std: {bw_std}\n")
    f.write(f'max time interval: {max(time_diff_list)}, min time interval: {min(time_diff_list[10:])}, time interval std: {numpy.std(time_diff_list)}\n')
    f.write(f'new bandwidth: {sum(list(new_bw_list.values())) / len(list(new_bw_list.values()))}\n')
    f.write(f'over {bw_limit}GB/s ratio: {cnt / len(list(new_bw_list.values()))}\n')
    f.write(f'graph area: {graph_area}\n')
    f.write(f'over {bw_limit}GB/s graph area: {over_graph_area}\n')
    f.write(f'event fetch frequency: {len(time_list) / (time_list[-1] - time_list[0]) / len(time_per_core_list)}\n')
    for core in time_per_core_list:
        f.write(f'core{core} event fetch frequency: {len(time_per_core_list[core]) / (time_per_core_list[core][-1] - time_per_core_list[core][0])}\n')

    f.close()
    ax1 = plt.subplot()
    ax1.set_ylabel('Memory Bandwidth (GB/s)')
    ax1.set_xlabel('Time(s)')    
    lns1= ax1.plot(list(new_bw_list.keys()), list(new_bw_list.values()), 'black', label='Bandwidth (GB/s)')
    # temp = {}
    # for time in new_bw_list:
    #     if new_bw_list[time] >= bw_limit:
    #         temp[time] = new_bw_list[time]
    # lns1= ax1.scatter(list(temp.keys()), list(temp.values()), s=0.1)


    plt.xticks(fontsize=10)
    plt.yticks(fontsize=8)
    ax1.set_xlim(xlim)
    ax1.set_ylim(ylim)
    
    lns = lns1
    #lns = lns1 + lns3
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc='lower left')

    # plt.show()
    plt.savefig(plot_path)
    plt.close()


if __name__ == '__main__':
    plot_bandwidth_profile()