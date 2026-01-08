import math
import scipy.stats

def mm1_theory(lam, mu):
    if lam >= mu:
        return float('inf'), float('inf')
    rho = lam / mu
    w = 1 / (mu - lam)
    # Variance of stay time in M/M/1 is 1/(mu-lam)^2
    var_w = 1 / ((mu - lam) ** 2)
    return w, var_w

def mmk_theory(lam, mu, k):
    rho = lam / (k * mu)
    if rho >= 1:
        return float('inf'), float('inf')
    
    # Probability P0
    sum_part = sum([(k * rho)**n / math.factorial(n) for n in range(k)])
    last_part = (k * rho)**k / (math.factorial(k) * (1 - rho))
    p0 = 1 / (sum_part + last_part)
    
    # Probability of queuing (Erlang-C)
    pq = last_part * p0
    
    # Wait in queue
    wq = pq / (k * mu - lam)
    # Total stay time
    w = wq + (1 / mu)
    
    # Variance of stay time in M/M/k is more complex, but can be approximated/calculated.
    # For now, let's focus on the Mean.
    return w, None

def mg1_theory(lam, mu, var_s):
    rho = lam / mu
    if rho >= 1:
        return float('inf'), float('inf')
    
    # Pollaczek-Khinchine formula for mean wait in system
    es = 1 / mu
    es2 = var_s + es**2
    wq = (lam * es2) / (2 * (1 - rho))
    w = wq + es
    return w, None
