import yaml
import os
import subprocess
import multiprocessing
import time
from tqdm import tqdm
import csv
import glob
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import seaborn as sns


title='240131'
# label = f'{title}'

# analyzation_path = f'analyzation/{label}/{label}_E2E_response_time_info(all,shortest).yaml' # avg, percentile_99

adas_analyzation_path_list = glob.glob(f'analyzation/{title}_b*')



def get_adas_seqwr_budget_list(adas_analyzation_path_list):
    adas_budget_list = []
    seqwr_budget_list = []

    for adas_analyzation_path in adas_analyzation_path_list:
        adas_budget = int(adas_analyzation_path.split('/')[-1].split('_')[1].replace('b', ''))
        if adas_budget in adas_budget_list:
            continue
        
        adas_with_seqwr_path_list = glob.glob(f'analyzation/{title}_b{adas_budget}_adas_b*')
        for adas_with_seqwr_path in adas_with_seqwr_path_list:
            seqwr_budget = int(adas_with_seqwr_path.split('/')[-1].split('_')[3].replace('b', ''))
            adas_budget_list.append(adas_budget)
            seqwr_budget_list.append(seqwr_budget)
            # print(adas_budget, seqwr_budget)

    return adas_budget_list, seqwr_budget_list

def get_exp_info(adas_budget, seqwr_budget):
    adas_only_label = f'{title}_b{adas_budget}_adas'
    adas_with_seqwr_label = f'{title}_b{adas_budget}_adas_seqwr{seqwr_budget}'
    adas_with_clguard_seqwr_label = f'{title}_b{adas_budget}_adas_b{seqwr_budget}_seqwr'

    with open(f'analyzation/{adas_only_label}/{adas_only_label}_E2E_response_time_info(all,shortest).yaml') as f:
        exp_results = yaml.safe_load(f)

    adas_only_avg_E2E = exp_results['avg']
    adas_only_99percentile_E2E = exp_results['percentile_99']

    with open(f'analyzation/{adas_with_seqwr_label}/{adas_with_seqwr_label}_E2E_response_time_info(all,shortest).yaml') as f:
        exp_results = yaml.safe_load(f)

    adas_with_seqwr_avg_E2E = exp_results['avg']
    adas_with_seqwr_99percentile_E2E = exp_results['percentile_99']

    with open(f'analyzation/{adas_with_clguard_seqwr_label}/{adas_with_clguard_seqwr_label}_E2E_response_time_info(all,shortest).yaml') as f:
        exp_results = yaml.safe_load(f)

    adas_with_clguard_seqwr_avg_E2E = exp_results['avg']
    adas_with_clguard_seqwr_99percentile_E2E = exp_results['percentile_99']

    performance_isolation = True
    adas_seqwr_isolation = True
    adas_seqwr_with_clguard_isolation = True
    if adas_only_99percentile_E2E + 10 < adas_with_seqwr_99percentile_E2E:
        adas_seqwr_isolation = False
    if adas_only_99percentile_E2E + 10 < adas_with_clguard_seqwr_99percentile_E2E:
        adas_seqwr_with_clguard_isolation = False
    if adas_only_avg_E2E + 7 < adas_with_seqwr_avg_E2E or adas_only_avg_E2E + 7 < adas_with_clguard_seqwr_avg_E2E or \
        adas_only_99percentile_E2E + 10 < adas_with_seqwr_99percentile_E2E or adas_only_99percentile_E2E + 10 < adas_with_clguard_seqwr_99percentile_E2E:
        performance_isolation = False

    exp_info = {}
    exp_info['adas_budget'] = adas_budget
    exp_info['seqwr_budget'] = seqwr_budget
    exp_info['adas_only_avg_E2E'] = adas_only_avg_E2E
    exp_info['adas_only_99percentile_E2E'] = adas_only_99percentile_E2E
    exp_info['adas_with_seqwr_avg_E2E'] = adas_with_seqwr_avg_E2E
    exp_info['adas_with_seqwr_99percentile_E2E'] = adas_with_seqwr_99percentile_E2E
    exp_info['adas_with_clguard_seqwr_avg_E2E'] = adas_with_clguard_seqwr_avg_E2E
    exp_info['adas_with_clguard_seqwr_99percentile_E2E'] = adas_with_clguard_seqwr_99percentile_E2E
    exp_info['performance_isolation'] = performance_isolation
    exp_info['adas_seqwr_isolation'] = adas_seqwr_isolation
    exp_info['adas_seqwr_with_clguard_isolation'] = adas_seqwr_with_clguard_isolation

    # adas_only_99percentile_E2E, adas_with_seqwr_99percentile_E2E, adas_with_clguard_seqwr_99percentile_E2E
    


    return exp_info

