FROM python:3.7.2-slim-stretch

LABEL \
  com.yourserveradmin.vendor="IT Craft YSA GmbH" \
  description="Tool to simplify time entries export from Toggl into Project Laboratory" \
  maintainer="pa@yourserveradmin.com" \
  version="${PACKAGE_VERSION}"

COPY dist/${PACKAGE_NAME} /usr/local/bin

CMD ["toggl2pl", "serve"]
