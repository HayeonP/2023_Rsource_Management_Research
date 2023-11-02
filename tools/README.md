# How to use

### Memory Mapping
1. Setup parameters in `configs/profile_memory_mapping.yaml`.
2. Run `profile_memory_mapping.sh`.
3. Run `analyze_memory_mapping.sh`.
    * Copy resutls from target and analyze it.

### Perf Events
1. Setup parameters in `configs/profile_perf_events.yaml`.
2. Run `profile_perf_events.sh`.
3. Run `analyze_perf_events.sh`.
    * Copy resutls from target and analyze it.

### Bandwidth
1. Setup parameters in `configs/bw_profiler.yaml`.
2. Run `profile_bandwidth.sh`.
3. Run `analyze_bandwidth.sh`.
    * Copy resutls from target and analyze it.

### Run Sequential Write
1. Setup Target Memory Bandwidth in `sequential_write.c`.
2. Run `make_sequential_write.sh`.
3. Run `a.out` in Exynos Auto V9 `/home/root/sdd/tools` directory.

### Memguard Auto experiment
1. Setup Target Workload and Memory Bandwidth in `configs.auto_memguard_experiment.yaml`.
2. Run `auto_memguard_experiment.sh`.
3. Run `analyze_auto_memguard_experiment.sh`.