import simpy
import numpy as np
import os
from src.simulation.engine import run_waterfall_sim
from src.utils.metrics import print_summary
from src.visualization.plots import plot_rejection_rates, plot_stay_times

def analyze_waterfall():
    print("--- Running Scenario 1: Waterfall ---")
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    arrival_rate = 1.2
    num_exec = 4
    exec_rate = 0.4  # Average 2.5s
    front_rate = 2.0 # Average 0.5s
    
    # Study 1: Finite Queue Size Impact
    ks_list = [2, 5, 10, 20, 50]
    exec_rejection_rates = []
    
    for ks in ks_list:
        env = simpy.Environment()
        sim = run_waterfall_sim(env, arrival_rate, num_exec, exec_rate, front_rate, ks=ks, kf=20, duration=5000)
        rate = sim.exec_rejected / sim.total_requests
        exec_rejection_rates.append(rate)
        print(f"ks={ks}: Rejection Rate = {rate:.2%}")

    plot_rejection_rates(ks_list, exec_rejection_rates, "Impact of Exec Queue Size on Rejection Rate", f"{results_dir}/scenario1_rejections.png")

    # Study 2: Backup vs No Backup
    env = simpy.Environment()
    sim_no_backup = run_waterfall_sim(env, arrival_rate, num_exec, exec_rate, front_rate, ks=20, kf=5, backup_prob=0.0, duration=5000)
    
    env = simpy.Environment()
    sim_backup = run_waterfall_sim(env, arrival_rate, num_exec, exec_rate, front_rate, ks=20, kf=5, backup_prob=1.0, duration=5000)
    
    print("\n--- Backup Comparison ---")
    print_summary("No Backup", sim_no_backup)
    print_summary("Full Backup", sim_backup)
    
    plot_stay_times({
        "No Backup": sim_no_backup.stay_times,
        "Full Backup": sim_backup.stay_times
    }, "Impact of Backup on Stay Times", f"{results_dir}/scenario1_backup_impact.png")

if __name__ == "__main__":
    analyze_waterfall()
