FROM python:3.7.2-slim-stretch

LABEL \
  com.yourserveradmin.vendor="IT Craft YSA GmbH" \
  description="Tool to simplify time entries export from Toggl into Project Laboratory" \
  maintainer="pa@yourserveradmin.com"

RUN pip install toggl2pl==1.0.5

CMD ["toggl2pl", "serve"]
