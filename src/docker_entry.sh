#!/bin/sh

mongod --fork --syslog
python3 create_initial_user.py
uwsgi --ini config/uwsgi.config

exit 0