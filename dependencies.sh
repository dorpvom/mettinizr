#!/usr/bin/env bash

(mkdir src/app/static 2> /dev/null) || true

# Fontawesome Icons
if [ ! -d  src/app/static/fontawesome-free-5.13.0-web ]
then
  wget https://use.fontawesome.com/releases/v5.13.0/fontawesome-free-5.13.0-web.zip
  unzip fontawesome-free-5.13.0-web.zip -d src/app/static
  rm -f fontawesome-free-5.13.0-web.zip
else
  echo "Fontawesome up to date"
fi

# Bootstrap4 Theme
if [ ! -d src/app/static/bootstrap-4.2.1-dist ]
then
  wget https://github.com/twbs/bootstrap/releases/download/v4.2.1/bootstrap-4.2.1-dist.zip
  unzip bootstrap-4.2.1-dist.zip -d src/app/static
  rm -f bootstrap-4.2.1-dist.zip
else
  echo "Boostrap up to date"
fi

# Datepicker
if [ ! -d src/app/static/datepicker ]
then
  wget https://github.com/uxsolutions/bootstrap-datepicker/releases/download/v1.8.0/bootstrap-datepicker-1.8.0-dist.zip
  unzip bootstrap-datepicker-1.8.0-dist.zip -d src/app/static/datepicker
  rm -f bootstrap-datepicker-1.8.0-dist.zip
else
  echo "Datepicker up to date"
fi

# jQuery
if [ ! -d src/app/static/jquery ]
then
  (mkdir src/app/static/jquery 2> /dev/null) || true
  wget https://code.jquery.com/jquery-3.5.0.min.js -O src/app/static/jquery/jquery-3.5.0.min.js
  wget https://code.jquery.com/jquery-3.5.0.min.map -O src/app/static/jquery/jquery-3.5.0.min.map
else
  echo "jQuery up to date"
fi

# Popper
if [ ! -d src/app/static/popper ]
then
  (mkdir src/app/static/popper 2> /dev/null) || true
  wget https://cdnjs.cloudflare.com/ajax/libs/popper.js/2.4.0/umd/popper.min.js -O src/app/static/popper/popper.min.js
else
  echo "Popper.js up to date"
fi