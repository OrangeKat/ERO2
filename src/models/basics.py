from typing import List
import simpy
import random
import string

from src.utils.metrics import QueueMetrics


class Utilisateur:
    """
    Initialise un utilisateur de notre file d'attente.

    :param name: Nom de l'étudiant.
    :param promo: Promotion de l'étudiant.
    """

    def __init__(
        self,
        name: str,
        promo: str,
    ):
        self.name = name
        self.promo = promo
        self.current_exo = 1
        self.intelligence = max(min(random.gauss(mu=0.6, sigma=0.075), 0.75), 0.2)

    def __str__(self):
        return f"[{self.name} - {self.promo}]"


class Commit:
    """
    Initialise un commit avec tag dans la file d'attente.

    :param user: autheur du commit.
    :param date: date (timestep de la simulation) du commit
    :param exo: exercice du commit.
    """

    def __init__(
        self, user: Utilisateur, date: int, exo: int, chance_to_pass: float | None
    ):
        self.user = user
        self.id = self._generate_id()
        self.date = date
        self.exo = exo
        self.chance_to_pass = (
            user.intelligence if chance_to_pass == None else chance_to_pass
        )

    def _generate_id(self):
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

    def __str__(self):
        return f"[{self.id} - exo {self.exo} - time {self.date}] by {self.user}"


class Moulinette:
    """
    Initialise une instance de moulinette.

    :param K: Nombre de FIFOs pour les tests.
    :param process_time: Temps de process d'un utilisateur dans la file de test.
    :param result_time: Temps de process d'un utilisateur dans la file d'envoi.
    :param tag_limit: Nombre de tag limite par heure (60 unités de temps).
    :param nb_exos: Nombre d'exos par utilisateur.
    """

    def __init__(
        self,
        K: int = 10,
        process_time: int = 1,
        result_time: int = 1,
        tag_limit: int = 5,
        nb_exos: int = 10,
    ):
        self.env = simpy.Environment()
        self.test_server = simpy.Resource(self.env, capacity=K)
        self.result_server = simpy.Resource(self.env, capacity=1)
        self.tag_limit = tag_limit
        self.process_time = process_time
        self.result_time = result_time
        self.nb_exos = nb_exos
        self.users: List[Utilisateur] = []
        self.users_commit_time = {}  # user -> [timestep, ...] (maxlen tag_limit)
        self.backup_storage = simpy.FilterStore(self.env)
        self.metrics = QueueMetrics()

    def collect_metrics(self):
        """
        Collect metrics at regular intervals
        """
        while True:
            if (all(user.current_exo > self.nb_exos for user in self.users) and
                len(self.backup_storage.items) == 0 and
                self.test_server.count == 0 and
                len(self.test_server.queue) == 0 and
                self.result_server.count == 0 and
                len(self.result_server.queue) == 0):
                break

            # Test queue metrics
            test_server_count = self.test_server.count
            test_queue_length = len(self.test_server.queue) + test_server_count
            test_utilization = (
                self.test_server.count / self.test_server.capacity
                if self.test_server.capacity > 0
                else 0
            )
            backup_length = len(self.backup_storage.items)

            # Result queue metrics
            result_server_count = self.result_server.count
            result_queue_length = len(self.result_server.queue) + result_server_count
            result_utilization = (
                self.result_server.count / self.result_server.capacity
                if self.result_server.capacity > 0
                else 0
            )

            self.metrics.record_state(
                self.env.now,
                test_agents=test_server_count,
                test_queue_length=test_queue_length,
                backup_length=backup_length,
                result_agents=result_server_count,
                result_queue_length=result_queue_length,
                test_server_utilization=test_utilization,
                result_server_utilization=result_utilization,
            )

            yield self.env.timeout(1)

    def add_user(self, user: Utilisateur = None):
        """
        Ajoute un nouvel utilisateur dans la moulinette.

        :param user: Utilisateur.
        """
        if user is None:
            user = Utilisateur()
        self.users.append(user)
        self.users_commit_time[user.name] = []

    def start_simulation(self, until: int | None, save_filename: str = "metrics.png"):
        """
        Lance une simulation complète sur tous les utilisateurs dans la moulinette et affiche des métriques.

        :param until: Limite de temps de la simulation.
        """
        self.env.process(self.collect_metrics())

        for user in self.users:
            self.env.process(self.handle_commit(user))

        self.env.run(until=until)

        metrics = self.metrics.calculate_metrics()
        print("\nSimulation Metrics:")
        print("\nTest Queue Metrics:")
        for metric, value in metrics["test_queue"].items():
            print(f"- {metric}: {value}")

        print("\nResult Queue Metrics:")
        for metric, value in metrics["result_queue"].items():
            print(f"- {metric}: {value}")

        print("\nSojourn Times:")
        for queue, times in metrics["sojourn_times"].items():
            print(f"- {queue}:")
            print(f"  - Average: {times['avg']}")
            print(f"  - Variance: {times['var']}")

        print(f"\nThroughput: {metrics['throughput']}")

        self.metrics.plot_metrics(save_filename=save_filename)
