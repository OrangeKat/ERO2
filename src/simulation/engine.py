import simpy
import random
import numpy as np

class MoulinetteSimulation:
    def __init__(self, env, num_exec_servers, exec_time_dist, front_time_dist, ks=float('inf'), kf=float('inf'), backup_prob=0.0):
        self.env = env
        self.num_exec_servers = num_exec_servers
        self.exec_time_dist = exec_time_dist # function that returns a duration
        self.front_time_dist = front_time_dist # function that returns a duration
        
        self.exec_queue = simpy.Resource(env, capacity=num_exec_servers)
        self.front_queue = simpy.Resource(env, capacity=1)
        
        self.ks = ks
        self.kf = kf
        self.backup_prob = backup_prob
        
        # Metrics
        self.total_requests = 0
        self.exec_rejected = 0
        self.front_rejected = 0
        self.stay_times = []
        self.results_captured = 0 # for backup
        self.empty_returns = 0

    def student_request(self, student_id):
        self.total_requests += 1
        arrival_time = self.env.now
        
        # Execution Queue Check
        if len(self.exec_queue.queue) >= self.ks:
            self.exec_rejected += 1
            return
        
        with self.exec_queue.request() as request:
            yield request
            
            # Processing time
            duration = self.exec_time_dist()
            yield self.env.timeout(duration)
            
        # Move to Front Queue
        # Note: In the problem, it says if front queue is full, student receives empty return.
        # But wait, is there a backup?
        
        # Backup logic
        is_backed_up = random.random() < self.backup_prob
        if is_backed_up:
            self.results_captured += 1

        if len(self.front_queue.queue) >= self.kf:
            if not is_backed_up:
                self.empty_returns += 1
                return # Result lost, empty return
            else:
                # If backed up, maybe it waits? Or maybe it's just saved but the front-end still sees empty if queue full.
                # "Si le résultat d'un moulinettage est refusé dans la seconde file, l'étudiant reçoit un retour vide."
                # The backup is "en amont de l'envoi".
                self.empty_returns += 1
                # The backup saves the data, but the immediate response is still "empty" if the queue is full?
                # Actually, the question "Quel changement cela opère-t-il sur la proportion de pages blanches ?"
                # suggests that backup might allow recovering the result later or preventing the "empty return" 
                # if the user can fetch it from backup. 
                # But usually, a backup is for persistence. 
                # If the front queue is full, the transmission worker (the single server) can't take it.
                pass

        with self.front_queue.request() as request:
            yield request
            duration = self.front_time_dist()
            yield self.env.timeout(duration)
            
        self.stay_times.append(self.env.now - arrival_time)

def run_waterfall_sim(env, arrival_rate, num_exec, exec_rate, front_rate, ks=float('inf'), kf=float('inf'), backup_prob=0.0, duration=1000):
    sim = MoulinetteSimulation(env, num_exec, 
                               lambda: random.expovariate(exec_rate), 
                               lambda: random.expovariate(front_rate),
                               ks=ks, kf=kf, backup_prob=backup_prob)
    
    def generator(env):
        student_id = 0
        while True:
            yield env.timeout(random.expovariate(arrival_rate))
            env.process(sim.student_request(student_id))
            student_id += 1
            
    env.process(generator(env))
    env.run(until=duration)
    return sim
