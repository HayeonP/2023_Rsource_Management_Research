import csv
import yaml
import os
import json
import glob
import numpy as np

title_tag = '240208_b7000_adas'
adas_exp_path_list = glob.glob(f'analyzation/{title_tag}_v*')


def get_exp_info(adas_exp_label):
    exp_info = {}
    # adas_exp_label = f'{title_tag}_v{version}'

    is_collapsed = False

    with open(f'analyzation/{adas_exp_label}/{adas_exp_label}_E2E_response_time_info(all,shortest).yaml') as f:
        exp_results = yaml.safe_load(f)

    adas_avg_E2E = exp_results['avg']
    adas_99percentile_E2E = exp_results['percentile_99']

    with open(f'analyzation/{adas_exp_label}/analyzation_info.yaml') as f:
        exp_results = yaml.safe_load(f)
        if len(exp_results['result']['collision_index']) > 0:
            is_collapsed = True

    for i in range(3):
        with open(f'analyzation/{adas_exp_label}/shortest_E2E_response_time/{adas_exp_label}_{i}_shortest_E2E_list.yaml') as f:
            e2e_info = yaml.safe_load(f)
            e2e_list = e2e_info['e2e_response_time']
            exp_info[f'it{i}_avg_E2E'] = sum(e2e_list) / len(e2e_list)
            exp_info[f'it{i}_99percentile_E2E'] = np.percentile(e2e_list, 99)

        with open(f'/home/lee/experience/rubis-lab/ClusterLevelMemguard/tools/results/bw_profiler/{adas_exp_label}_it{i}/summary.json') as f:
            bw_profile_result = json.load(f)
            exp_info[f'it{i}_over7000_ratio'] = bw_profile_result['over7000_ratio']

        with open(f'results/{adas_exp_label}/configs/it{i}_clguard_config_start.txt') as f:
            lines = f.readlines()
            for line in lines:
                if 'Throttling count' in line:
                    start_throttling_count = int(line.replace(' ', '').split(':')[-1].split('-')[0])
                    # print(start_throttling_count)

        with open(f'results/{adas_exp_label}/configs/it{i}_clguard_config_end.txt') as f:
            lines = f.readlines()
            for line in lines:
                if 'Throttling count' in line:
                    end_throttling_count = int(line.replace(' ', '').split(':')[-1].split('-')[0])
        exp_info[f'it{i}_throttling_cnt'] = end_throttling_count - start_throttling_count
            

    version = int(adas_exp_label.split('_')[-1].replace('v', ''))

    exp_info['adas_avg_E2E'] = adas_avg_E2E
    exp_info['adas_99percentile_E2E'] = adas_99percentile_E2E
    exp_info['is_collapsed'] = is_collapsed
    exp_info['version'] = version

    return exp_info


def write_adas_E2E(exp_info_list):
    e2e_file_name = title_tag.replace(title_tag.split('_')[0] + '_', '') + '_e2e'
    with open(f'{e2e_file_name}.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['adas_budget', 'seqwr_budget', 'avg_E2E', '99percentile_E2E', 'is_collapsed', 'it0_99percentile_E2E', 'it1_99percentile_E2E', 'it2_99percentile_E2E', 'it0_over7000_ratio', 'it1_over7000_ratio', 'it2_over7000_ratio', 'it0_throttling_cnt', 'it1_throttling_cnt', 'it2_throttling_cnt', 'version'])

        for exp_info in exp_info_list:
            writer.writerow([7000, 4000, exp_info['adas_avg_E2E'], exp_info['adas_99percentile_E2E'], exp_info['is_collapsed'], exp_info['it0_99percentile_E2E'], exp_info['it1_99percentile_E2E'], exp_info['it2_99percentile_E2E'], exp_info['it0_over7000_ratio'], exp_info['it1_over7000_ratio'], exp_info['it2_over7000_ratio'], exp_info['it0_throttling_cnt'], exp_info['it1_throttling_cnt'], exp_info['it2_throttling_cnt'], exp_info['version']])

if __name__ == '__main__':
    exp_info_list = []
    for adas_exp_path in adas_exp_path_list:
        adas_exp_label = adas_exp_path.split('/')[-1]
        exp_info = get_exp_info(adas_exp_label)
        exp_info_list.append(exp_info)

    exp_info_list = sorted(exp_info_list, key = lambda x: (x['version']))
    
    write_adas_E2E(exp_info_list)
    adas_e2e_list = [v['adas_99percentile_E2E'] for v in exp_info_list]
    print(f'adas 99percentile E2E std: {np.std(adas_e2e_list)}')
    print(f'adas 99percentile E2E mean: {np.mean(adas_e2e_list)}')
    print(f'adas 99percentile E2E max: {max(adas_e2e_list)}, min: {min(adas_e2e_list)}')
    # print('start')
    # for i in range(69):
    #     adas_exp_label = f'240207_b7000_adas_b4000_seqwr_v{i}'
    #     with open("yaml/autoware_analyzer.yaml", "r") as f:
    #         analyzer_config = yaml.load(f, Loader=yaml.FullLoader)

    #     analyzer_config["experiment_title"] = [adas_exp_label]
    #     analyzer_config["output_title"] = [adas_exp_label]

    #     with open("yaml/autoware_analyzer.yaml", "w") as f:
    #         yaml.dump(analyzer_config, f)

    #     os.system('python3 autoware_analyzer.py')