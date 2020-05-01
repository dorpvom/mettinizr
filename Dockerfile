FROM phusion/baseimage:0.11

WORKDIR /opt/app

COPY . /opt/app

RUN apt-get update && install_clean \
    python3 python3-pip \
    python3-setuptools \
    python3-distutils gcc \
    libpython3-dev mongodb-server

RUN pip3 install wheel

RUN pip3 install -r requirements.txt

RUN ./dependencies.sh

WORKDIR /opt/app/src

CMD ["./docker_entry.sh"]
