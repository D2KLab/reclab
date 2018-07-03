import json
import urllib.request
from threading import Thread, Lock

from flask import Flask, request, abort

app = Flask(__name__)

models = {}
phases = {}

modelsLock = Lock()
phasesLock = Lock()


class MostPopular(Thread):

    def __init__(self, exp):
        super().__init__()
        self.exp = exp

    def run(self):
        with urllib.request.urlopen("http://localhost:5000/dataset?id=" + str(self.exp)) as url:
            ratings = json.loads(url.read().decode())
            model = {}

            for rating in ratings:
                item = rating[1]

                if item in model:
                    model[item] += 1
                else:
                    model[item] = 1

            modelsLock.acquire()
            models[self.exp] = model

            phasesLock.acquire()
            phases[self.exp] = "ready"

            modelsLock.release()
            phasesLock.release()


@app.route("/setup", methods=['GET'])
def setup():
    exp = request.args.get("id")
    if exp is None:
        abort(400)
    try:
        exp = int(exp)
    except ValueError:
        abort(400)

    # Check that the experiment is not running
    phasesLock.acquire()
    if exp in phases:
        phasesLock.release()
        abort(400)

    phases[exp] = "training"
    phasesLock.release()

    recommender = MostPopular(exp)
    recommender.start()

    return json.dumps({'id': exp,
                       'status': "training"})


@app.route("/clear", methods=['GET'])
def clear():
    exp = request.args.get("id")
    if exp is None:
        abort(400)
    try:
        exp = int(exp)
    except ValueError:
        abort(400)

    phasesLock.acquire()

    if exp not in phases:
        phasesLock.release()
        abort(404)

    if phases[exp] != "ready":
        result = {'id': exp,
                  'status': phases[exp]}
        phasesLock.release()
        return json.dumps(result)

    modelsLock.acquire()

    del phases[exp]
    del models[exp]

    phasesLock.release()
    modelsLock.release()

    return json.dumps({'id': exp,
                       'status': "clear"})


@app.route("/predict", methods=['GET'])
def predict():
    exp = request.args.get("id")
    user = request.args.get("user")
    item = request.args.get("item")
    if exp is None or user is None or item is None:
        abort(400)
    try:
        exp = int(exp)
        user = int(user)
        item = int(item)
    except ValueError:
        abort(400)

    phasesLock.acquire()

    if exp not in phases:
        phasesLock.release()
        abort(404)

    if phases[exp] != "ready":
        result = {'id': exp,
                  'status': phases[exp]}
        phasesLock.release()
        return json.dumps(result)

    modelsLock.acquire()
    try:
        rating = models[exp][item]
    except KeyError:
        rating = 0

    modelsLock.release()
    phasesLock.release()

    result = {'id': exp,
              'user': user,
              'item': item,
              'rating': rating}

    return json.dumps(result)


@app.route("/status", methods=['GET'])
def status():
    exp = request.args.get("id")
    if exp is None:
        abort(400)
    try:
        exp = int(exp)
    except ValueError:
        abort(400)

    phasesLock.acquire()

    if exp not in phases:
        result = {'id': exp,
                  'status': "clear"}
    else:
        result = {'id': exp,
                  'status': phases[exp]}

    phasesLock.release()
    return json.dumps(result)


if __name__ == "__main__":
    app.run(port=5001)
