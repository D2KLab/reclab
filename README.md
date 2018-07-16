# RecLab

RecLab is a REST-based offline evaluation framework for recommender systems developed in Python.

## Architecture

RecLab consists of a main application, that manages the interaction with the users and the evaluation process, and a set
of recommender systems. The recommender systems available in this repository are provided for demonstrative purposes.
Everyone is free to implement other recommenders that follows the protocol of RecLab and to deploy them on their own
server. The list of recommenders is available in the _config.json_ file.

## Installation

```bash
$ pip install -r requirements.txt
```

## Usage

```bash
$ ./run.sh
```
