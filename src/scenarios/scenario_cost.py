import os
import sys
import simpy
import numpy as np
import random
from src.simulation.waterfall.finite import WaterfallMoulinetteFinite
from src.models.basics import Utilisateur
from src.utils.cost_analysis import CostAnalyzer, create_cost_config_aws_small
from src.visualization.cost_plots import plot_cost_comparison, plot_scaling_analysis


def create_users(n, promo_ratio=0.7):
    users = []
    for i in range(n):
        promo = "ING" if random.random() < promo_ratio else "PREPA"
        users.append(Utilisateur(name=f"USER{i}", promo=promo))
    return users


def run_test_for_k(k, num_users=30):
    moulinette = WaterfallMoulinetteFinite(
        K=k, 
        process_time=2, 
        result_time=1, 
        ks=20, 
        kf=10, 
        tag_limit=5, 
        nb_exos=5
    )
    users = create_users(num_users)
    
    for user in users:
        moulinette.add_user(user)
    
    moulinette.env.process(moulinette.collect_metrics())
    
    for user in moulinette.users:
        moulinette.env.process(moulinette.handle_commit(user))
    
    moulinette.env.run(until=None)
    
    return moulinette


def analyze_server_costs():
    results_dir = "output/cost_analysis"
    os.makedirs(results_dir, exist_ok=True)
    
    random.seed(42)
    np.random.seed(42)
    
    cost_config = create_cost_config_aws_small()
    cost_config.simulation_duration_hours = 1.0
    analyzer = CostAnalyzer(cost_config)
    
    server_configs = [1, 2, 4, 6, 8, 10]
    cost_results = []
    
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    
    try:
        for num_servers in server_configs:
            moulinette = run_test_for_k(num_servers)
            
            metrics_obj = moulinette.metrics.calculate_metrics()
            
            metrics = {
                "test_queue": {
                    "blocking_rate": metrics_obj["test_queue"]["blocking_rate"],
                },
                "result_queue": {
                    "blocking_rate": metrics_obj["result_queue"]["blocking_rate"],
                },
                "sojourn_times": {
                    "test_queue": {"avg": metrics_obj["sojourn_times"]["test_queue"]["avg"] / 60},
                    "result_queue": {"avg": metrics_obj["sojourn_times"]["result_queue"]["avg"] / 60}
                }
            }
            
            cost_result = analyzer.calculate_total_cost(
                num_test_servers=num_servers,
                metrics=metrics,
                total_requests=moulinette.metrics.total_requests,
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