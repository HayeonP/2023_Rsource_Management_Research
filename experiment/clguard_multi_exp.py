import os
import subprocess
import multiprocessing
import yaml
import csv
import json
from tqdm import tqdm
import time

def adas_with_clguard_exp_setup(adas_budget):
    label = f'{experiment_tag}_b{adas_budget}_adas'
    os.system(f'sed -i "/label/ c\label: {label}" yaml/clguard_single_exp.yaml')

    # clguard1 settings
    os.system(f'sed -i "/run_clguard1/ c\run_clguard1: True" yaml/clguard_single_exp.yaml')
    os.system(f'sed -i "/clguard1_target_cores/ c\clguard1_target_cores: 4-7" yaml/clguard_single_exp.yaml')
    os.system(f'sed -i "/clguard1_budget/ c\clguard1_budget: {adas_budget}" yaml/clguard_single_exp.yaml')

    # seqwr settings
    os.system(f'sed -i "/run_seqwr/ c\run_seqwr: False" yaml/clguard_single_exp.yaml')
    # clguard2 settings
    os.system(f'sed -i "/run_clguard2/ c\run_clguard2: False" yaml/clguard_single_exp.yaml')

def adas_with_clguard_seqwr_without_clguard_exp_setup(adas_budget, seqwr_budget):
    label = f'{experiment_tag}_b{adas_budget}_adas_seqwr{seqwr_budget}'
    os.system(f'sed -i "/label/ c\label: {label}" yaml/clguard_single_exp.yaml')

    # clguard1 settings
    os.system(f'sed -i "/run_clguard1/ c\run_clguard1: True" yaml/clguard_single_exp.yaml')
    os.system(f'sed -i "/clguard1_target_cores/ c\clguard1_target_cores: 4-7" yaml/clguard_single_exp.yaml')
    os.system(f'sed -i "/clguard1_budget/ c\clguard1_budget: {adas_budget}" yaml/clguard_single_exp.yaml')

    # seqwr settings
    os.system(f'sed -i "/run_seqwr/ c\run_seqwr: True" yaml/clguard_single_exp.yaml')
    os.system(f'sed -i "/seqwr_core_list/ c\seqwr_core_list: [1]" yaml/clguard_single_exp.yaml')
    os.system(f'sed -i "/seqwr_budget_list/ c\seqwr_budget_list: [{seqwr_budget}]" yaml/clguard_single_exp.yaml')

    # clguard2 settings
    os.system(f'sed -i "/run_clguard2/ c\run_clguard2: False" yaml/clguard_single_exp.yaml')
    
def adas_with_clguard_seqwr_with_clguard_exp_setup(adas_budget, seqwr_budget):
    label = f'{experiment_tag}_b{adas_budget}_adas_b{seqwr_budget}_seqwr'
    os.system(f'sed -i "/label/ c\label: {label}" yaml/clguard_single_exp.yaml')

    # clguard1 settings
    os.system(f'sed -i "/run_clguard1/ c\run_clguard1: True" yaml/clguard_single_exp.yaml')
    os.system(f'sed -i "/clguard1_target_cores/ c\clguard1_target_cores: 4-7" yaml/clguard_single_exp.yaml')
    os.system(f'sed -i "/clguard1_budget/ c\clguard1_budget: {adas_budget}" yaml/clguard_single_exp.yaml')

    # seqwr settings
    os.system(f'sed -i "/run_seqwr/ c\run_seqwr: True" yaml/clguard_single_exp.yaml')
    os.system(f'sed -i "/seqwr_core_list/ c\seqwr_core_list: [1]" yaml/clguard_single_exp.yaml')
    os.system(f'sed -i "/seqwr_budget_list/ c\seqwr_budget_list: [204800]" yaml/clguard_single_exp.yaml')

    # clguard2 settings
    os.system(f'sed -i "/run_clguard2/ c\run_clguard2: False" yaml/clguard_single_exp.yaml')
    os.system(f'sed -i "/clguard2_target_cores/ c\clguard2_target_cores: 1-3" yaml/clguard_single_exp.yaml')
    os.system(f'sed -i "/clguard2_budget/ c\clguard2_budget: {seqwr_budget}" yaml/clguard_single_exp.yaml')

if __name__ == '__main__':
    with open('yaml/clguard_multi_exp.yaml') as f:
        configs = yaml.load(f, Loader=yaml.FullLoader)

    adas_iteration = configs['adas_iteration']
    adas_duration = configs['adas_duration']

    experiment_tag = configs['experiment_tag']
    adas_budget_list = configs['adas_budget_list']
    seqwr_budget_list = configs['seqwr_budget_list']

    os.system(f'sed -i "/adas_iteration/ c\adas_iteration: {adas_iteration}" yaml/clguard_single_exp.yaml')
    os.system(f'sed -i "/adas_duration/ c\adas_duration: {adas_duration}" yaml/clguard_single_exp.yaml')

    for adas_budget in adas_budget_list:
        for seqwr_budget in seqwr_budget_list:
            adas_with_clguard_exp_setup(adas_budget)
            os.system(f'python3 clguard_single_exp.py')
            adas_with_clguard_seqwr_without_clguard_exp_setup(adas_budget, seqwr_budget)
            os.system(f'python3 clguard_single_exp.py')
            adas_with_clguard_seqwr_with_clguard_exp_setup(adas_budget, seqwr_budget)
            os.system(f'python3 clguard_single_exp.py')