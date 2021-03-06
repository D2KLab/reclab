import json
from threading import Thread, Lock

import requests
from flask import Flask
from flask_restful import Api
from requests.exceptions import ConnectionError, HTTPError, Timeout

from recommenders import Model, Recommendation

app = Flask(__name__)
api = Api(app)

models = {}
phases = {}

models_lock = Lock()
phases_lock = Lock()


class Trainer(Thread):

    def __init__(self, exp_id, callback, threshold):
        super().__init__()
        self.exp_id = exp_id
        self.callback = callback
        self.threshold = threshold

    def run(self):
        try:
            r = requests.get(self.callback + "/dataset/" + str(self.exp_id), timeout=60)
            r.raise_for_status()
            ratings = json.loads(r.text)
            model_items = {}
            model_users = {}
            model_top_k = []

            for rating in ratings:
                user = rating[0]
                item = rating[1]

                if item in model_items:
                    model_items[item] += 1
                else:
                    model_items[item] = 1

                if user not in model_users:
                    model_users[user] = set()
                model_users[user].add(item)

            # Sort items by the number of ratings
            for item in sorted(model_items, key=model_items.get, reverse=True):
                model_top_k.append(item)

            models_lock.acquire()
            models[self.exp_id] = {'top_k': model_top_k,
                                   'users': model_users,
                                   'recommendations': None}

            phases_lock.acquire()
            phases[self.exp_id] = "ready"
            models_lock.release()
            phases_lock.release()

        except (ConnectionError, HTTPError, Timeout, ValueError, TypeError, KeyError):
            phases_lock.acquire()
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

        try:
            recommendations = []

            for user in self.user_set:
                counter = 0
                top_k = []
                for target_item in model['top_k']:
                    try:
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

        except (ValueError, TypeError, KeyError):
            phases_lock.acquire()
            models_lock.acquire()
            model['recommendations'] = None
            phases[self.exp_id] = "ready"
            models_lock.release()
            phases_lock.release()


api.add_resource(Model, '/model/<int:exp_id>',
                 resource_class_args=(models, models_lock, phases, phases_lock, Trainer))
api.add_resource(Recommendation, '/recommendation/<int:exp_id>',
                 resource_class_args=(models, models_lock, phases, phases_lock, Recommender))


@app.route("/")
def main():
    return "Most Popular"


if __name__ == "__main__":
    app.run(port=6002)
