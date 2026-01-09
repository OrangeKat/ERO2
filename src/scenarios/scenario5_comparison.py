import simpy
import random
import numpy as np
import os
# from src.simulation.engine import run_waterfall_sim
from src.models.queuing_theory import mm1_theory, mmk_theory, mg1_theory
from src.utils.metrics import calculate_empirical_stats

def run_generic_sim(env, arrival_rate, num_servers, service_dist, duration=5000):
    stay_times = []
    resource = simpy.Resource(env, capacity=num_servers)
    
    def request(env):
        arrival_time = env.now
        with resource.request() as req:
            yield req
            yield env.timeout(service_dist())
        stay_times.append(env.now - arrival_time)

    def generator(env):
        while True:
            yield env.timeout(random.expovariate(arrival_rate))
            env.process(request(env))
            
    env.process(generator(env))
    env.run(until=duration)
    return stay_times

def compare_theory_sim():
    print("\n--- Theoretical vs Simulation Comparison ---")
    
    lam = 0.8
    mu = 1.0
    duration = 30000

    # 1. M/M/1
    print("\n[M/M/1 Case]")
    env = simpy.Environment()
    sim_mm1 = run_generic_sim(env, lam, 1, lambda: random.expovariate(mu), duration)
    mean_sim, _ = calculate_empirical_stats(sim_mm1)
    mean_theory = mm1_theory(lam, mu)["w"]
    print(f"  Simulation Mean: {mean_sim:.4f}")
    print(f"  Theoretical Mean: {mean_theory:.4f}")
    print(f"  Error: {abs(mean_sim - mean_theory)/mean_theory:.2%}")

    # 2. M/M/k (k=3)
    k = 3
    lam_k = 2.0
    print(f"\n[M/M/{k} Case]")
    env = simpy.Environment()
    sim_mmk = run_generic_sim(env, lam_k, k, lambda: random.expovariate(mu), duration)
    mean_sim, _ = calculate_empirical_stats(sim_mmk)
    mean_theory = mmk_theory(lam_k, mu, k)["w"]
    print(f"  Simulation Mean: {mean_sim:.4f}")
    print(f"  Theoretical Mean: {mean_theory:.4f}")
    print(f"  Error: {abs(mean_sim - mean_theory)/mean_theory:.2%}")

    # 3. M/G/1 (Constant service time - variance = 0)
    print("\n[M/G/1 Case] (Constant Service)")
    env = simpy.Environment()
    sim_mg1 = run_generic_sim(env, lam, 1, lambda: 1.0/mu, duration)
    mean_sim, _ = calculate_empirical_stats(sim_mg1)
    # For Constant service, var = 0
    mean_theory = mg1_theory(lam, mu, 0)["w"]
    print(f"  Simulation Mean: {mean_sim:.4f}")
    print(f"  Theoretical Mean: {mean_theory:.4f}")
    print(f"  Error: {abs(mean_sim - mean_theory)/mean_theory:.2%}")

if __name__ == "__main__":
    compare_theory_sim()
