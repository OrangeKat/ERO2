import random
import sys
import os
import numpy as np
from typing import List, Callable

from src.models.basics import Utilisateur
from src.simulation.waterfall.infinite import WaterfallMoulinetteInfinite
from src.simulation.waterfall.finite import WaterfallMoulinetteFinite
from src.simulation.waterfall.backup import WaterfallMoulinetteFiniteBackup
from src.simulation.channels_dams.channelsdams import ChannelsAndDams
from src.simulation.priority import run_priority_sim # My addition
from src.scenarios.scenario5_comparison import compare_theory_sim # My addition

def generate_users_names(n: int):
    return ["USER" + str(i) for i in range(n)]

def create_user_list(names: List[str], promo_ratio=0.5) -> List[Utilisateur]:
    users = []
    for name in names:
        promo = "ING" if random.random() < promo_ratio else "PREPA"
        users.append(Utilisateur(name=name, promo=promo))
    return users

def launch_test(moulinette, user_list, until=None, save_filename="metrics.png"):
    for user in user_list:
        moulinette.add_user(user)

    if isinstance(moulinette, ChannelsAndDams):
        moulinette.env.process(moulinette.regulate_ing())

    if isinstance(moulinette, WaterfallMoulinetteFiniteBackup) or isinstance(moulinette, ChannelsAndDams):
        moulinette.env.process(moulinette.free_backup())

    moulinette.start_simulation(until=until, save_filename=save_filename)

def exec_simulations(nb_user: int, module: Callable, configs: dict, promo_ratio: float = 0.7):
    for key in configs.keys():
        user_list = create_user_list(generate_users_names(nb_user), promo_ratio)
        m_config = module(**configs[key])
        
        base_path = f"output/{m_config.__class__.__name__}"
        os.makedirs(f"{base_path}/files", exist_ok=True)
        os.makedirs(f"{base_path}/graphs", exist_ok=True)

        log_file = f"{base_path}/files/U{len(user_list)}_{key}.txt"
        graph_file = f"{base_path}/graphs/U{len(user_list)}_{key}.png"
        
        print(f"Running {m_config.__class__.__name__} - {key} ({nb_user} users)...")
        
        old_stdout = sys.stdout
        with open(log_file, "w") as f:
            sys.stdout = f
            launch_test(m_config, user_list, until=None, save_filename=graph_file)
        sys.stdout = old_stdout

if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)

    user_loads = {"normal": 30, "high": 60} # Reduced for speed in this demo environment

    config_infinite = {
        "base": {"K": 3, "process_time": 2, "result_time": 1, "tag_limit": 5, "nb_exos": 5},
    }

    config_finite = {
        "standard": {"K": 4, "process_time": 2, "result_time": 1, "ks": 20, "kf": 10, "nb_exos": 5},
    }

    config_backup = {
        "with_backup": {"K": 4, "process_time": 2, "result_time": 1, "ks": 20, "kf": 5, "nb_exos": 5},
    }

    config_channels = {
        "regulated": {"K": 3, "process_time": 2, "result_time": 1, "ks": 15, "kf": 8, "tb": 10, "block_option": True, "nb_exos": 5},
        "not_regulated": {"K": 3, "process_time": 2, "result_time": 1, "ks": 15, "kf": 8, "tb": 10, "block_option": False, "nb_exos": 5},
    }

    print("=== Starting Improved Moulinette Simulations ===")
    
    print("\n[Case 1: Waterfall Infinite]")
    exec_simulations(user_loads["normal"], WaterfallMoulinetteInfinite, config_infinite)

    print("\n[Case 2: Waterfall Finite]")
    exec_simulations(user_loads["normal"], WaterfallMoulinetteFinite, config_finite)

    print("\n[Case 3: Waterfall Finite with Backup]")
    exec_simulations(user_loads["normal"], WaterfallMoulinetteFiniteBackup, config_backup)

    print("\n[Case 4: Channels and Dams]")
    exec_simulations(user_loads["normal"], ChannelsAndDams, config_channels)

    print("\n[Case 5: Theoretical Comparison]")
    from src.scenarios.scenario5_comparison import compare_theory_sim
    compare_theory_sim()

    print("\n[Case 6: Comparison Plots]")
    from src.scenarios.scenario6_theory_plots import generate_comparison_plots
    generate_comparison_plots()

    print("\n[Case 7: Cost Analysis - Scaling]")
    from src.scenarios.scenario_cost import analyze_server_costs
    analyze_server_costs()

    print("\n[Case 8: Cost Analysis - All Architectures]")
    from src.scenarios.scenario_all_architectures import compare_all_architectures
    compare_all_architectures()

    print("\nSimulation complete. Outputs are in 'output/' directory.")