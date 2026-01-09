import simpy
import random
import numpy as np
import matplotlib.pyplot as plt
import os
from src.models.queuing_theory import mm1_theory, mmk_theory, mmk_finite_theory

def run_mmk_sim(env, arrival_rate, num_servers, service_rate, duration=5000):
    metrics = {"stay_times": [], "wait_times": []}
    resource = simpy.Resource(env, capacity=num_servers)
    
    def request(env):
        arrival_time = env.now
        with resource.request() as req:
            yield req
            metrics["wait_times"].append(env.now - arrival_time)
            
            yield env.timeout(random.expovariate(service_rate))
            
        metrics["stay_times"].append(env.now - arrival_time)

    def generator(env):
        while True:
            yield env.timeout(random.expovariate(arrival_rate))
            env.process(request(env))
            
    env.process(generator(env))
    env.run(until=duration)
    
    avg_w = np.mean(metrics["stay_times"]) if metrics["stay_times"] else 0
    avg_wq = np.mean(metrics["wait_times"]) if metrics["wait_times"] else 0

    avg_l = arrival_rate * avg_w
    avg_lq = arrival_rate * avg_wq
    avg_ls = avg_l - avg_lq
    
    return {"w": avg_w, "wq": avg_wq, "l": avg_l, "lq": avg_lq, "ls": avg_ls}

def run_mmk_finite_sim(env, arrival_rate, num_servers, service_rate, capacity, duration=5000):
    resource = simpy.Resource(env, capacity=num_servers)

    stats = {"arrivals": 0, "rejections": 0}
    current_in_system = [0]
    
    def request(env):
        stats["arrivals"] += 1
        
        if current_in_system[0] >= capacity:
            stats["rejections"] += 1
            return # Bye bye
            
        current_in_system[0] += 1
        
        with resource.request() as req:
            yield req
            yield env.timeout(random.expovariate(service_rate))
            
        current_in_system[0] -= 1

    def generator(env):
        while True:
            yield env.timeout(random.expovariate(arrival_rate))
            env.process(request(env))
            
    env.process(generator(env))
    env.run(until=duration)
    
    rejection_rate = stats["rejections"] / stats["arrivals"] if stats["arrivals"] > 0 else 0
    return {"p_block": rejection_rate}

def plot_dashboard(util_inf, data_inf, util_fin, data_fin, filename):
    fig, axs = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('M/M/4 Comparison Dashboard (Theory vs Simulation)', fontsize=16)
    
    def plot_ax(ax, x, y_th, y_sim, ylabel, title, color_th='blue', color_sim='red'):
        ax.plot(x, y_th, label='Theory', color=color_th, linestyle='--')
        ax.plot(x, y_sim, label='Simulation', color=color_sim, marker='o', markersize=4)
        ax.set_title(title)
        ax.set_xlabel('Utilization (rho)')
        ax.set_ylabel(ylabel)
        ax.legend()
        ax.grid(True)

    # 1. Stay Time (W)
    plot_ax(axs[0, 0], util_inf, data_inf["theory"]["w"], data_inf["sim"]["w"], "Time (W)", "Avg Stay Time (W)")
    
    # 2. Wait Time (Wq)
    plot_ax(axs[0, 1], util_inf, data_inf["theory"]["wq"], data_inf["sim"]["wq"], "Time (Wq)", "Avg Wait Time (Wq)")
    
    # 3. Number Processing (Ls)
    plot_ax(axs[0, 2], util_inf, data_inf["theory"]["ls"], data_inf["sim"]["ls"], "Users (Ls)", "Users Processing (Ls)")
    
    # 4. Number in System (L)
    plot_ax(axs[1, 0], util_inf, data_inf["theory"]["l"], data_inf["sim"]["l"], "Users (L)", "Users in System (L)")
    
    # 5. Number in Queue (Lq)
    plot_ax(axs[1, 1], util_inf, data_inf["theory"]["lq"], data_inf["sim"]["lq"], "Users (Lq)", "Users in Queue (Lq)")
    
    # 6. Rejection Rate
    plot_ax(axs[1, 2], util_fin, data_fin["theory"], data_fin["sim"], "Probability", "Rejection Rate (Finite Capacity)", 'green', 'orange')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(filename)
    plt.close()

def generate_comparison_plots():
    results_dir = "output/comparisons"
    os.makedirs(results_dir, exist_ok=True)
    
    print("Generating Theory vs Simulation Plots...")
    
    duration = 20000 
    utilizations = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    # --- Part 1: M/M/4 Infinite Capacity Metrics ---
    print("\n[M/M/4 Detailed Comparison]")
    k = 4
    mu_test = 0.5
    lam_list = [rho * k * mu_test for rho in utilizations]
    
    data_inf = {
        "theory": {"w": [], "wq": [], "l": [], "lq": [], "ls": []},
        "sim": {"w": [], "wq": [], "l": [], "lq": [], "ls": []}
    }
    
    for lam in lam_list:
        t = mmk_theory(lam, mu_test, k)
        for key in data_inf["theory"]: data_inf["theory"][key].append(t[key])
        
        env = simpy.Environment()
        s = run_mmk_sim(env, lam, k, mu_test, duration)
        for key in data_inf["sim"]: data_inf["sim"][key].append(s[key])
        
    # --- Part 2: M/M/4/10 Finite Capacity Rejection ---
    print("\n[M/M/4/10 Rejection Rate Comparison]")
    capacity = 10
    utilizations_finite = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0]
    lam_list_finite = [rho * k * mu_test for rho in utilizations_finite]
    
    data_rej = {"theory": [], "sim": []}
    
    for lam in lam_list_finite:
        t = mmk_finite_theory(lam, mu_test, k, capacity)
        data_rej["theory"].append(t["p_block"])
        
        env = simpy.Environment()
        s = run_mmk_finite_sim(env, lam, k, mu_test, capacity, duration)
        data_rej["sim"].append(s["p_block"])
        
    plot_dashboard(utilizations, data_inf, utilizations_finite, data_rej, f"{results_dir}/dashboard_mm4.png")

if __name__ == "__main__":
    generate_comparison_plots()
