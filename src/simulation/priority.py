import simpy
import random
import numpy as np

class PrioritySimulation:
    def __init__(self, env, num_exec_servers):
        self.env = env
        # Using PriorityResource: lower priority value = higher priority
        self.exec_queue = simpy.PriorityResource(env, capacity=num_exec_servers)
        
        self.stats = {
            'ING': {'arrivals': 0, 'stay_times': [], 'priority': 2},
            'PREPA': {'arrivals': 0, 'stay_times': [], 'priority': 1} # Higher priority
        }
        self.total_requests = 0

    def request(self, pop_type, exec_time_dist):
        self.total_requests += 1
        self.stats[pop_type]['arrivals'] += 1
        arrival_time = self.env.now
        
        priority = self.stats[pop_type]['priority']
        
        with self.exec_queue.request(priority=priority) as req:
            yield req
            yield self.env.timeout(exec_time_dist())
            
        self.stats[pop_type]['stay_times'].append(self.env.now - arrival_time)

def run_priority_sim(env, ing_arrival_rate, prepa_arrival_rate, 
                      ing_exec_rate, prepa_exec_rate, 
                      num_exec=1, duration=1000):
    
    sim = PrioritySimulation(env, num_exec)
    
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
    
    env.run(until=duration)
    return sim
