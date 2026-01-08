import simpy
import numpy as np
import os
from src.simulation.populations import run_population_sim
from src.simulation.priority import run_priority_sim
from src.utils.metrics import print_summary
from src.visualization.plots import plot_stay_times

def analyze_channels():
    print("--- Running Scenario 2: Channels and Dams ---")
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    # ING: frequent, fast
    ing_arrival = 3.0
    ing_exec = 6.0
    
    # PREPA: rare, slow
    prepa_arrival = 0.3
    prepa_exec = 0.5
    
    # 1. Base
    env = simpy.Environment()
    sim_base = run_population_sim(env, ing_arrival, prepa_arrival, ing_exec, prepa_exec, num_exec=1, duration=5000)
    print("\n--- Base Case (No Block) ---")
    print_summary("Base", sim_base)

    # 2. Dam
    env = simpy.Environment()
    sim_dam = run_population_sim(env, ing_arrival, prepa_arrival, ing_exec, prepa_exec, num_exec=1, initial_tb=10.0, duration=5000)
    print("\n--- Dam Case (tb=10s) ---")
    print_summary("Dam", sim_dam)

    # 3. Priority Queue
    env = simpy.Environment()
    sim_priority = run_priority_sim(env, ing_arrival, prepa_arrival, ing_exec, prepa_exec, num_exec=1, duration=5000)
    print("\n--- Priority Case (PREPA > ING) ---")
    print_summary("Priority", sim_priority)

    plot_stay_times({
        "ING Base": sim_base.stats['ING']['stay_times'],
        "PREPA Base": sim_base.stats['PREPA']['stay_times'],
        "ING Priority": sim_priority.stats['ING']['stay_times'],
        "PREPA Priority": sim_priority.stats['PREPA']['stay_times']
    }, "Comparison: Base vs Priority", f"{results_dir}/scenario2_priority_impact.png")

if __name__ == "__main__":
    analyze_channels()
