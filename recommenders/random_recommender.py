import json
import random
from threading import Thread, Lock
from urllib.request import urlopen

from flask import Flask, request, abort

app = Flask(__name__)

models = {}
phases = {}

modelsLock = Lock()
phasesLock = Lock()


class MostPopular(Thread):

    def __init__(self, exp, callback):
        super().__init__()
        self.exp = exp
        self.callback = callback

    def run(self):
        with urlopen(self.callback + "/dataset?id=" + str(self.exp)) as response:
            ratings = json.loads(response.read().decode())
            model = {'items': set(),
                     'ratings': set()}

            for rating in ratings:
                model['items'].add(rating[1])
                model['ratings'].add(rating[2])

            model['items'] = list(model['items'])
            model['ratings'] = list(model['ratings'])

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

    callback = request.args.get("callback")
    if callback is None:
        abort(400)

    # Check that the experiment is not running
    phasesLock.acquire()
    if exp in phases:
        phasesLock.release()
        abort(400)

    phases[exp] = "training"
    phasesLock.release()

    recommender = MostPopular(exp, callback)
    recommender.start()

    return json.dumps({'id': exp,
                       'callback': callback,
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


@app.route("/predict", methods=['POST'])
def predict():
    exp = request.args.get("id")
    if exp is None:
        abort(400)
    try:
        exp = int(exp)
    except ValueError:
        abort(400)

    content = request.json
    if content is None:
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
    predictions = []

    for rating in content:
        del rating
        prediction = random.choice(models[exp]['ratings'])
        predictions.append(prediction)

    modelsLock.release()
    phasesLock.release()

    return json.dumps(predictions)


@app.route("/recommend", methods=['POST'])
def recommend():
    exp = request.args.get("id")
    k = request.args.get("k")
    if exp is None or k is None:
        abort(400)
    try:
        exp = int(exp)
        k = int(k)
    except ValueError:
        abort(400)

    if k <= 0:
        abort(400)

    content = request.json
    if content is None:
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
    recommendations = []

    for user in content:
        del user
        top_k = random.sample(models[exp]['items'], k)
        recommendations.append(top_k)

    modelsLock.release()
    phasesLock.release()

    return json.dumps(recommendations)


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
    app.run(port=5002)