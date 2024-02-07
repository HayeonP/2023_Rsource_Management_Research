import csv
import yaml
import os
import glob

adas_exp_path_list = glob.glob(f'analyzation/240207_b7000_adas_b4000_seqwr_*')



def get_exp_info(version):
    exp_info = {}
    adas_exp_label = f'240207_b7000_adas_b4000_seqwr_v{version}'

    is_collapsed = False

    with open(f'analyzation/{adas_exp_label}/{adas_exp_label}_E2E_response_time_info(all,shortest).yaml') as f:
        exp_results = yaml.safe_load(f)

    adas_avg_E2E = exp_results['avg']
    adas_99percentile_E2E = exp_results['percentile_99']

    with open(f'analyzation/{adas_exp_label}/analyzation_info.yaml') as f:
        exp_results = yaml.safe_load(f)
        if len(exp_results['result']['collision_index']) > 0:
            is_collapsed = True

    exp_info['adas_avg_E2E'] = adas_avg_E2E
    exp_info['adas_99percentile_E2E'] = adas_99percentile_E2E
    exp_info['is_collapsed'] = is_collapsed

    return exp_info


def write_adas_E2E(exp_info_list):
    with open(f'test.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['adas_budget', 'seqwr_budget', 'avg_E2E', '99percentile_E2E', 'is_collapsed'])

        for exp_info in exp_info_list:
            writer.writerow([7000, 4000, exp_info['adas_avg_E2E'], exp_info['adas_99percentile_E2E'], exp_info['is_collapsed']])

if __name__ == '__main__':
    exp_info_list = []
    # for i in range(100):
    #     exp_info = get_exp_info(i)
    #     exp_info_list.append(exp_info)
    
    # write_adas_E2E(exp_info_list)
    print('start')
    for i in range(68):
        adas_exp_label = f'240207_b7000_adas_b4000_seqwr_v{i}'
        with open("yaml/autoware_analyzer.yaml", "r") as f:
            analyzer_config = yaml.load(f, Loader=yaml.FullLoader)

        analyzer_config["experiment_title"] = [adas_exp_label]
        analyzer_config["output_title"] = [adas_exp_label]

        with open("yaml/autoware_analyzer.yaml", "w") as f:
            yaml.dump(analyzer_config, f)

        os.system('python3 autoware_analyzer.py')