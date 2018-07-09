import inspect
import json
import time
from threading import Thread

import requests
from requests.exceptions import HTTPError, Timeout

from .evaluator import Evaluator
from .loader import loader_instance
from .splitter import splitter_instance


def get_splitted_dataset(exp, config):
    # Load the dataset
    loader = loader_instance(config['datasets'][exp['dataset']])
    ratings = loader.load()

    # Split the dataset
    splitter = splitter_instance(exp)
    return splitter.split(ratings)


def get_user_set(test_set):
    user_set = set()

    for rating in test_set:
        user_set.add(rating[0])

    return list(user_set)


def run_recommender(exp, recommender, user_set, config):
    url = config['recommenders'][recommender]['url']

    # Train the recommender
    try:
        r = requests.post(url + '/model/' + str(exp['id']),
                          json={'callback': config['url'], 'threshold': exp['threshold']}, timeout=60)
        r.raise_for_status()
    except (HTTPError, Timeout):
        return

    # Wait for the recommender
    status = None
    counter = 0

    while status != "ready":
        time.sleep(counter)
        counter += 1
        try:
            assert counter <= 60
            r = requests.get(url + '/model/' + str(exp['id']), timeout=60)
            r.raise_for_status()
            response_json = json.loads(r.text)
            status = response_json['status']
        except (HTTPError, Timeout, KeyError, AssertionError):
            return

    # Get top-k recommendations
    try:
        r = requests.post(url + "/recommendation/" + str(exp['id']) + "?k=" + str(exp['k']), json=user_set, timeout=60)
        r.raise_for_status()
    except (HTTPError, Timeout):
        return

    # Wait for the recommender
    status = None
    response_json = None
    counter = 0

    while status != "ready":
        time.sleep(counter)
        counter += 1
        try:
            assert counter <= 60
            r = requests.get(url + '/recommendation/' + str(exp['id']), timeout=60)
            r.raise_for_status()
            response_json = json.loads(r.text)
            status = response_json['status']
        except (HTTPError, Timeout, KeyError, AssertionError):
            return

    try:
        recommendations = response_json['recommendations']
    except KeyError:
        return

    # Delete the model
    try:
        r = requests.delete(url + '/model/' + str(exp['id']), timeout=60)
        r.raise_for_status()
    except (HTTPError, Timeout):
        pass

    return recommendations


class Experiment(Thread):

    def __init__(self, exp_id, db, config):
        super().__init__()
        self.exp_id = exp_id
        self.db = db
        self.config = config

    def run(self):
        exp = self.db['experiments'].find_one({'id': self.exp_id})
        if exp is None:
            return

        training_set, test_set = get_splitted_dataset(exp, self.config)
        user_set = get_user_set(test_set)

        for recommender in exp['recommenders']:
            result = {'name': recommender,
                      'status': 'running'}
            exp['results'].append(result)
            self.db['experiments'].save(exp)

            recommendations = run_recommender(exp, recommender, user_set, self.config)

            try:
                assert recommendations is not None
                assert len(recommendations) == len(user_set)
                for recommendation in recommendations:
                    assert len(recommendation) <= exp['k']
            except AssertionError:
                result['status'] = 'failed'
                self.db['experiments'].save(exp)
                continue

            evaluator = Evaluator(exp, training_set, test_set, user_set, recommendations)

            # For all the metrics
            for name, obj in inspect.getmembers(evaluator):
                if inspect.ismethod(obj) and not name.startswith('_'):
                    result[name] = obj()

            result['status'] = 'done'
            self.db['experiments'].save(exp)
