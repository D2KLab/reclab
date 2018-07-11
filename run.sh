export PYTHONPATH="${PYTHONPATH}:$(pwd)"

source venv/bin/activate

gunicorn -b 127.0.0.1:5000 main:app &

cd recommenders

gunicorn -b 127.0.0.1:5001 random_rec:app &
gunicorn -b 127.0.0.1:5002 most_popular:app &
gunicorn -b 127.0.0.1:5003 itemknn:app &
gunicorn -b 127.0.0.1:5004 userknn:app &
gunicorn -b 127.0.0.1:5005 bprmf:app &
gunicorn -b 127.0.0.1:5006 wrmf:app &
