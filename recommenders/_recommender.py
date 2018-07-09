from flask import request
from flask_restful import Resource, abort


class Model(Resource):

    def __init__(self, models, models_lock, phases, phases_lock, trainer):
        self.models = models
        self.models_lock = models_lock
        self.phases = phases
        self.phases_lock = phases_lock
        self.trainer = trainer

    def get(self, exp_id):
        self.phases_lock.acquire()

        if exp_id not in self.phases:
            self.phases_lock.release()
            abort(404)

        result = {'id': exp_id,
                  'status': self.phases[exp_id]}
        self.phases_lock.release()

        return result

    def post(self, exp_id):
        content = request.json
        if content is None:
            abort(400)

        try:
            content['callback']
        except KeyError:
            abort(400)

        try:
            threshold = float(content['threshold'])
            if threshold < 0:
                abort(400)
        except (KeyError, ValueError):
            abort(400)

        threshold = float(content['threshold'])

        self.phases_lock.acquire()
        if exp_id in self.phases:
            self.phases_lock.release()
            abort(400)

        self.phases[exp_id] = "training"
        self.phases_lock.release()

        self.trainer(exp_id, content['callback'], threshold).start()

        return {'id': exp_id,
                'callback': content['callback'],
                'threshold': threshold,
                'status': "training"}, 202

    def delete(self, exp_id):
        self.phases_lock.acquire()

        if exp_id not in self.phases:
            self.phases_lock.release()
            abort(404)

        if self.phases[exp_id] != "ready":
            result = {'id': exp_id,
                      'status': self.phases[exp_id]}
            self.phases_lock.release()
            return result, 405

        self.models_lock.acquire()

        del self.phases[exp_id]
        del self.models[exp_id]

        self.phases_lock.release()
        self.models_lock.release()

        return {'id': exp_id,
                'status': "deleted"}


class Recommendation(Resource):

    def __init__(self, models, models_lock, phases, phases_lock, recommender):
        self.models = models
        self.models_lock = models_lock
        self.phases = phases
        self.phases_lock = phases_lock
        self.recommender = recommender

    def get(self, exp_id):
        self.phases_lock.acquire()
        if exp_id not in self.phases:
            self.phases_lock.release()
            abort(404)

        if self.phases[exp_id] == "recommending":
            self.phases_lock.release()
            return {'id': exp_id,
                    'status': "recommending"}

        self.phases_lock.release()

        self.models_lock.acquire()
        if exp_id not in self.models:
            self.models_lock.release()
            abort(404)

        if self.models[exp_id]['recommendations'] is None:
            self.models_lock.release()
            abort(404)

        recommendations = self.models[exp_id]['recommendations']
        self.models_lock.release()

        return {'id': exp_id,
                'status': "ready",
                'recommendations': recommendations}

    def post(self, exp_id):
        k = request.args.get("k")
        if k is None:
            abort(400)

        try:
            k = int(k)
        except ValueError:
            abort(400)

        if k <= 0:
            abort(400)

        user_set = request.json
        if user_set is None:
            abort(400)

        self.phases_lock.acquire()

        if exp_id not in self.phases:
            self.phases_lock.release()
            abort(404)

        if self.phases[exp_id] != "ready":
            result = {'id': exp_id,
                      'status': self.phases[exp_id]}
            self.phases_lock.release()
            return result, 405

        self.phases[exp_id] = "recommending"
        self.phases_lock.release()

        self.recommender(exp_id, user_set, k).start()

        return {'id': exp_id,
                'status': "recommending"}, 202

    def delete(self, exp_id):
        self.phases_lock.acquire()

        if exp_id not in self.phases:
            self.phases_lock.release()
            abort(404)

        if self.phases[exp_id] != "ready":
            result = {'id': exp_id,
                      'status': self.phases[exp_id]}
            self.phases_lock.release()
            return result, 405

        self.models_lock.acquire()

        self.models[exp_id]['recommendations'] = None

        self.phases_lock.release()
        self.models_lock.release()

        return {'id': exp_id,
                'status': "deleted"}
