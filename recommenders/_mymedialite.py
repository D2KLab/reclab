import csv
import json
import subprocess
from subprocess import SubprocessError
from threading import Thread, Lock

import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout

from recommenders import Model, Recommendation

exec_path = "../mymedialite"
exec_memory = 4 * 1024 * 1024
exec_lock = Lock()


def mymedialite(models, models_lock, phases, phases_lock, recommender):

    work_path = "/tmp/" + recommender
    subprocess.run("mkdir " + work_path, shell=True)

    class Trainer(Thread):

        def __init__(self, exp_id, callback, threshold):
            super().__init__()
            self.exp_id = exp_id
            self.callback = callback
            self.threshold = threshold

        def run(self):
            exp_path = work_path + "/" + str(self.exp_id)

            try:
                r = requests.get(self.callback + "/dataset/" + str(self.exp_id), timeout=60)
                r.raise_for_status()
                ratings = json.loads(r.text)

                subprocess.run("mkdir " + exp_path, shell=True, check=True)

                model_items = {}
                model_users = {}
                model_top_k = []

                with open(exp_path + "/training.txt", 'w', newline='') as fp:
                    writer = csv.writer(fp)
                    for rating in ratings:
                        user = rating[0]
                        item = rating[1]
                        value = rating[2]

                        if item in model_items:
                            model_items[item] += 1
                        else:
                            model_items[item] = 1

                        if user not in model_users:
                            model_users[user] = set()
                        model_users[user].add(item)

                        if value > self.threshold:
                            writer.writerow(rating[:3])

                # Sort items by the number of ratings
                for item in sorted(model_items, key=model_items.get, reverse=True):
                    model_top_k.append(item)

                exec_lock.acquire()
                subprocess.run("ulimit -d " + str(exec_memory) + " && "
                               "mono " + exec_path +
                               "/item_recommendation.exe "
                               "--training-file=" + exp_path + "/training.txt "
                               "--recommender=" + recommender + " "
                               "--save-model=" + exp_path + "/model.txt", shell=True,
                               check=True)
                exec_lock.release()

                models_lock.acquire()
                models[self.exp_id] = {'top_k': model_top_k,
                                       'users': model_users,
                                       'recommendations': None}

                phases_lock.acquire()
                phases[self.exp_id] = "ready"
                models_lock.release()
                phases_lock.release()

            except (ConnectionError, HTTPError, Timeout, SubprocessError, ValueError, TypeError, KeyError):
                if exec_lock.locked():
                    exec_lock.release()
                phases_lock.acquire()
                subprocess.run("rm -r " + exp_path, shell=True)
                del phases[self.exp_id]
                phases_lock.release()

    class Recommender(Thread):

        def __init__(self, exp_id, user_set, k):
            super().__init__()
            self.exp_id = exp_id
            self.user_set = user_set
            self.k = k

        def run(self):
            model = models[self.exp_id]
            exp_path = work_path + "/" + str(self.exp_id)

            try:
                with open(exp_path + "/users.txt", 'w', newline='') as fp:
                    writer = csv.writer(fp)
                    for user in self.user_set:
                        writer.writerow([user])

                exec_lock.acquire()
                subprocess.run("ulimit -d " + str(exec_memory) + " && "
                               "mono " + exec_path +
                               "/item_recommendation.exe "
                               "--training-file=" + exp_path + "/training.txt "
                               "--recommender=" + recommender + " "
                               "--load-model=" + exp_path + "/model.txt "
                               "--test-users=" + exp_path + "/users.txt "
                               "--prediction-file=" + exp_path + "/recommendations.txt",
                               shell=True, check=True)
                exec_lock.release()

                mml_rec = {}

                with open(exp_path + "/recommendations.txt", 'r') as fp:
                    for line in fp.readlines():
                        rows = line.split('\t')

                        try:
                            user = int(rows[0])
                        except ValueError:
                            user = rows[0]

                        if user not in mml_rec:
                            mml_rec[user] = []

                        items = rows[1].split(',')

                        if len(items) == 1:
                            # Fallback to Most Popular
                            mml_rec[user] = model['top_k']
                        else:
                            for item in items:
                                pair = item.split(':')

                                if pair[0].startswith('['):
                                    pair[0] = pair[0][1:]

                                try:
                                    item = int(pair[0])
                                except ValueError:
                                    item = pair[0]

                                mml_rec[user].append(item)

                recommendations = []

                for user in self.user_set:
                    counter = 0
                    top_k = []
                    for target_item in mml_rec[user]:
                        try:
                            # Avoid recommending items in the training set
                            if target_item not in model['users'][user]:
                                counter += 1
                                top_k.append(target_item)
                        except KeyError:
                            counter += 1
                            top_k.append(target_item)
                        if counter >= self.k:
                            break

                    recommendations.append(top_k)

                phases_lock.acquire()
                models_lock.acquire()
                model['recommendations'] = recommendations
                phases[self.exp_id] = "ready"
                models_lock.release()
                phases_lock.release()

            except (SubprocessError, ValueError, TypeError, KeyError):
                if exec_lock.locked():
                    exec_lock.release()
                phases_lock.acquire()
                models_lock.acquire()
                subprocess.run("rm -r " + exp_path, shell=True)
                model['recommendations'] = None
                phases[self.exp_id] = "ready"
                models_lock.release()
                phases_lock.release()

    class ModelMML(Model):

        def delete(self, exp_id):
            exp_path = work_path + "/" + str(exp_id)
            subprocess.run("rm -r " + exp_path, shell=True)
            return super().delete(exp_id)

    class RecommendationMML(Recommendation):

        def delete(self, exp_id):
            exp_path = work_path + "/" + str(exp_id)
            subprocess.run("rm " + exp_path + "/recommendations.txt", shell=True)
            return super().delete(exp_id)

    return Trainer, Recommender, ModelMML, RecommendationMML
