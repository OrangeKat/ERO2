import math
import scipy.stats

def mm1_theory(lam, mu):
    if lam >= mu:
        return {"w": float('inf'), "wq": float('inf'), "l": float('inf'), "lq": float('inf'), "ls": float('inf')}
    
    rho = lam / mu
    w = 1 / (mu - lam)
    wq = w - (1/mu)
    l = lam * w
    lq = lam * wq
    ls = l - lq # Or simpy rho, since k=1
    
    return {"w": w, "wq": wq, "l": l, "lq": lq, "ls": ls}

def mmk_theory(lam, mu, k):
    rho = lam / (k * mu)
    if rho >= 1:
        return {"w": float('inf'), "wq": float('inf'), "l": float('inf'), "lq": float('inf'), "ls": float('inf')}
    
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
    
    l = lam * w
    lq = lam * wq
    ls = l - lq # Expected number of busy servers
    
    return {"w": w, "wq": wq, "l": l, "lq": lq, "ls": ls}

def mg1_theory(lam, mu, var_s):
    rho = lam / mu
    if rho >= 1:
        return {"w": float('inf'), "wq": float('inf'), "l": float('inf'), "lq": float('inf'), "ls": float('inf')}
    
    # Pollaczek-Khinchine formula for mean wait in system
    es = 1 / mu
    es2 = var_s + es**2
    wq = (lam * es2) / (2 * (1 - rho))
    w = wq + es
    
    l = lam * w
    lq = lam * wq
    ls = l - lq
    
    return {"w": w, "wq": wq, "l": l, "lq": lq, "ls": ls}

def mmk_finite_theory(lam, mu, k, capacity):
    """
    M/M/k/K queue (Finite System Capacity K).
    Returns blocking probability (P_K).
    """
    rho = lam / mu # Traffic intensity
    r = lam / mu # Same as rho for formulas usually, keep distinct if needed
    
    # Calculate P0
    # Sum part for n < k
    sum_n_lt_k = sum([(r**n) / math.factorial(n) for n in range(k)])
    
    # Sum part for k <= n <= capacity
    sum_n_ge_k = sum([(r**n) / (math.factorial(k) * k**(n-k)) for n in range(k, capacity + 1)])
    
    p0 = 1.0 / (sum_n_lt_k + sum_n_ge_k)
    
    # Calculate P_K (Probability that system is full -> Blocking Probability)
    # P_n = (r^n / (k! * k^(n-k))) * P0   for k <= n <= K
    n = capacity
    p_k = ((r**n) / (math.factorial(k) * k**(n-k))) * p0
    
    return {"p_block": p_k}
