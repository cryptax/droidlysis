ARG PYTHON_VERSION=3.9.4-buster
FROM python:${PYTHON_VERSION} as build

MAINTAINER Axelle Apvrille
ENV REFRESHED_AT 2025-03-24
ENV APKTOOL_VERSION "2.11.1"
ENV SMALI_VERSION "2.5.2"

WORKDIR /opt

RUN apt-get update && apt-get install -yqq default-jre libxml2-dev libxslt-dev libmagic-dev git wget cmake
RUN pip3 install -U pip wheel
RUN mkdir -p /share

# Install Apktool ----------------------------------------------
RUN cd /opt && wget -q "https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_${APKTOOL_VERSION}.jar"

# Install Smali / Baksmali -------------------------
RUN wget -q "https://bitbucket.org/JesusFreke/smali/downloads/baksmali-${SMALI_VERSION}.jar"

# Install Dex2jar -------------------------------------
RUN wget -O dex2jar.zip -q https://github.com/pxb1988/dex2jar/releases/download/v2.4/dex-tools-v2.4.zip && unzip dex2jar.zip -d /opt && rm -f dex2jar.zip

# Install DroidLysis ----------------------------------
RUN git clone https://github.com/cryptax/droidlysis
ENV PATH $PATH:/root/.local/bin
ENV PYTHONPATH $PYTHONPATH:/opt/droidlysis
RUN cd /opt/droidlysis && pip3 install --user -r requirements.txt
RUN chmod u+x /opt/droidlysis/droidlysis

# Configure ---------------------------------------------
RUN sed -i 's#~/softs#/opt#g' /opt/droidlysis/conf/general.conf

CMD [ "/bin/bash" ]
