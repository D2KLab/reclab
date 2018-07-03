import json
import random

from flask import Flask, request, abort
from pymongo import MongoClient

import reclab

random.seed()

with open('config.json') as f:
    config = json.load(f)

client = MongoClient(config['mongodb']['host'], config['mongodb']['port'])
db = client[config['mongodb']['db']]

app = Flask(__name__)


def next_id():
    exp = db['experiments'].find_one({'id': {'$exists': True}}, sort=[('id', -1)])
    if exp is not None:
        return exp['id'] + 1
    else:
        return 1


@app.route("/settings", methods=['GET'])
def settings():
    return json.dumps({'datasets': config['datasets']})


@app.route("/experiment", methods=['POST'])
def experiment():
    dataset_id = request.form.get("dataset")
    if dataset_id not in config['datasets']:
        abort(400)

    splitter = request.form.get("splitter")
    if splitter not in reclab.splitter_list():
        abort(400)

    test_size = request.form.get("test_size")
    try:
        test_size = float(test_size)
    except ValueError:
        abort(400)

    if test_size < 0 or test_size > 1:
        abort(400)

    exp = {'id': next_id(),
           'dataset': dataset_id,
           'seed': random.random(),
           'splitter': splitter,
           'test_size': test_size}

    db['experiments'].insert_one(exp)

    del exp['_id']
    return json.dumps(exp)


@app.route("/dataset", methods=['GET'])
def dataset():
    exp_id = request.args.get("id")
    try:
        exp_id = int(exp_id)
    except ValueError:
        abort(400)

    exp = db['experiments'].find_one({'id': exp_id})
    if exp is None:
        abort(404)

    dataset_config = config['datasets'][exp['dataset']]

    # Load the dataset
    loader = reclab.loader_instance(dataset_config['format'])
    ratings = loader.load(dataset_config['path'])

    # Split the dataset
    splitter = reclab.splitter_instance(exp['splitter'], exp['test_size'], exp['seed'])
    training_set = splitter.split(ratings)[0]

    return json.dumps(training_set)


@app.route("/status", methods=['GET'])
def status():
    exp_id = request.args.get("id")
    if exp_id is None:
        abort(400)

    try:
        exp_id = int(exp_id)
    except ValueError:
        abort(400)

    exp = db['experiments'].find_one({'id': exp_id})
    if exp is None:
        abort(404)

    del exp['_id']
    return json.dumps(exp)


if __name__ == "__main__":
    app.run()
