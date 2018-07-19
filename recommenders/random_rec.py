import json
import random
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
            model_items = set()

            for rating in ratings:
                item = rating[1]

                model_items.add(item)

            models_lock.acquire()
            models[self.exp_id] = {'items': model_items,
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
                del user
                top_k = random.sample(model['items'], self.k)
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
    return "Random"


if __name__ == "__main__":
    app.run(port=6001)
