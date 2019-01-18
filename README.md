Here be dragons

## Setup:
Assuming you have python3 and pip3 installed.

```sh
(sudo mkdir -p /data/mett && sudo chown -R $USER:$USER /data/mett)
sudo apt-get install -f gcc libpython3-dev mongodb-server
sudo -EH pip3 install -r requirements.txt
```

## Start:
```sh
(cd src && uwsgi --ini config/uwsgi.config)
```

Some code lent from [FACT_core](https://github.com/fkie-cad/FACT_core) licensed under [GPL v3](https://github.com/fkie-cad/FACT_core/blob/master/LICENSE).
Web Content is designed using [Bootstrap](https://getbootstrap.com/) and [jQuery](https://jquery.com/).