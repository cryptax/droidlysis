ARG PYTHON_VERSION=3.9.4-buster
FROM python:${PYTHON_VERSION} as build

MAINTAINER Axelle Apvrille
ENV REFRESHED_AT 2022-01-18
ENV APKTOOL_VERSION "2.6.0"
ENV SMALI_VERSION "2.5.2"

WORKDIR /opt

RUN apt-get update && apt-get install -yqq default-jre libxml2-dev libxslt-dev libmagic-dev git wget
RUN pip3 install -U pip wheel
RUN mkdir -p /share

# Apktool ----------------------------------------------
RUN cd /opt && wget -q "https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_${APKTOOL_VERSION}.jar"

# Install Smali / Baksmali -------------------------
RUN wget -q "https://bitbucket.org/JesusFreke/smali/downloads/baksmali-${SMALI_VERSION}.jar"

# Install DroidLysis ----------------------------------
RUN git clone https://github.com/cryptax/droidlysis
ENV PATH $PATH:/root/.local/bin
ENV PYTHONPATH $PYTHONPATH:/opt/droidlysis
RUN cd /opt/droidlysis && pip3 install --user -r requirements.txt

# Configure ---------------------------------------------
RUN sed -i 's/~\/softs/\/opt/g' /opt/droidlysis/droidconfig.py
RUN sed -i "s/apktool_\(.*\).jar/apktool_${APKTOOL_VERSION}.jar/g" /opt/droidlysis/droidconfig.py
RUN sed -i "s/baksmali-\(.*\).jar/baksmali-${SMALI_VERSION}.jar/g" /opt/droidlysis/droidconfig.py

CMD [ "/bin/bash" ]
