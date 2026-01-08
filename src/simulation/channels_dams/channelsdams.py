import random

from src.models.basics import Utilisateur, Commit
from src.simulation.waterfall.backup import WaterfallMoulinetteFiniteBackup


class ChannelsAndDams(WaterfallMoulinetteFiniteBackup):
    """
    Moulinette Channels&Dams, avec 3 stages de processing :

    1. Checker si la régulation de la population ING est en place et blocage de la moulinette si nécessaire.
    2. Placer le code dans une file d'attente FIFO finie (taille ks) pour exécuter des tests. (K serveurs)
    3. Envoyer le résultat dans une file d'attente FIFO finie (taille kf) pour l'envoyer au front. (1 serveur)

    Si un blocage survient au niveau du serveur d'envoi du résultat, le résultat du test est envoyé dans un backup.
    Lorsque la queue des résultats est libre, les commits du backup y sont poussés.

    :param K: Nombre de FIFO pour les tests.
    :param process_time: Temps de process d'un utilisateur dans la file de test.
    :param result_time: Temps de process d'un utilisateur dans la file de résultat.
    :param ks: Tailles des FIFOs pour exécuter des tests.
    :param kf: Taille de la FIFO pour l'envoi des résultats.
    :param tb: Temps de blocage de la moulinette pour les ING.
    :param block_option: Permet d'activer ou non la fonction de blocage des ING.
    """

    def __init__(
        self,
        K: int = 1,
        process_time: int = 1,
        result_time: int = 1,
        ks: int = 1,
        kf: int = 1,
        tb: int = 5,
        block_option: bool = False,
        tag_limit: int = 5,
        nb_exos: int = 10,
    ):
        super().__init__(
            K=K, process_time=process_time, result_time=result_time, ks=ks, kf=kf,
            tag_limit=tag_limit, nb_exos=nb_exos
        )
        self.tb = tb
        self.block_option = block_option
        self.is_blocked = False

    def regulate_ing(self):
        """
        Implémentation du "barrage" de régulation pour la population ING.
        """
        while True:
            if (
                all(user.current_exo > self.nb_exos for user in self.users)
                and len(self.backup_storage.items) == 0
            ):
                break

            # On bloque le serveur pour tb temps
            self.is_blocked = True
            print(f"Moulinette blocked for ING population at {self.env.now}")
            yield self.env.timeout(self.tb)

            # On débloque le serveur pour tb/2 temps
            self.is_blocked = False
            print(f"Moulinette unblocked for ING population at {self.env.now}")
            yield self.env.timeout(self.tb // 2)

    def handle_commit(self, user: Utilisateur):
        """
        Simule la réception et le traitement d'un commit pour un utilisateur.

        :param user: Utilisateur.
        """
        minute_unit = 2
        last_chance_commit = None
        # modéliser l'occupation plus longue de la moulinette par les prépas
        coeff = 2 if user.promo == "PREPA" else 1

        while user.current_exo <= self.nb_exos:
            # check si ING et blocage actif
            if self.block_option and user.promo == "ING" and self.is_blocked:
                print(f"{user} : blocked by ING regulation.")
                yield self.env.timeout(random.randint(1, 3))
                continue

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
            user_id = f"{user.promo}_{user.name}_{current_time}_{exo}"

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
                yield self.env.timeout(self.process_time * coeff)
                print(f"{commit} : finishes testing.")
                yield self.test_queue.get(lambda x: x == user)

            self.metrics.record_test_queue_exit(user_id, self.env.now)

            # si plus de place dans la FIFO d'envoi, refus
            if len(self.result_queue.items) >= self.kf:
                self.metrics.record_result_queue_blocked(self.env.now)
                print(
                    f"{commit} : refused at result queue (FULL). The result is backed up."
                )
                # on ajoute le commit dans le backup
                self.backup_storage.put((commit, user_id))

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
