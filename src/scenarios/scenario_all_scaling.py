import os
import sys
import numpy as np
import random
from src.simulation.waterfall.infinite import WaterfallMoulinetteInfinite
from src.simulation.waterfall.finite import WaterfallMoulinetteFinite
from src.simulation.waterfall.backup import WaterfallMoulinetteFiniteBackup
from src.simulation.channels_dams.channelsdams import ChannelsAndDams
from src.models.basics import Utilisateur
from src.utils.cost_analysis import CostAnalyzer, create_cost_config_aws_small
from src.visualization.cost_plots import plot_scaling_analysis
import matplotlib.pyplot as plt


def create_users(n, promo_ratio=0.7):
    users = []
    for i in range(n):
        promo = "ING" if random.random() < promo_ratio else "PREPA"
        users.append(Utilisateur(name=f"USER{i}", promo=promo))
    return users


def run_test(architecture_class, config, num_users=30):
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


def analyze_architecture_scaling(arch_name, arch_class, base_config, k_values, analyzer, num_users=30):
    cost_results = []
    
    for k in k_values:
        config = base_config.copy()
        config["K"] = k
        
        moulinette = run_test(arch_class, config, num_users)
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
            num_test_servers=k,
            metrics=metrics,
            total_requests=moulinette.metrics.total_requests,
            backup_enabled=isinstance(moulinette, WaterfallMoulinetteFiniteBackup)
        )
        
        cost_results.append(cost_result)
    
    return cost_results


def analyze_all_architectures_scaling():
    results_dir = "output/cost_analysis_scaling"
    os.makedirs(results_dir, exist_ok=True)
    
    random.seed(42)
    np.random.seed(42)
    
    cost_config = create_cost_config_aws_small()
    cost_config.simulation_duration_hours = 1.0
    analyzer = CostAnalyzer(cost_config)
    
    k_values = [1, 2, 4, 6, 8, 10]
    num_users = 30
    
    architectures = [
        {
            "name": "W.Infinite",
            "class": WaterfallMoulinetteInfinite,
            "config": {"process_time": 2, "result_time": 1, "tag_limit": 5, "nb_exos": 5}
        },
        {
            "name": "W.Finite",
            "class": WaterfallMoulinetteFinite,
            "config": {"process_time": 2, "result_time": 1, "ks": 20, "kf": 10, "tag_limit": 5, "nb_exos": 5}
        },
        {
            "name": "W.Backup",
            "class": WaterfallMoulinetteFiniteBackup,
            "config": {"process_time": 2, "result_time": 1, "ks": 20, "kf": 5, "tag_limit": 5, "nb_exos": 5}
        },
        {
            "name": "Ch.Regulated",
            "class": ChannelsAndDams,
            "config": {"process_time": 2, "result_time": 1, "ks": 15, "kf": 8, "tb": 10, "block_option": True, "tag_limit": 5, "nb_exos": 5}
        },
        {
            "name": "Ch.NoRegul",
            "class": ChannelsAndDams,
            "config": {"process_time": 2, "result_time": 1, "ks": 15, "kf": 8, "tb": 10, "block_option": False, "tag_limit": 5, "nb_exos": 5}
        }
    ]
    
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    
    all_results = {}
    
    try:
        for arch in architectures:
            cost_results = analyze_architecture_scaling(
                arch["name"],
                arch["class"],
                arch["config"],
                k_values,
                analyzer,
                num_users
            )
            all_results[arch["name"]] = cost_results
    finally:
        sys.stdout.close()
        sys.stdout = old_stdout
    
    for arch_name, cost_results in all_results.items():
        plot_scaling_analysis(
            k_values,
            cost_results,
            save_filename=f"{results_dir}/scaling_{arch_name.replace('.', '_')}.png"
        )
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    ax1 = axes[0, 0]
    for arch_name, cost_results in all_results.items():
        total_costs = [r['total_cost'] for r in cost_results]
        ax1.plot(k_values, total_costs, 'o-', label=arch_name, linewidth=2, markersize=6)
    ax1.set_xlabel('Nombre de serveurs de test (K)')
    ax1.set_ylabel('Coût total (€)')
    ax1.set_title('Coût total selon K - Toutes architectures')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2 = axes[0, 1]
    for arch_name, cost_results in all_results.items():
        success_rates = [r['success_rate'] * 100 for r in cost_results]
        ax2.plot(k_values, success_rates, 'o-', label=arch_name, linewidth=2, markersize=6)
    ax2.set_xlabel('Nombre de serveurs de test (K)')
    ax2.set_ylabel('Taux de succès (%)')
    ax2.set_title('Taux de succès selon K')
    ax2.axhline(y=95, color='r', linestyle='--', alpha=0.3)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    ax3 = axes[1, 0]
    for arch_name, cost_results in all_results.items():
        cost_per_success = [r['cost_per_successful_request'] for r in cost_results]
        ax3.plot(k_values, cost_per_success, 'o-', label=arch_name, linewidth=2, markersize=6)
    ax3.set_xlabel('Nombre de serveurs de test (K)')
    ax3.set_ylabel('Coût par succès (€)')
    ax3.set_title('Coût par requête réussie selon K')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    ax4 = axes[1, 1]
    for arch_name, cost_results in all_results.items():
        efficiency = [r['successful_requests'] / r['total_cost'] if r['total_cost'] > 0 else 0 
                     for r in cost_results]
        ax4.plot(k_values, efficiency, 'o-', label=arch_name, linewidth=2, markersize=6)
    ax4.set_xlabel('Nombre de serveurs de test (K)')
    ax4.set_ylabel('Requêtes réussies par euro')
    ax4.set_title('Efficacité économique selon K')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{results_dir}/comparison_all_architectures.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    with open(f"{results_dir}/results.txt", "w") as f:
        f.write("=== Scaling Analysis - All Architectures ===\n\n")
        
        for arch_name, cost_results in all_results.items():
            f.write(f"{arch_name}:\n")
            for i, k in enumerate(k_values):
                f.write(f"  K={k}: Cost={cost_results[i]['total_cost']:.2f}€, "
                       f"Success={cost_results[i]['success_rate']*100:.1f}%, "
                       f"Cost/success={cost_results[i]['cost_per_successful_request']:.4f}€\n")
            
            best_idx = np.argmin([c['cost_per_successful_request'] for c in cost_results])
            f.write(f"  Optimal K: {k_values[best_idx]}\n\n")
    
    for arch_name, cost_results in all_results.items():
        best_idx = np.argmin([c['cost_per_successful_request'] for c in cost_results])
        print(f"{arch_name} optimal K: {k_values[best_idx]}")


if __name__ == "__main__":
    analyze_all_architectures_scaling()