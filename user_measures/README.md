# User Measures Auto Experiment


## How to use


**1. Setup experiment**

Setup parameters in /yaml/user_measures_auto_experiment.yaml

1. experiment_tag : set experiment title

2. user_measure_scenario : select one of the user measures scenarios

```user_measure_scenario: ['braking', 'handling', 'lane_change']```

3. versions : how many times to run for each budget

4. adas_budget : clguard budget for adas

5. seqwr_budget : clguard budget or target BW for seqwr

6. seqwr_clguard : choose to use clguard or not for seqwr


***experiment name templates***

[1] seqwr_budget: 0

-> `(tag)_{measure}_{adas budget}_adas_only_v{version}`

[2] seqwr_budget != 0, seqwr_clguard: 'y'

-> `{tag}_{measure}_{adas budget}_adas_{seqwr budget}_seqwr_v{version}`

[3] seqwr_budget != 0, seqwr_clguard: 'n'

-> `{tag}_{measure}_{adas budget}_adas_seqwr{seqwr_budget}_v{version}`



**2. run**

    python3 clguard_user_measures_auto_experiment.py 
