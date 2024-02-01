import csv
import yaml
import json
import matplotlib.pyplot as plt

import os
import time
import numpy as np
import copy
import seaborn as sns
sns.set_style("white")

normal_case_title = f'240125_adas_only_vel9'
normal_case_it = 2
# stream_case_title = f'240125_adas_with_3stream_vel9_v3'
stream_case_title = f'240123_adas_1-3_stream_mp'
stream_case_it = 0

normal_case_e2e_path = f'analyzation/{normal_case_title}/shortest_E2E_response_time/{normal_case_title}_{normal_case_it}_shortest_E2E_list.yaml'
stream_case_e2e_path = f'analyzation/{stream_case_title}/shortest_E2E_response_time/{stream_case_title}_{stream_case_it}_shortest_E2E_list.yaml'

normal_case_e2e_dict = {}
stream_case_e2e_dict = {}

with open(normal_case_e2e_path) as f:
    normal_case_e2e_list = yaml.load(f, Loader=yaml.FullLoader)
    normal_case_instance = normal_case_e2e_list['instance_id']
    normal_case_e2e = normal_case_e2e_list['e2e_response_time']
    normal_case_e2e_dict = {instance_id: e2e_response_time for instance_id, e2e_response_time in zip(normal_case_instance, normal_case_e2e)}

with open(stream_case_e2e_path) as f:
    stream_case_e2e_list = yaml.load(f, Loader=yaml.FullLoader)
    stream_case_instance = stream_case_e2e_list['instance_id']
    stream_case_e2e = stream_case_e2e_list['e2e_response_time']
    stream_case_e2e_dict = {instance_id: e2e_response_time for instance_id, e2e_response_time in zip(stream_case_instance, stream_case_e2e)}

print(f'normal case avg E2E: {sum(normal_case_e2e) / len(normal_case_e2e)}, max E2E: {max(normal_case_e2e)}, min E2E: {min(normal_case_e2e)}')
print(f'stream case avg E2E: {sum(stream_case_e2e) / len(stream_case_e2e)}, max E2E: {max(stream_case_e2e)}, min E2E: {min(stream_case_e2e)}')
print(f'normal len: {len(normal_case_e2e)}')
print(f'stream len: {len(stream_case_e2e)}')

print(np.percentile(stream_case_e2e, 99))
print(np.percentile(normal_case_e2e, 99))
# plt.figure(figsize=(8,4))
# # plt.title('E2E response time')
# plt.plot(normal_case_instance, normal_case_e2e, color='b', label='Normal case')
# plt.plot(stream_case_instance, stream_case_e2e, color='r', label='Contention case')

# # plt.xlim(350, 850)
# plt.ylim(150, 400)

# plt.xlabel('Instance ID')
# plt.ylabel('E2E response time (ms)')

# plt.legend()

# plt.hist(normal_case_e2e,a)


# if 1 == 2:
bin_width = 2
bins = np.arange(0, 410, bin_width)

# kwargs = dict(hist_kws={'alpha':.6}, kde_kws={'linewidth':2})

# y = ((1 / (np.sqrt(2 * np.pi) * sigma)) *
#      np.exp(-0.5 * (1 / sigma * (bins - mu))**2))

plt.figure(figsize=(7.0,3.5))
plt.rc("font", size=15)
plt.hist(stream_case_e2e, bins=bins, color='red', alpha=1.0, edgecolor='none', density=True, label='w/ STREAM')
# plt.plot(bins, stream_case_e2e, )
plt.hist(normal_case_e2e, bins=bins, color='blue', alpha=1.0, edgecolor='none', density=True, label='ADAS only')
# sns.displot(normal_case_e2e, color='blue', label='Normal case', **kwargs)
# sns.displot(stream_case_e2e, color='red', label='Contention case', **kwargs)

# plt.axvline(np.percentile(stream_case_e2e, 99), color="r", linestyle="--")
# plt.axvline(np.percentile(normal_case_e2e, 99), color="b", linestyle="--")
# plt.axvline(max(stream_case_e2e), color="r", linestyle="--")
# plt.axvline(max(normal_case_e2e), color="b", linestyle="--")
plt.subplots_adjust(bottom=0.2, left=0.15)

plt.xlim(0, 410)

plt.xlabel('Response time (ms)')
plt.ylabel('Probability density (%)')

plt.legend()

plt.savefig('little_without_line.png')