import inspect
import json
import time
from threading import Thread
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen, Request

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
        query = {'id': exp['id'],
                 'callback': config['url']}
        urlopen(url + "/setup?" + urlencode(query))
    except URLError:
        return

    # Wait for the recommender
    status = None

    while status != "ready":
        time.sleep(1)
        try:
            with urlopen(url + "/status?id=" + str(exp['id'])) as response:
                response_json = json.loads(response.read().decode())
                status = response_json['status']
        except URLError:
            return
        except KeyError:
            return

    # Get top-k recommendations
    request = Request(url + "/recommend?id=" + str(exp['id']) + "&k=" + str(exp['k']))
    request.add_header('Content-Type', 'application/json; charset=utf-8')
    request_json = json.dumps(user_set).encode('utf-8')
    request.add_header('Content-Length', len(request_json))

    try:
        response = urlopen(request, request_json)
        recommendations = json.loads(response.read().decode())
    except URLError:
        return

    # Clear the model
    try:
        urlopen(url + "/clear?id=" + str(exp['id']))
    except URLError:
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
        exp['results'] = []

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

            if recommendations is None:
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
