# RecLab

RecLab is a REST-based offline evaluation framework for recommender systems developed in Python.

## Demo

A demo of RecLab is available at [http://datascience.ismb.it/reclab/](http://datascience.ismb.it/reclab/).

## Architecture

RecLab consists of a main application, that manages the interaction with the users and the evaluation process, and a set
of recommender systems. The recommender systems available in this repository are provided for demonstrative purposes.
Everyone is free to implement other recommenders that follows the protocol of RecLab and to deploy them on their own
server. The list of recommenders is available in the _config.json_ file.

## Installation

RecLab requires a MongoDB instance to store the results of the experiments. It is necessary to specify the connection
parameters in the _config.json_ file.

In order to run RecLab, create a new virtual environment, activate it, then install the required packages.

```bash
$ pip install -r requirements.txt
```

For using the recommender based on MyMediaLite, it is necessary to install `mono` and the place the
[MyMediaLite](http://www.mymedialite.net/download/index.html) executables in the folder `./mymedialite`.

## Usage

You can run RecLab and all the included recommenders with the following script.

```bash
$ ./run.sh
```
