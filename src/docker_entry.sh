#!/bin/sh

mkdir -p /data/mett/mett_store || true

mongod --fork --syslog --config config/mongo.config
python3 create_initial_user.py
uwsgi --ini config/proxy.config

exit 0
