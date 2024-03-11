# User Measures Auto Experiment


## How to use


**1. Setup experiment**

Setup parameters in `/yaml/user_measures_auto_experiment.yaml`

1. experiment_tag : set experiment title

2. user_measure_scenario : select one of the user measures scenarios

    ```user_measure_scenario: ['braking', 'handling', 'lane_change']```

3. versions : how many times to run for each adas budget

4. adas_budget : clguard budget for adas

5. seqwr_budget : clguard budget or target BW for seqwr

    If you want to run adas only, Set seqwr budget [0, 0, 0, ... ]

    adas_budget[i] and seqwr_budet[i] are used at once in one experiment, so you have to set len(adas_budget) <= len
    (seqwr_budget)
    

6. seqwr_clguard : choose to use clguard or not for seqwr

    'y' -> use clguard

    'n' -> use seqwr parameter instead of clguard

<br/>

***experiment name templates***

[1] seqwr_budget: 0

-> `{tag}_{measure}_{adas budget}_adas_only_v{version}`

[2] seqwr_budget != 0, seqwr_clguard: 'y'

-> `{tag}_{measure}_{adas budget}_adas_{seqwr budget}_seqwr_v{version}`

[3] seqwr_budget != 0, seqwr_clguard: 'n'

-> `{tag}_{measure}_{adas budget}_adas_seqwr{seqwr_budget}_v{version}`

<br/><br/>
**2. run**

    python3 clguard_user_measures_auto_experiment.py 