def get_exp_info_list(adas_analyzation_path_list):
    exp_info_list = []
    alone_list = []
    no_clguard = []
    with_clguard = []

    adas_budget_list, seqwr_budget_list = get_adas_seqwr_budget_list(adas_analyzation_path_list)
    for i in range(len(adas_budget_list)):
        adas_budget = adas_budget_list[i]
        seqwr_budget = seqwr_budget_list[i]

        exp_info= get_exp_info(adas_budget, seqwr_budget)
        exp_info_list.append(exp_info)
    exp_info_list = sorted(exp_info_list, key = lambda x: (x['adas_budget'], x['seqwr_budget']))

    data = []
    seqwr_budget = range(1000, 7001, 1000)
    adas_budget = range(6000, 9001, 1000)

    data1 = []
    data2 = []

    temp_line1 = []
    temp_line2 = []


    for line in exp_info_list:
        sb = line["seqwr_budget"]
        sa = line["adas_budget"]
        wo_clguard = line["adas_with_seqwr_99percentile_E2E"] - line["adas_only_99percentile_E2E"]
        with_clguard = line["adas_with_clguard_seqwr_99percentile_E2E"] - line["adas_only_99percentile_E2E"]
        temp_line1.append(wo_clguard)
        temp_line2.append(with_clguard)
        if len(temp_line1) == 7:
            data1.append(temp_line1)
            data2.append(temp_line2)
            temp_line1 = []
            temp_line2 = []

    sns.heatmap(data1, annot=True, linewidths=.5, square=True, fmt = '.1f', cmap = 'YlOrRd')
    plt.savefig("1no_cl.jpg")
    plt.close()
    sns.heatmap(data2, annot=True, linewidths=.5, square=True, fmt = '.1f', cmap = 'YlOrRd')
    plt.savefig("2yes_cl.jpg")
    plt.close()

    exit()

    return exp_info_list

def write_exp_info(exp_info_list):
    with open(f'test.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['adas_budget', 'seqwr_budget', 'adas_only_avg_E2E', 'adas_only_99percentile_E2E', 
                        'adas_with_seqwr_avg_E2E', 'adas_with_seqwr_99percentile_E2E', 
                        'adas_with_clguard_seqwr_avg_E2E', 'adas_with_clguard_seqwr_99percentile_E2E',
                        'adas_seqwr_isolation', 'adas_seqwr_with_clguard_isolation', 'performance_isolation'])

        for exp_info in exp_info_list:
            writer.writerow([exp_info['adas_budget'], exp_info['seqwr_budget'], exp_info['adas_only_avg_E2E'], exp_info['adas_only_99percentile_E2E'], exp_info['adas_with_seqwr_avg_E2E'], exp_info['adas_with_seqwr_99percentile_E2E'], exp_info['adas_with_clguard_seqwr_avg_E2E'], exp_info['adas_with_clguard_seqwr_99percentile_E2E'], exp_info['adas_seqwr_isolation'],
                                exp_info['adas_seqwr_with_clguard_isolation'], exp_info['performance_isolation']])
            
def get_isolation_graph(exp_info_list):
    # ADAS + SeqWr (w/o Clguard)
    isolation_adas_budget_list = [v['adas_budget'] for v in exp_info_list if v['adas_seqwr_isolation'] == True]
    isolation_seqwr_budget_list = [v['seqwr_budget'] for v in exp_info_list if v['adas_seqwr_isolation'] == True]

    contention_adas_budget_list = [v['adas_budget'] for v in exp_info_list if v['adas_seqwr_isolation'] == False]
    contention_seqwr_budget_list = [v['seqwr_budget'] for v in exp_info_list if v['adas_seqwr_isolation'] == False]

    plt.scatter(isolation_adas_budget_list, isolation_seqwr_budget_list, label='no interference',color='blue', marker = 'o')
    plt.scatter(contention_adas_budget_list, contention_seqwr_budget_list, label='interferenced', color='red', marker = 'x')

    plt.xlabel('ADAS budget')
    plt.ylabel('SeqWr Bandwidth')

    plt.savefig('adas_seqwr_isolation_graph.png')
    
    plt.close()

    # ADAS + SeqWr (w/ Clguard)
    isolation_adas_budget_list = [v['adas_budget'] for v in exp_info_list if v['adas_seqwr_with_clguard_isolation'] == True]
    isolation_seqwr_budget_list = [v['seqwr_budget'] for v in exp_info_list if v['adas_seqwr_with_clguard_isolation'] == True]

    contention_adas_budget_list = [v['adas_budget'] for v in exp_info_list if v['adas_seqwr_with_clguard_isolation'] == False]
    contention_seqwr_budget_list = [v['seqwr_budget'] for v in exp_info_list if v['adas_seqwr_with_clguard_isolation'] == False]

    plt.scatter(isolation_adas_budget_list, isolation_seqwr_budget_list, label='no interference',color='blue', marker = 'o')
    plt.scatter(contention_adas_budget_list, contention_seqwr_budget_list, label='interferenced', color='red', marker = 'x')

    plt.xlabel('ADAS budget')
    plt.ylabel('SeqWr budget')

    plt.savefig('adas_seqwr_with_clguard_isolation_graph.png')

    plt.close()



if __name__ == '__main__':
    exp_info_list = get_exp_info_list(adas_analyzation_path_list)
    write_exp_info(exp_info_list)
    get_isolation_graph(exp_info_list)