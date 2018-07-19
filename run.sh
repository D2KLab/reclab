export PYTHONPATH="${PYTHONPATH}:$(pwd)"

source venv/bin/activate

gunicorn -b 127.0.0.1:6000 main:app &>> log.txt &

cd recommenders

gunicorn -b 127.0.0.1:6001 random_rec:app &>> ../log.txt &
gunicorn -b 127.0.0.1:6002 most_popular:app &>> ../log.txt &
gunicorn -b 127.0.0.1:6003 itemknn:app &>> ../log.txt &
gunicorn -b 127.0.0.1:6004 userknn:app &>> ../log.txt &
gunicorn -b 127.0.0.1:6005 bprmf:app &>> ../log.txt &
gunicorn -b 127.0.0.1:6006 wrmf:app &>> ../log.txt &

