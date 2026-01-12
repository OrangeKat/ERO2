import os
import sys
import simpy
import numpy as np
from src.simulation.waterfall.infinite import WaterfallMoulinetteInfinite
from src.simulation.waterfall.finite import WaterfallMoulinetteFinite
from src.simulation.waterfall.backup import WaterfallMoulinetteFiniteBackup
from src.simulation.channels_dams.channelsdams import ChannelsAndDams
from src.models.basics import Utilisateur
from src.utils.cost_analysis import CostAnalyzer, create_cost_config_aws_small
from src.visualization.cost_plots import plot_cost_comparison
import random


def create_users(n, promo_ratio=0.7):
    users = []
    for i in range(n):
        promo = "ING" if random.random() < promo_ratio else "PREPA"
        users.append(Utilisateur(name=f"USER{i}", promo=promo))
    return users


def run_architecture_test(architecture_class, config, num_users=30):
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    
    try:
        moulinette = architecture_class(**config)
        users = create_users(num_users)
        
        for user in users:
            moulinette.add_user(user)
        
        if isinstance(moulinette, ChannelsAndDams):
            moulinette.env.process(moulinette.regulate_ing())
        
        if isinstance(moulinette, WaterfallMoulinetteFiniteBackup) or isinstance(moulinette, ChannelsAndDams):
            moulinette.env.process(moulinette.free_backup())
        
        moulinette.env.process(moulinette.collect_metrics())
        
        for user in moulinette.users:
            moulinette.env.process(moulinette.handle_commit(user))
        
        moulinette.env.run(until=None)
        
        return moulinette
    finally:
        sys.stdout.close()
        sys.stdout = old_stdout


def extract_metrics_from_moulinette(moulinette):
    metrics_obj = moulinette.metrics.calculate_metrics()
    
    return {
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


def compare_all_architectures():
    results_dir = "output/cost_analysis_all"
    os.makedirs(results_dir, exist_ok=True)
    
    random.seed(42)
    np.random.seed(42)
    
    cost_config = create_cost_config_aws_small()
    cost_config.simulation_duration_hours = 1.0
    analyzer = CostAnalyzer(cost_config)
    
    num_users = 30
    
    architectures = [
        {
            "name": "W.Infinite",
            "class": WaterfallMoulinetteInfinite,
            "config": {"K": 4, "process_time": 2, "result_time": 1, "tag_limit": 5, "nb_exos": 5},
            "K": 4
        },
        {
            "name": "W.Finite",
            "class": WaterfallMoulinetteFinite,
            "config": {"K": 4, "process_time": 2, "result_time": 1, "ks": 20, "kf": 10, "tag_limit": 5, "nb_exos": 5},
            "K": 4
        },
        {
            "name": "W.Backup",
            "class": WaterfallMoulinetteFiniteBackup,
            "config": {"K": 4, "process_time": 2, "result_time": 1, "ks": 20, "kf": 5, "tag_limit": 5, "nb_exos": 5},
            "K": 4
        },
        {
            "name": "Ch.Regulated",
            "class": ChannelsAndDams,
            "config": {"K": 3, "process_time": 2, "result_time": 1, "ks": 15, "kf": 8, "tb": 10, "block_option": True, "tag_limit": 5, "nb_exos": 5},
            "K": 3
        },
        {
            "name": "Ch.NoRegul",
            "class": ChannelsAndDams,
            "config": {"K": 3, "process_time": 2, "result_time": 1, "ks": 15, "kf": 8, "tb": 10, "block_option": False, "tag_limit": 5, "nb_exos": 5},
            "K": 3
        }
    ]
    
    cost_results = []
    labels = []
    
    for arch in architectures:
        moulinette = run_architecture_test(arch["class"], arch["config"], num_users)
        metrics = extract_metrics_from_moulinette(moulinette)
        
        total_requests = moulinette.metrics.total_requests
        
        cost_result = analyzer.calculate_total_cost(
            num_test_servers=arch["K"],
            metrics=metrics,
            total_requests=total_requests,
            backup_enabled=isinstance(moulinette, WaterfallMoulinetteFiniteBackup)
        )
        
        cost_results.append(cost_result)
        labels.append(arch["name"])
    
    plot_cost_comparison(cost_results, labels, 
                        save_filename=f"{results_dir}/architecture_comparison.png")
    
    best_idx = np.argmin([c['cost_per_successful_request'] for c in cost_results])
    print(f"Optimal: {labels[best_idx]} (Cost: {cost_results[best_idx]['total_cost']:.2f}€, Success: {cost_results[best_idx]['success_rate']*100:.1f}%)")
    
    with open(f"{results_dir}/results.txt", "w") as f:
        f.write("=== Architecture Cost Comparison ===\n\n")
        for i, arch in enumerate(architectures):
            f.write(f"{labels[i]}:\n")
            f.write(f"  K servers: {arch['K']}\n")
            f.write(f"  Total cost: {cost_results[i]['total_cost']:.2f}€\n")
            f.write(f"  Success rate: {cost_results[i]['success_rate']*100:.1f}%\n")
            f.write(f"  Cost per success: {cost_results[i]['cost_per_successful_request']:.4f}€\n")
            f.write(f"  Infrastructure: {cost_results[i]['total_infrastructure']:.2f}€\n")
            f.write(f"  Quality cost: {cost_results[i]['total_quality_cost']:.2f}€\n")
            f.write(f"  Operational: {cost_results[i]['total_operational']:.2f}€\n")
            f.write("\n")
        
        f.write(f"\nOptimal: {labels[best_idx]}\n")


if __name__ == "__main__":
    compare_all_architectures()