import json
import time
from threading import Thread
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from .loader import loader_instance
from .splitter import splitter_instance


def get_predict_set(exp, config):
    dataset_config = config['datasets'][exp['dataset']]

    # Load the dataset
    loader = loader_instance(dataset_config['format'])
    ratings = loader.load(dataset_config['path'])

    # Split the dataset
    splitter = splitter_instance(exp['splitter'], exp['test_size'], exp['seed'])
    test_set = splitter.split(ratings)[1]

    predict_set = []

    for rating in test_set:
        predict_set.append([rating[0], rating[1]])

    return predict_set


def get_predictions(exp_id, recommender, predict_set, config):
    url = config['recommenders'][recommender]['url']

    # Train the recommender
    try:
        query = {'id': exp_id,
                 'callback': config['url']}
        urlopen(url + "/setup?" + urlencode(query))
    except URLError:
        return

    # Wait for the recommender
    status = None

    while status != "ready":
        time.sleep(1)
        try:
            with urlopen(url + "/status?id=" + str(exp_id)) as response:
                response_json = json.loads(response.read().decode())
                status = response_json['status']
        except URLError:
            return
        except KeyError:
            return

    request = Request(url + "/predict?id=" + str(exp_id))
    request.add_header('Content-Type', 'application/json; charset=utf-8')
    request_json = json.dumps(predict_set).encode('utf-8')
    request.add_header('Content-Length', len(request_json))

    try:
        response = urlopen(request, request_json)
        predictions = json.loads(response.read().decode())
    except URLError:
        return

    # Clear the model
    try:
        urlopen(url + "/clear?id=" + str(exp_id))
    except URLError:
        pass

    return predictions


class Experiment(Thread):

    def __init__(self, exp_id, db, config):
        super().__init__()
        self.exp_id = exp_id
        self.db = db
        self.config = config

    def run(self):
        exp = self.db['experiments'].find_one({'id': self.exp_id})
        exp['results'] = []

        if exp is None:
            return

        predict_set = get_predict_set(exp, self.config)

        for recommender in exp['recommenders']:
            result = {'name': recommender,
                      'status': 'running'}
            exp['results'].append(result)
            self.db['experiments'].save(exp)

            predictions = get_predictions(self.exp_id, recommender, predict_set, self.config)

            if predictions is None:
                result['status'] = 'failed'
            else:
                result['status'] = 'done'

            self.db['experiments'].save(exp)
