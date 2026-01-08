import simpy
import random
import numpy as np

class MultiPopulationSimulation:
    def __init__(self, env, num_exec_servers, exec_queue_size=float('inf')):
        self.env = env
        self.exec_queue = simpy.Resource(env, capacity=num_exec_servers)
        self.exec_queue_size = exec_queue_size
        
        self.stats = {
            'ING': {'arrivals': 0, 'stay_times': [], 'rejected': 0},
            'PREPA': {'arrivals': 0, 'stay_times': [], 'rejected': 0}
        }
        self.total_requests = 0
        self.ing_blocked = False

    def request(self, pop_type, exec_time_dist):
        self.total_requests += 1
        self.stats[pop_type]['arrivals'] += 1
        if pop_type == 'ING' and self.ing_blocked:
            self.stats['ING']['rejected'] += 1
            return
        arrival_time = self.env.now
        
        if len(self.exec_queue.queue) >= self.exec_queue_size:
            self.stats[pop_type]['rejected'] += 1
            return

        with self.exec_queue.request() as req:
            yield req
            yield self.env.timeout(exec_time_dist())
            
        self.stats[pop_type]['stay_times'].append(self.env.now - arrival_time)

    def dam_controller(self, initial_tb):
        tb = initial_tb
        while True:
            # Block ING
            self.ing_blocked = True
            yield self.env.timeout(tb)
            
            # Open ING
            self.ing_blocked = False
            yield self.env.timeout(tb / 2)
            
            # The prompt says "puis ouvert pour tb/2, etc." 
            # It might mean a sequence or just a cycle. 
            # I'll stick to a cycle for now or a decreasing sequence if "etc" implies it.
            # Usually "etc" in this context might mean tb/4? Or just repeating.
            # Let's assume a cycle of (tb block, tb/2 open).

def run_population_sim(env, ing_arrival_rate, prepa_arrival_rate, 
                       ing_exec_rate, prepa_exec_rate, 
                       num_exec=1, initial_tb=None, duration=1000):
    
    sim = MultiPopulationSimulation(env, num_exec)
    
    def ing_generator(env):
        while True:
            yield env.timeout(random.expovariate(ing_arrival_rate))
            env.process(sim.request('ING', lambda: random.expovariate(ing_exec_rate)))

    def prepa_generator(env):
        while True:
            yield env.timeout(random.expovariate(prepa_arrival_rate))
            env.process(sim.request('PREPA', lambda: random.expovariate(prepa_exec_rate)))

    env.process(ing_generator(env))
    env.process(prepa_generator(env))
    
    if initial_tb is not None:
        env.process(sim.dam_controller(initial_tb))
        
    env.run(until=duration)
    return sim
