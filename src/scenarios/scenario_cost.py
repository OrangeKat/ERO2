import os
import sys
import simpy
import numpy as np
from src.simulation.engine import run_waterfall_sim
from src.utils.cost_analysis import CostAnalyzer, create_cost_config_aws_small
from src.visualization.cost_plots import plot_cost_comparison, plot_scaling_analysis


def analyze_server_costs():
    results_dir = "output/cost_analysis"
    os.makedirs(results_dir, exist_ok=True)
    
    arrival_rate = 1.2
    exec_rate = 0.4
    front_rate = 2.0
    ks = 20
    kf = 10
    duration = 5000
    
    cost_config = create_cost_config_aws_small()
    cost_config.simulation_duration_hours = 1.0
    analyzer = CostAnalyzer(cost_config)
    
    server_configs = [1, 2, 4, 6, 8, 10]
    cost_results = []
    
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    
    try:
        for num_servers in server_configs:
            env = simpy.Environment()
            sim = run_waterfall_sim(env, arrival_rate, num_servers, exec_rate, front_rate,
                                   ks=ks, kf=kf, duration=duration)
            
            metrics = {
                "test_queue": {
                    "blocking_rate": sim.exec_rejected / sim.total_requests if sim.total_requests > 0 else 0,
                },
                "result_queue": {
                    "blocking_rate": sim.front_rejected / sim.total_requests if sim.total_requests > 0 else 0,
                },
                "sojourn_times": {
                    "test_queue": {"avg": np.mean(sim.stay_times) * 0.3 / 60 if sim.stay_times else 0},
                    "result_queue": {"avg": np.mean(sim.stay_times) * 0.1 / 60 if sim.stay_times else 0}
                }
            }
            
            cost_result = analyzer.calculate_total_cost(
                num_test_servers=num_servers,
                metrics=metrics,
                total_requests=sim.total_requests,
                backup_enabled=False
            )
            
            cost_results.append(cost_result)
    finally:
        sys.stdout.close()
        sys.stdout = old_stdout
    
    labels = [f"K={k}" for k in server_configs]
    
    plot_cost_comparison(cost_results, labels, 
                        save_filename=f"{results_dir}/comparison.png")
    
    plot_scaling_analysis(server_configs, cost_results,
                         save_filename=f"{results_dir}/scaling.png")
    
    best_idx = np.argmin([c['cost_per_successful_request'] for c in cost_results])
    print(f"Optimal K: {server_configs[best_idx]}")


if __name__ == "__main__":
    analyze_server_costs()