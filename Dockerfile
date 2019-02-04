FROM phusion/baseimage:0.11

WORKDIR /opt/app

COPY . /opt/app

RUN apt-get update && install_clean \
    python3 python3-pip \
    python3-setuptools \
    python3-distutils gcc \
    libpython3-dev mongodb-server

RUN pip3 install -r requirements.txt

RUN mkdir -p /data/mett && mkdir -p /data/db

RUN mongod --fork --syslog && sleep 2

RUN python3 src/create_initial_user.py

WORKDIR /opt/app/src

CMD ["uwsgi", "--ini", "config/uwsgi.config"]