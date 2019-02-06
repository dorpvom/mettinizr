#!/bin/sh

mongod --fork --syslog --config config/mongo.config
python3 create_initial_user.py
uwsgi --ini config/uwsgi.config

exit 0