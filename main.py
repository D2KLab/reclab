import json
import random

import requests
from flask import Flask, render_template, request
from flask_restful import Resource, Api, abort
from pymongo import MongoClient
from requests.exceptions import ConnectionError, HTTPError, Timeout

import reclab

with open('config.json') as f:
    config = json.load(f)

client = MongoClient(config['mongodb']['host'], config['mongodb']['port'])
db = client[config['mongodb']['db']]

app = Flask(__name__)
api = Api(app)


def next_id():
    exp = db['experiments'].find_one({'id': {'$exists': True}}, sort=[('id', -1)])
    if exp is not None:
        return exp['id'] + 1
    else:
        return 1


class Experiment(Resource):

    @staticmethod
    def get(exp_id):
        exp = db['experiments'].find_one({'id': exp_id})
        if exp is None:
            abort(404)

        del exp['_id']
        return exp

    @staticmethod
    def post():
        content = request.json
        if content is None:
            abort(400)

        try:
            if content['dataset'] not in config['datasets']:
                abort(400)

            if content['splitter'] not in reclab.splitter_list():
                abort(400)

            try:
                test_size = float(content['test_size'])
                if test_size < 0 or test_size > 1:
                    abort(400)
            except ValueError:
                abort(400)

            try:
                k = int(content['k'])
                if k <= 0:
                    abort(400)
            except ValueError:
                abort(400)

            try:
                threshold = float(content['threshold'])
                if threshold < 0:
                    abort(400)
            except ValueError:
                abort(400)

            for recommender in content['recommenders']:
                if recommender not in config['recommenders']:
                    abort(400)

        except KeyError:
            abort(400)

        exp = {'id': next_id(),
               'version': config['version'],
               'dataset': content['dataset'],
               'seed': random.random(),
               'splitter': content['splitter'],
               'test_size': float(content['test_size']),
               'k': int(content['k']),
               'threshold': float(content['threshold']),
               'recommenders': content['recommenders'],
               'results': []}

        db['experiments'].insert_one(exp)

        # Start the experiment
        reclab.Experiment(exp['id'], db, config).start()

        del exp['_id']
        return exp, 201


class Dataset(Resource):

    @staticmethod
    def get(exp_id):
        exp = db['experiments'].find_one({'id': exp_id})
        if exp is None:
            abort(404)

        # Load the dataset
        loader = reclab.loader_instance(config['datasets'][exp['dataset']])
        ratings = loader.load()

        # Split the dataset
        splitter = reclab.splitter_instance(exp)
        training_set = splitter.split(ratings)[0]

        return training_set


class Config(Resource):

    @staticmethod
    def get():
        return {'datasets': config['datasets'],
                'recommenders': config['recommenders'],
                'splitters': reclab.splitter_list(),
                'metrics': reclab.evaluator_list()}


class Status(Resource):

    @staticmethod
    def get():
        status = {}
        down = False

        for recommender in config['recommenders']:
            try:
                r = requests.get(config['recommenders'][recommender]['url'], timeout=5)
                r.raise_for_status()
                status[recommender] = "up"
            except (ConnectionError, HTTPError, Timeout):
                status[recommender] = "down"
                down = True

        if down:
            return status, 503
        else:
            return status


api.add_resource(Experiment, '/experiment', '/experiment/<int:exp_id>')
api.add_resource(Dataset, '/dataset/<int:exp_id>')
api.add_resource(Config, '/config')
api.add_resource(Status, '/status')


@app.route("/")
def main():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(port=6000)
