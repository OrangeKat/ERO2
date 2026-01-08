import simpy
import random

from .infinite import WaterfallMoulinetteInfinite
from src.models.basics import Commit, Utilisateur


class WaterfallMoulinetteFinite(WaterfallMoulinetteInfinite):
    """
    Moulinette Waterfall Finie utilisant FilterStore, avec 2 stages de processing :

    1. Placer le code dans une file d'attente FIFO finie (taille ks) pour exécuter des tests. (K serveurs)
    2. Envoyer le résultat dans une file d'attente FIFO finie (taille kf) pour l'envoyer au front. (1 serveur)

    :param K: Nombre de FIFO pour les tests.
    :param process_time: Temps de process d'un utilisateur dans la file de test.
    :param result_time: Temps de process d'un utilisateur dans la file de résultat.
    :param ks: Tailles des FIFOs pour exécuter des tests.
    :param kf: Taille de la FIFO pour l'envoi des résultats.
    """

    def __init__(
        self,
        K: int = 1,
        process_time: int = 1,
        tag_limit: int = 5,
        nb_exos: int = 10,
        result_time: int = 1,
        ks: int = 1,
        kf: int = 1,
    ):
        super().__init__(
            K=K,
            process_time=process_time,
            result_time=result_time,
            tag_limit=tag_limit,
            nb_exos=nb_exos,
        )
        self.ks = ks
        self.kf = kf
        self.test_queue = simpy.FilterStore(self.env, capacity=self.ks)
        self.result_queue = simpy.FilterStore(self.env, capacity=self.kf)

    def handle_commit(self, user: Utilisateur):
        """
        Simule la réception et le traitement d'un commit pour un utilisateur.

        :param user: Utilisateur.
        """
        minute_unit = 2
        last_chance_commit = None

        # working on first exercise
        wating_before_next = round(max(random.gauss(mu=45, sigma=15), 1))
        yield self.env.timeout(wating_before_next * minute_unit)

        while user.current_exo <= self.nb_exos:
            # push autorisé si dans la limite de tag
            current_time = self.env.now
            if len(self.users_commit_time[user.name]) >= self.tag_limit:
                if (
                    self.users_commit_time[user.name][0]
                    > current_time - 60 * minute_unit
                ):
                    yield self.env.timeout(minute_unit)
                    continue
                self.users_commit_time[user.name].pop(0)

            exo = user.current_exo
            commit = Commit(user, current_time, exo, last_chance_commit)
            user_id = f"{user.name}_{current_time}_{exo}"

            # si plus de place dans la FIFO de test, refus
            if len(self.test_queue.items) >= self.ks:
                self.metrics.record_test_queue_blocked(self.env.now)
                print(f"{commit} : refused at test queue (FULL).")
                yield self.env.timeout(random.randint(4, 10) * minute_unit)
                continue

            # métriques queue test
            self.metrics.record_test_queue_entry(user_id, current_time)

            # fifo serveur test
            print(f"{commit} : enters the test queue.")
            yield self.test_queue.put(user)
            with self.test_server.request() as test_request:
                yield test_request
                print(f"{commit} : starts testing.")
                yield self.env.timeout(self.process_time)
                print(f"{commit} : finishes testing.")
                yield self.test_queue.get(lambda x: x == user)

            self.metrics.record_test_queue_exit(user_id, self.env.now)

            # si plus de place dans la FIFO d'envoi, refus
            if len(self.result_queue.items) >= self.kf:
                self.metrics.record_result_queue_blocked(self.env.now)
                print(f"{commit} : refused at result queue (FULL).")
                yield self.env.timeout(random.randint(4, 10) * minute_unit)
                continue

            # métriques queue résultat
            self.metrics.record_result_queue_entry(user_id, self.env.now)

            # fifo serveur d'envoi
            print(f"{commit} : enters the result queue.")
            yield self.result_queue.put(user)
            with self.result_server.request() as result_request:
                yield result_request
                print(f"{commit} : starts result processing.")
                yield self.env.timeout(self.result_time)
                print(f"{commit} : finishes result processing.")
                yield self.result_queue.get(lambda x: x == user)

            self.metrics.record_result_queue_exit(user_id, self.env.now)

            # si le commit est bon
            if random.random() <= commit.chance_to_pass:
                print(f"{commit} : commit passed for exo {exo} !")
                user.current_exo += 1
                self.users_commit_time[user.name] = []
                last_chance_commit = None

                if user.current_exo > self.nb_exos:
                    break

                wating_before_next = round(max(random.gauss(mu=45, sigma=15), 1))
                yield self.env.timeout(wating_before_next * minute_unit)
            else:
                print(
                    f"{commit} : commit failed for exo {exo}... Increasing chance to pass for next commit."
                )
                more_chance_to_pass = max(
                    min(random.gauss(mu=0.1, sigma=0.015), 0.2), 0.05
                )
                last_chance_commit = min(commit.chance_to_pass + more_chance_to_pass, 1)

                self.users_commit_time[user.name].append(current_time)
                wating_before_next = round(max(random.gauss(mu=15, sigma=5), 1))

                yield self.env.timeout(wating_before_next * minute_unit)
