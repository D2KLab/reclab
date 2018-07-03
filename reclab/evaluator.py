import json
import time
from threading import Thread
from urllib.error import URLError
from urllib.request import urlopen, Request

from .loader import loader_instance
from .splitter import splitter_instance


class Evaluator(Thread):

    def __init__(self, exp_id, db, config):
        super().__init__()
        self.exp_id = exp_id
        self.db = db
        self.config = config

    def run(self):
        exp = self.db['experiments'].find_one({'id': self.exp_id})

        if exp is None:
            return

        # Train the recommender
        try:
            urlopen("http://localhost:5001/setup?id=" + str(self.exp_id))
        except URLError:
            return

        # Check if the recommender is ready
        status = None

        while status != "ready":
            time.sleep(1)
            try:
                with urlopen("http://localhost:5001/status?id=" + str(self.exp_id)) as url:
                    response = json.loads(url.read().decode())
                    status = response['status']
            except URLError:
                return

        # Get the test set
        dataset_config = self.config['datasets'][exp['dataset']]

        # Load the dataset
        loader = loader_instance(dataset_config['format'])
        ratings = loader.load(dataset_config['path'])

        # Split the dataset
        splitter = splitter_instance(exp['splitter'], exp['test_size'], exp['seed'])
        training_set, test_set = splitter.split(ratings)

        # Query the recommender
        request_set = []

        for rating in test_set:
            request_set.append([rating[0], rating[1]])

        request = Request("http://localhost:5001/predict_all?id=" + str(self.exp_id))
        request.add_header('Content-Type', 'application/json; charset=utf-8')
        request_json = json.dumps(request_set).encode('utf-8')
        request.add_header('Content-Length', len(request_json))
        try:
            response = urlopen(request, request_json)
        except URLError:
            return
        predictions = json.loads(response.read().decode())

        print(predictions)

        # Clear the model
        try:
            urlopen("http://localhost:5001/clear?id=" + str(self.exp_id))
        except URLError:
            pass
