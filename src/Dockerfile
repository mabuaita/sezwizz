FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

MAINTAINER mabuaita@yahoo.com

# Libraries and dependencies

RUN \
  apt-get update && apt-get -y install \
  libboost-thread-dev \
  libjpeg-dev \
  libopenexr-dev \
  libpng-dev \
  libtiff-dev \
  python3 \
  python3-dev \
  python-distribute \
  python3-pip \
  unzip \
  zlib1g-dev \
  vim

COPY sez_app.py /
COPY requirements.txt /
RUN \
pip3 install -r requirements.txt && pip install redis

EXPOSE 3777/tcp
CMD [ "python3", "sez_app.py" ]
#CMD [ "tail", "-f", "/dev/null" ]
