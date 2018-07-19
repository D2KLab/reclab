from threading import Lock

from flask import Flask
from flask_restful import Api

from recommenders import mymedialite

app = Flask(__name__)
api = Api(app)

models = {}
phases = {}

models_lock = Lock()
phases_lock = Lock()

Trainer, Recommender, Model, Recommendation = mymedialite(models, models_lock, phases, phases_lock, "ItemKNN")

api.add_resource(Model, '/model/<int:exp_id>',
                 resource_class_args=(models, models_lock, phases, phases_lock, Trainer))
api.add_resource(Recommendation, '/recommendation/<int:exp_id>',
                 resource_class_args=(models, models_lock, phases, phases_lock, Recommender))


@app.route("/")
def main():
    return "Item KNN"


if __name__ == "__main__":
    app.run(port=6003)
