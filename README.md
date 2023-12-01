# Auto Experiment
### How to Use(for svl simulator)
1. Modify `experiment/svl_auto_experiment_configs.yaml`
2. Execute `roscore` on the target environment
3. Execute `rosbridge_server rosbridge_websocket`
4. Execute python script `experiment/svl_auto_experiment.py`


### Online Profiling(for svl simulator)
1. Modify online profiling, online profiling duration, output title in `experiment/configs/autoware_analyzer.yaml`
2. Execute `experiment/autoware_analyzer.py`
3. Recent experiment data in `experiment/analyzation/{output_title}`