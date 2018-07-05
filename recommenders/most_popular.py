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
            model_dict = {}
            model_top_k = []

            for rating in ratings:
                item = rating[1]

                if item in model_dict:
                    model_dict[item] += 1
                else:
                    model_dict[item] = 1

            # Sort items by the number of ratings
            for item in sorted(model_dict, key=model_dict.get, reverse=True):
                model_top_k.append(item)

            modelsLock.acquire()
            models[self.exp] = model_top_k

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
    model = models[exp]
    recommendations = []

    for user in content:
        del user
        recommendations.append(model[0:k])

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
