ARG PYTHON_VERSION=3.9-slim-buster
FROM python:${PYTHON_VERSION} as build
WORKDIR /opt
RUN apt-get update && apt-get install -yqq libxml2-dev libxslt-dev libmagic-dev git
RUN git clone https://github.com/cryptax/droidlysis
ENV PATH="$PATH:/root/.local/bin"
ENV PYTHONPATH=$PYTHONPATH:/opt/droidlysis
RUN cd /opt/droidlysis && pip3 install -U pip && pip3 install --user -r requirements.txt
