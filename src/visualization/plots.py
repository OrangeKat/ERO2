import matplotlib.pyplot as plt

def plot_stay_times(stay_times_dict, title, filename):
    plt.figure(figsize=(10, 6))
    for label, times in stay_times_dict.items():
        plt.hist(times, bins=30, alpha=0.5, label=label)
    plt.title(title)
    plt.xlabel('Stay Time')
    plt.ylabel('Frequency')
    plt.legend()
    plt.savefig(filename)
    plt.close()

def plot_rejection_rates(ks_vals, rates, title, filename):
    plt.figure(figsize=(10, 6))
    plt.plot(ks_vals, rates, marker='o')
    plt.title(title)
    plt.xlabel('Queue Size (ks)')
    plt.ylabel('Rejection Rate')
    plt.grid(True)
    plt.savefig(filename)
    plt.close()
