import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict


def plot_cost_comparison(configurations: List[Dict], labels: List[str], save_filename: str = None):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    ax1 = axes[0, 0]
    total_costs = [config['total_cost'] for config in configurations]
    bars = ax1.bar(labels, total_costs, color='#3498db', alpha=0.7)
    ax1.set_ylabel('Coût total (€)')
    ax1.set_title('Coût total par configuration')
    ax1.grid(axis='y', alpha=0.3)
    
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{total_costs[i]:.2f}€', ha='center', va='bottom')
    
    ax2 = axes[0, 1]
    cost_per_request = [config['cost_per_request'] for config in configurations]
    cost_per_success = [config['cost_per_successful_request'] for config in configurations]
    
    x = np.arange(len(labels))
    width = 0.35
    
    ax2.bar(x - width/2, cost_per_request, width, label='Par requête', color='#2ecc71')
    ax2.bar(x + width/2, cost_per_success, width, label='Par succès', color='#e74c3c')
    
    ax2.set_ylabel('Coût (€)')
    ax2.set_title('Coût unitaire par configuration')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    ax3 = axes[1, 0]
    infrastructure = [config['total_infrastructure'] for config in configurations]
    quality = [config['total_quality_cost'] for config in configurations]
    operational = [config['total_operational'] for config in configurations]
    
    x = np.arange(len(labels))
    width = 0.6
    
    p1 = ax3.bar(x, infrastructure, width, label='Infrastructure', color='#3498db')
    p2 = ax3.bar(x, quality, width, bottom=infrastructure, label='Qualité', color='#e74c3c')
    p3 = ax3.bar(x, operational, width, 
                 bottom=np.array(infrastructure) + np.array(quality),
                 label='Opérationnel', color='#2ecc71')
    
    ax3.set_ylabel('Coût (€)')
    ax3.set_title('Répartition des coûts par type')
    ax3.set_xticks(x)
    ax3.set_xticklabels(labels)
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    
    ax4 = axes[1, 1]
    success_rates = [config['success_rate'] * 100 for config in configurations]
    bars = ax4.bar(labels, success_rates, color='#9b59b6', alpha=0.7)
    ax4.set_ylabel('Taux de succès (%)')
    ax4.set_title('Taux de succès par configuration')
    ax4.set_ylim([0, 105])
    ax4.grid(axis='y', alpha=0.3)
    ax4.axhline(y=95, color='g', linestyle='--', label='Objectif 95%')
    ax4.legend()
    
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{success_rates[i]:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    
    if save_filename:
        plt.savefig(save_filename, dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
    plt.close()


def plot_scaling_analysis(server_counts: List[int], cost_results: List[Dict], save_filename: str = None):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    ax1 = axes[0, 0]
    total_costs = [result['total_cost'] for result in cost_results]
    infrastructure_costs = [result['total_infrastructure'] for result in cost_results]
    quality_costs = [result['total_quality_cost'] for result in cost_results]
    
    ax1.plot(server_counts, total_costs, 'o-', label='Coût total', linewidth=2, markersize=8)
    ax1.plot(server_counts, infrastructure_costs, 's--', label='Infrastructure', alpha=0.7)
    ax1.plot(server_counts, quality_costs, '^--', label='Qualité', alpha=0.7)
    ax1.set_xlabel('Nombre de serveurs de test (K)')
    ax1.set_ylabel('Coût (€)')
    ax1.set_title('Évolution des coûts selon le nombre de serveurs')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2 = axes[0, 1]
    cost_per_request = [result['cost_per_request'] for result in cost_results]
    cost_per_success = [result['cost_per_successful_request'] for result in cost_results]
    
    ax2.plot(server_counts, cost_per_request, 'o-', label='Par requête', linewidth=2, markersize=8)
    ax2.plot(server_counts, cost_per_success, 's-', label='Par succès', linewidth=2, markersize=8, alpha=0.7)
    ax2.set_xlabel('Nombre de serveurs de test (K)')
    ax2.set_ylabel('Coût unitaire (€)')
    ax2.set_title('Coût unitaire selon le nombre de serveurs')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    ax3 = axes[1, 0]
    success_rates = [result['success_rate'] * 100 for result in cost_results]
    
    ax3.plot(server_counts, success_rates, 'o-', linewidth=2, markersize=8, color='#2ecc71')
    ax3.set_xlabel('Nombre de serveurs de test (K)')
    ax3.set_ylabel('Taux de succès (%)')
    ax3.set_title('Taux de succès selon le nombre de serveurs')
    ax3.axhline(y=95, color='r', linestyle='--', label='Objectif 95%', alpha=0.5)
    ax3.axhline(y=99, color='g', linestyle='--', label='Objectif 99%', alpha=0.5)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim([min(success_rates) - 5, 100])
    
    ax4 = axes[1, 1]
    efficiency = [result['successful_requests'] / result['total_cost'] 
                  if result['total_cost'] > 0 else 0 
                  for result in cost_results]
    
    ax4.plot(server_counts, efficiency, 'o-', linewidth=2, markersize=8, color='#9b59b6')
    ax4.set_xlabel('Nombre de serveurs de test (K)')
    ax4.set_ylabel('Requêtes réussies par euro')
    ax4.set_title('Efficacité économique (succès/€)')
    ax4.grid(True, alpha=0.3)
    
    optimal_idx = np.argmax(efficiency)
    ax4.plot(server_counts[optimal_idx], efficiency[optimal_idx], 'r*', 
             markersize=20, label=f'Optimum: K={server_counts[optimal_idx]}')
    ax4.legend()
    
    plt.tight_layout()
    
    if save_filename:
        plt.savefig(save_filename, dpi=300, bbox_inches='tight')
    else:
        plt.show()
    
    plt.close()