import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

def calculate_empirical_stats(stay_times):
    if not stay_times:
        return 0, 0
    mean = np.mean(stay_times)
    variance = np.var(stay_times)
    return mean, variance

@dataclass
class QueueMetrics:
    """Store metrics queue system with two queues"""

    # ===== Time series data =====
    timestamps: List[float] = field(default_factory=list)

    # ===== Test queue metrics =====
    # -> number of users waiting in the test queue at each timestamp
    test_queue_lengths: List[int] = field(default_factory=list)
    # -> percentage of test servers being used at each timestamp (0.0 to 1.0)
    test_server_utilization: List[float] = field(default_factory=list)
    # -> number of users currently being processed by test servers
    test_server_count: List[int] = field(default_factory=list)
    # -> number of blocked test request by test servers at each timestamp
    test_queue_blocked_times: List[float] = field(default_factory=list)

    # ===== Result queue metrics =====
    # -> number of users waiting in the result queue at each timestamp
    result_queue_lengths: List[int] = field(default_factory=list)
    # -> percentage of result servers being used at each timestamp (0.0 to 1.0)
    result_server_utilization: List[float] = field(default_factory=list)
    # -> number of users currently being processed by result servers
    result_server_count: List[int] = field(default_factory=list)
    # -> number of blocked result request by result servers at each timestamp
    result_queue_blocked_times: List[float] = field(default_factory=list)

    # ===== System-wide metrics =====
    # -> total number of users in the entire system at each timestamp
    system_clients: List[int] = field(default_factory=list)
    # -> backup length (results accumulation)
    backup_length: List[int] = field(default_factory=list)

    # ===== Timing tracking for each queue =====
    # -> used to calculate time spent waiting for testing
    test_queue_entry_times: Dict[str, float] = field(default_factory=dict)
    # -> used with entry times to calculate test queue sojourn time
    test_queue_exit_times: Dict[str, float] = field(default_factory=dict)
    # -> used to calculate time spent waiting for results
    result_queue_entry_times: Dict[str, float] = field(default_factory=dict)
    # -> used with entry times to calculate results queue sojourn time
    result_queue_exit_times: Dict[str, float] = field(default_factory=dict)

    # ===== General =====
    test_queue_blocked: int = 0
    result_queue_blocked: int = 0
    total_requests: int = 0

    def record_state(
        self,
        env_time: float,
        test_agents: int,
        test_queue_length: int,
        backup_length: int,
        result_agents: int,
        result_queue_length: int,
        test_server_utilization: float,
        result_server_utilization: float,
    ):
        """Record system state at a given time"""
        self.timestamps.append(env_time)

        # test queue
        self.test_server_count.append(test_agents)
        self.test_queue_lengths.append(test_queue_length)
        self.test_server_utilization.append(test_server_utilization)

        # backup
        self.backup_length.append(backup_length)

        # result queue
        self.result_server_count.append(result_agents)
        self.result_queue_lengths.append(result_queue_length)
        self.result_server_utilization.append(result_server_utilization)

        # Total users in the system
        self.system_clients.append(
            test_agents + result_agents + test_queue_length + result_queue_length
        )

    # === entry / exit
    def record_test_queue_entry(self, user_id: str, time: float):
        """Record entry to test queue"""
        self.test_queue_entry_times[user_id] = time
        self.total_requests += 1

    def record_test_queue_exit(self, user_id: str, time: float):
        """Record exit from test queue"""
        self.test_queue_exit_times[user_id] = time

    def record_result_queue_entry(self, user_id: str, time: float):
        """Record entry to result queue"""
        self.result_queue_entry_times[user_id] = time

    def record_result_queue_exit(self, user_id: str, time: float):
        """Record exit from result queue"""
        self.result_queue_exit_times[user_id] = time

    # ===

    # === blocking
    def record_test_queue_blocked(self, time: float):
        """Record blocked request in test queue"""
        self.test_queue_blocked += 1
        self.test_queue_blocked_times.append(time)

    def record_result_queue_blocked(self, time: float):
        """Record blocked request in result queue"""
        self.result_queue_blocked += 1
        self.result_queue_blocked_times.append(time)

    # ===

    def calculate_metrics(self) -> dict:
        """Calculate all metrics"""
        metrics = {}

        # Test queue metrics
        metrics["test_queue"] = {
            "avg_length": np.mean(self.test_queue_lengths),
            "var_length": np.var(self.test_queue_lengths),
            "max_length": np.max(self.test_queue_lengths),
            "avg_utilization": np.mean(self.test_server_utilization),
            "var_utilization": np.var(self.test_server_utilization),
            "blocking_rate": (
                self.test_queue_blocked / self.total_requests
                if self.total_requests > 0
                else 0
            ),
        }

        # Result queue metrics
        metrics["result_queue"] = {
            "avg_length": np.mean(self.result_queue_lengths),
            "var_length": np.var(self.result_queue_lengths),
            "max_length": np.max(self.result_queue_lengths),
            "avg_utilization": np.mean(self.result_server_utilization),
            "var_utilization": np.var(self.result_server_utilization),
            "blocking_rate": (
                self.result_queue_blocked / self.total_requests
                if self.total_requests > 0
                else 0
            ),
        }

        # Calculate sojourn times for each queue
        test_sojourn_times = []
        result_sojourn_times = []
        total_sojourn_times = []

        for user_id in self.test_queue_entry_times:
            # test-queue sojourn time
            if user_id in self.test_queue_exit_times:
                test_time = (
                    self.test_queue_exit_times[user_id]
                    - self.test_queue_entry_times[user_id]
                )
                test_sojourn_times.append(test_time)

            # result-queue sojourn time
            if (
                user_id in self.result_queue_entry_times
                and user_id in self.result_queue_exit_times
            ):
                result_time = (
                    self.result_queue_exit_times[user_id]
                    - self.result_queue_entry_times[user_id]
                )
                result_sojourn_times.append(result_time)

            # total system sojourn time
            if user_id in self.result_queue_exit_times:
                total_time = (
                    self.result_queue_exit_times[user_id]
                    - self.test_queue_entry_times[user_id]
                )
                total_sojourn_times.append(total_time)

        # Add sojourn time metrics
        metrics["sojourn_times"] = {
            "test_queue": {
                "avg": np.mean(test_sojourn_times) if test_sojourn_times else 0,
                "var": np.var(test_sojourn_times) if test_sojourn_times else 0,
                "min": np.min(test_sojourn_times) if test_sojourn_times else 0,
                "max": np.max(test_sojourn_times) if test_sojourn_times else 0,
            },
            "result_queue": {
                "avg": np.mean(result_sojourn_times) if result_sojourn_times else 0,
                "var": np.var(result_sojourn_times) if result_sojourn_times else 0,
                "min": np.min(result_sojourn_times) if result_sojourn_times else 0,
                "max": np.max(result_sojourn_times) if result_sojourn_times else 0,
            },
            "total": {
                "avg": np.mean(total_sojourn_times) if total_sojourn_times else 0,
                "var": np.var(total_sojourn_times) if total_sojourn_times else 0,
                "min": np.min(total_sojourn_times) if total_sojourn_times else 0,
                "max": np.max(total_sojourn_times) if total_sojourn_times else 0,
            },
        }

        # /!\ effective throughput
        if self.timestamps:
            total_time = self.timestamps[-1] - self.timestamps[0]
            completed_requests = len(
                [
                    uid
                    for uid in self.test_queue_entry_times
                    if uid in self.result_queue_exit_times
                ]
            )
            metrics["throughput"] = (
                completed_requests / total_time if total_time > 0 else 0
            )
        else:
            metrics["throughput"] = 0

        return metrics

    def plot_metrics(self, save_filename: str = "metrics.png"):
        """Generate improved plots for all metrics with better visual separation"""
        fig = plt.figure(figsize=(20, 15))
        gs = fig.add_gridspec(6, 2, hspace=0.6, wspace=0.3)
        print(f"\n=== PLOTS: {save_filename} ===")

        color_test = "#2ecc71"
        color_result = "#e74c3c"

        # 1
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(
            self.timestamps,
            self.test_queue_lengths,
            label="Test q.",
            color=color_test,
        )
        ax1.plot(
            self.timestamps,
            self.result_queue_lengths,
            label="Result q.",
            color=color_result,
        )
        ax1.set_title("Queue lengths over time")
        ax1.set_xlabel("Time")
        ax1.set_ylabel(
            "Number of users in queue",
        )
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0)
        ax1.legend(loc="upper right")
        print("- #1 Done: Queue lengths over time")

        # 2
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.fill_between(self.timestamps, self.test_server_utilization, color=color_test)
        ax2.set_title("Test server utilization over time")
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Utilization rate")
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 1.0)
        print("- #2 Done: Test server utilization over time")

        # 3
        ax3 = fig.add_subplot(gs[1, 1])
        ax3.fill_between(self.timestamps, self.result_server_utilization, color=color_result)
        ax3.set_title("Result server utilization over time")
        ax3.set_xlabel("Time")
        ax3.set_ylabel("Utilization rate")
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(0, 1.0)
        print("- #3 Done: Result server utilization over time")

        # Sojourn times distribution
        ax4 = fig.add_subplot(gs[2, 0])
        test_sojourn_times = []
        result_sojourn_times = []
        total_sojourn_times = []
        total_prepa_sojourn_times = []
        total_ing_sojourn_times = []

        for user_id in self.test_queue_entry_times:
            if user_id in self.test_queue_exit_times:
                test_time = (
                    self.test_queue_exit_times[user_id]
                    - self.test_queue_entry_times[user_id]
                )
                test_sojourn_times.append(test_time)

            if (
                user_id in self.result_queue_entry_times
                and user_id in self.result_queue_exit_times
            ):
                result_time = (
                    self.result_queue_exit_times[user_id]
                    - self.result_queue_entry_times[user_id]
                )
                result_sojourn_times.append(result_time)

            if user_id in self.result_queue_exit_times:
                total_time = (
                    self.result_queue_exit_times[user_id]
                    - self.test_queue_entry_times[user_id]
                )

                if 'PREPA' in user_id[:5]:
                    total_prepa_sojourn_times.append(total_time)
                elif 'ING' in user_id[:3]:
                    total_ing_sojourn_times.append(total_time)
                else:
                    total_sojourn_times.append(total_time)

        # 4
        ax4.hist(
            [test_sojourn_times, result_sojourn_times],
            label=["Test q.", "Result q."],
            color=[color_test, color_result],
            bins=30,
        )
        ax4.set_title("Distribution of sojourn times")
        ax4.set_xlabel("Time spent in queue")
        ax4.set_ylabel("Number of users")
        ax4.grid(True, alpha=0.3)
        ax4.set_yscale("log")
        ax4.set_ylim(1)
        ax4.legend(loc="upper right")
        print("- #4 Done: Distribution of sojourn times")

        # 5
        ax5 = fig.add_subplot(gs[2, 1])
        if len(total_sojourn_times) != 0:
            ax5.hist(total_sojourn_times, color="#3498db", alpha=0.7, bins=60)
        else:
            ax5.hist(
                [total_prepa_sojourn_times, total_ing_sojourn_times],
                label=["PREPA", "ING"],
                color=["#53917E", "#715B64"],
                bins=30
            )
            ax5.legend(loc="upper right")

        ax5.set_title("Distribution of total system time")
        ax5.set_xlabel("Total time spent in system")
        ax5.set_ylabel("Number of users")
        ax5.set_yscale("log")
        ax5.set_ylim(1)
        ax5.grid(True, alpha=0.3)
        print("- #5 Done: Distribution of total system time")

        # 6
        ax6 = fig.add_subplot(gs[3, 0])
        window_size = max(1, len(self.timestamps) // 40)

        if test_sojourn_times:
            cumsum = np.cumsum(np.insert(test_sojourn_times, 0, 0))
            test_ma = (cumsum[window_size:] - cumsum[:-window_size]) / window_size
            ax6.plot(
                np.arange(len(test_ma)), test_ma, label="Test q.", color=color_test
            )

        if result_sojourn_times:
            cumsum = np.cumsum(np.insert(result_sojourn_times, 0, 0))
            result_ma = (cumsum[window_size:] - cumsum[:-window_size]) / window_size
            ax6.plot(
                range(len(result_ma)),
                result_ma,
                label="Result q.",
                color=color_result,
            )

        ax6.set_title(f"Moving average wait times (with window_size = {window_size})")
        ax6.set_xlabel("Job number")
        ax6.set_ylabel("Average waiting time")
        ax6.grid(True, alpha=0.3)
        ax6.set_ylim(0)
        ax6.legend(loc="upper right")
        print(f"- #6 Done: Moving average wait times (with window_size = {window_size})")

        # 7
        ax7 = fig.add_subplot(gs[3, 1])

        completed_jobs = []
        attempted_jobs = []
        timestamps_after_warmup = []

        # warmup
        timestamps = np.array(self.timestamps)
        warmup_period = timestamps[-1] * 0.1
        window_size = max(1, len(timestamps) // 40)

        mask = timestamps >= warmup_period
        timestamps_after_warmup = timestamps[mask]

        # convert dictionaries to arrays -> faster processing
        entry_times = np.array([self.test_queue_entry_times[uid] for uid in self.test_queue_entry_times])
        exit_times = np.array([
            self.result_queue_exit_times.get(uid, np.inf)
            for uid in self.test_queue_entry_times
        ])

        completed_jobs = np.zeros(len(timestamps_after_warmup))
        attempted_jobs = np.zeros(len(timestamps_after_warmup))

        for i, t in enumerate(timestamps_after_warmup):
            completed_jobs[i] = np.sum((exit_times <= t) & (entry_times <= t))
            attempted_jobs[i] = np.sum(entry_times <= t)

        # sliding window throughput computation
        if len(completed_jobs) > window_size:
            time_diffs = timestamps_after_warmup[window_size:] - timestamps_after_warmup[:-window_size]
            completed_diffs = completed_jobs[window_size:] - completed_jobs[:-window_size]
            attempted_diffs = attempted_jobs[window_size:] - attempted_jobs[:-window_size]

            completed_rates = completed_diffs / time_diffs
            attempted_rates = attempted_diffs / time_diffs


            ax7.plot(
                timestamps_after_warmup[window_size:],
                completed_rates,
                label="Full throughput",
                color="#177E89"
            )
            ax7.plot(
                timestamps_after_warmup[window_size:],
                attempted_rates,
                label="'Test' throughput",
                color="#FFC857",
                linestyle="--"
            )

        ax7.set_title("System throughput rates")
        ax7.set_xlabel("Time")
        ax7.set_ylabel("Jobs per unit time")
        ax7.grid(True, alpha=0.3)
        ax7.set_ylim(0)
        ax7.legend(loc="upper right")
        print("- #7 Done: System throughput rates")


        # 8
        ax8 = fig.add_subplot(gs[4, 0])

        test_blocked_times_set = set(self.test_queue_blocked_times)
        result_blocked_times_set = set(self.result_queue_blocked_times)
        window_size = max(1, len(self.timestamps) // 40)
        block_window = max(1, len(self.timestamps) // window_size)

        if block_window > 0:
            test_blocks = np.zeros(len(self.timestamps))
            result_blocks = np.zeros(len(self.timestamps))

            for idx, t in enumerate(self.timestamps):
                # Use a slice of the timestamp range to find blocked times
                test_blocked = sum(1 for time in range(max(0, t - block_window), t) if time in test_blocked_times_set)
                result_blocked = sum(1 for time in range(max(0, t - block_window), t) if time in result_blocked_times_set)

                test_blocks[idx] = test_blocked / block_window
                result_blocks[idx] = result_blocked / block_window
        else:
            # Edge case: If block_window is 0, set blocking probabilities to 0
            test_blocks = np.zeros(len(self.timestamps))
            result_blocks = np.zeros(len(self.timestamps))

        ax8.plot(self.timestamps, test_blocks, label="Test q.", color=color_test)
        ax8.plot(self.timestamps, result_blocks, label="Result q.", color=color_result)
        ax8.set_title("Blocking probability over time")
        ax8.set_xlabel("Time")
        ax8.set_ylabel("Blocking probability")
        ax8.grid(True, alpha=0.3)
        ax8.set_ylim(0, 1.0)
        ax8.legend(loc="upper right")
        print("- #8 Done: Blocking probability over time")


        # 9
        ax9 = fig.add_subplot(gs[4, 1])
        ax9.plot(self.timestamps, self.backup_length, color="#3498db")
        ax9.set_title("Result backup length over time")
        ax9.set_xlabel("Time")
        ax9.set_ylabel("Backup length")
        ax9.grid(True, alpha=0.3)
        ax9.set_ylim(0)
        print("- #9 Done: Result backup length over time")


        # 10
        ax10 = fig.add_subplot(gs[5, :])
        total_load = np.array(self.test_queue_lengths) + np.array(
            self.result_queue_lengths
        )
        test_proportion = np.array(self.test_queue_lengths) / (total_load + 1e-10)
        result_proportion = np.array(self.result_queue_lengths) / (total_load + 1e-10)

        ax10.stackplot(
            self.timestamps,
            [test_proportion, result_proportion],
            labels=["Test q.", "Result q."],
            colors=[color_test, color_result],
            alpha=0.7,
        )
        ax10.set_title("Queue load balance over time")
        ax10.set_xlabel("Time")
        ax10.set_ylabel("Proportion of total load")
        ax10.grid(True, alpha=0.3)
        ax10.set_ylim(0, 1.0)
        ax10.legend(loc="upper right")
        print("- #10 Done: Queue load balance over time")

        fig.suptitle("Moulinette queue system metrics", fontsize=16, y=0.95)
        print("\n################################################\n\n")
        plt.savefig(save_filename, dpi=300, bbox_inches="tight")
        plt.close()