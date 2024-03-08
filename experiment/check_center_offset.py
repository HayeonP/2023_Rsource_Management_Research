import os
import csv
import yaml
import numpy as np
import glob
import matplotlib.pyplot as plt

class EXP_INFO:
    def __init__(self, exp_date, exp_title, iteration, percentile99_E2E, max_center_offset, percentile99_center_offset, avg_center_offset):
        self.exp_date = exp_date
        self.exp_title = exp_title
        self.iteration = iteration
        self.percentile99_E2E = percentile99_E2E
        self.max_center_offset = max_center_offset
        self.percentile99_center_offset = percentile99_center_offset
        self.avg_center_offset = avg_center_offset

def update_adas_config(label):
    # update autoware analyzer config
    with open("yaml/autoware_analyzer.yaml", "r") as f:
        analyzer_config = yaml.load(f, Loader=yaml.FullLoader)

    analyzer_config["experiment_title"] = [label]
    analyzer_config["output_title"] = [label]

    with open("yaml/autoware_analyzer.yaml", "w") as f:
        yaml.dump(analyzer_config, f)



def re_analyze():
    exp_path_list = glob.glob(f'results/240216/*')
    for exp_path in exp_path_list:
        exp_name = exp_path.split('/')[-1]
        exp_label = f'240216/{exp_name}'
        update_adas_config(exp_label)
        os.system(f'python3 autoware_analyzer.py')
    exp_path_list = glob.glob(f'results/240217/*')
    for exp_path in exp_path_list:
        exp_name = exp_path.split('/')[-1]
        exp_label = f'240217/{exp_name}'
        update_adas_config(exp_label)
        os.system(f'python3 autoware_analyzer.py')



def get_99percentile_E2E_max_center_offset_pair(exp_date, exp_title, iteration):
    with open(f'analyzation/{exp_date}/{exp_title}/shortest_E2E_response_time/{exp_title}_{iteration}_shortest_E2E_list.yaml') as f:
        e2e_info_dict = yaml.safe_load(f)
        e2e_list = e2e_info_dict['e2e_response_time']
        percentile99_E2E = np.percentile(e2e_list, 99)
    with open(f'analyzation/{exp_date}/{exp_title}/center_offset/{exp_title}_{iteration}_center_offset_info.yaml') as f:
        center_offset_dict = yaml.safe_load(f)
        center_offset_list = center_offset_dict['center_offset']
        max_center_offset = max(center_offset_list)
        percentile99_center_offset = np.percentile(center_offset_list, 99)
        avg_center_offset = sum(center_offset_list) / len(center_offset_list)
    
    return percentile99_E2E, max_center_offset, percentile99_center_offset, avg_center_offset


def make_99percentile_to_max_center_offset_table():
    date240216_path = glob.glob(f'results/240216/*')
    date240217_path = glob.glob(f'results/240217/*')
    all_exp_path = date240216_path
    all_exp_path.extend(date240217_path)
    exp_info_list = []

    for exp_path in all_exp_path:
        exp_date = exp_path.split('/')[-2]
        exp_title = exp_path.split('/')[-1]
        if exp_date == '240216':
            iteration = 1
        else:
            iteration = 3

        for it in range(iteration):
            percentile99_E2E, max_center_offset, percentile99_center_offset, avg_center_offset = get_99percentile_E2E_max_center_offset_pair(exp_date, exp_title, it)
            exp_info = EXP_INFO(exp_date, exp_title, iteration, percentile99_E2E, max_center_offset, percentile99_center_offset, avg_center_offset)
            exp_info_list.append(exp_info)

    exp_info_list = sorted(exp_info_list, key = lambda x: (x.percentile99_E2E))
    return exp_info_list

if __name__ == '__main__':
    # re_analyze()
    # exit(0)
    exp_info_list = make_99percentile_to_max_center_offset_table()
    with open('percentile99_to_center_offset.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['percentile99', 'max_center_offset', 'percentile99_center_offset', 'avg_center_offset', 'exp_date', 'exp_title', 'iteration'])
        for exp_info in exp_info_list:
            writer.writerow([exp_info.percentile99_E2E, exp_info.max_center_offset, exp_info.percentile99_center_offset, exp_info.avg_center_offset, exp_info.exp_date, exp_info.exp_title, exp_info.iteration])


    percentile99_list = [x.percentile99_E2E for x in exp_info_list]
    max_center_offset_list = [x.max_center_offset for x in exp_info_list]
    plt.plot(percentile99_list, max_center_offset_list)
    plt.xlabel('99%tile E2E response time (ms)')
    plt.ylabel('max center offset (m)')
    plt.savefig('percentile99_to_max_center_offset.png')
    plt.close()

    percentile99_list = [x.percentile99_E2E for x in exp_info_list]
    percentile99_center_offset_list = [x.percentile99_center_offset for x in exp_info_list]
    plt.plot(percentile99_list, percentile99_center_offset_list)
    plt.xlabel('99%tile E2E response time (ms)')
    plt.ylabel('99%tile center offset (m)')
    plt.savefig('percentile99_to_percentile99_center_offset.png')
    plt.close()

    percentile99_list = [x.percentile99_E2E for x in exp_info_list]
    avg_center_offset_list = [x.avg_center_offset for x in exp_info_list]
    plt.plot(percentile99_list, avg_center_offset_list)
    plt.xlabel('99%tile E2E response time (ms)')
    plt.ylabel('avg center offset (m)')
    plt.savefig('percentile99_to_avg_center_offset.png')
    plt.close()

