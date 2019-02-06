[![Build Status](https://travis-ci.com/dorpvom/mettinizr.svg?branch=master)](https://travis-ci.com/dorpvom/mettinizr)
[![Coverage Status](https://coveralls.io/repos/github/dorpvom/mettinizr/badge.svg?branch=master)](https://coveralls.io/github/dorpvom/mettinizr?branch=master)

Here be dragons

## Setup:
Assuming you have python3 and pip3 installed.

```sh
(sudo mkdir -p /data/mett/mett_store && sudo chown -R $USER:$GROUP /data/mett)
sudo apt-get install -f gcc libpython3-dev mongodb-server
sudo -EH pip3 install -r requirements.txt
```

Alternatively you can use the given Dockerfile to build a running instance. Note that to persist results accross container builds, you have to share a host folder to `/data/mett`.
Use docker like this:

```sh
docker build -t mett .
docker run -d -v <path_on_host>:/data/mett -p 8000:5000 mett
```

The application will be served at port 8000 on your host. Note that app will not be at `:8000/` but `:8000/mett/`.

## Configuration

All important configuration can be found in the `src/config` folder.

- app.config: general options
  - behind_proxy, proxy_suffix: control if served under root (`/`) or subpath (e.g. `mett`)
  - user_database: path to user database file. **note:** keep the `sqlite:///` prefix
- uwsgi.config vs. proxy.config (both nearly identical)
  - use *proxy.config* combined with *behind_proxy=true* to make uwsgi recognize subpath serving
  - mount in *proxy.config*: change `mett` to same as *proxy_suffix* if latter was changed before
- mongo.config: database configuration
  - dbPath: filesystem path to database directory
  - **note:** file will only take effect if mongod is started by hand or service is modified

## Start:

Manually start application with:

```sh
(cd src && uwsgi --ini config/uwsgi.config)
```

## Test

After installing run tests with

```sh
py.test
```

pylint is configured as well. Run with

Some code lent from [FACT_core](https://github.com/fkie-cad/FACT_core) licensed under [GPL v3](https://github.com/fkie-cad/FACT_core/blob/master/LICENSE).
Web Content is designed using [Bootstrap](https://getbootstrap.com/) and [jQuery](https://jquery.com/).
