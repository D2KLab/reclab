import json
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
            model = {}
            max_item = 0
            max_rating = 0

            for rating in ratings:
                item = rating[1]

                if item in model:
                    model[item] += 1
                else:
                    model[item] = 1

                # Find the count of the most popular item
                if max_item < model[item]:
                    max_item = model[item]

                value = rating[2]

                # Find the maximum rating value
                if max_rating < value:
                    max_rating = value

            # Normalize the scores
            for item in model:
                model[item] = model[item] / max_item * max_rating

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
        try:
            prediction = models[exp][rating[1]]
        except KeyError:
            prediction = 0
        predictions.append(prediction)

    modelsLock.release()
    phasesLock.release()

    return json.dumps(predictions)


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
