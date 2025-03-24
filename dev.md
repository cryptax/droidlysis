# Dev notes

## Testing the git in a Docker container

```
$ docker run -it --rm ubuntu:latest /bin/bash
# apt update
# apt-get install default-jre git python3 python3-pip unzip wget libmagic-dev libxml2-dev libxslt-dev
# mkdir -p ~/softs
# cd ~/softs
# wget https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.11.1.jar
# wget https://bitbucket.org/JesusFreke/smali/downloads/baksmali-2.5.2.jar
# wget https://github.com/pxb1988/dex2jar/releases/download/v2.4/dex-tools-v2.4.zip
# unzip dex-tools-2.4.zip 
# rm -f dex-tools-2.4.zip 
# pip3 install -U pip
# git clone https://github.com/cryptax/droidlysis
# cd droidlysis
# pip3 install -r requirements.txt
```

## Packaging

https://packaging.python.org/en/latest/tutorials/packaging-projects/

Update packages:

```
python3 -m pip install --upgrade pip
python3 -m pip install --upgrade build
python3 -m pip install --upgrade twine
```

Then build:

```
python3 -m build
```

Upload the package to test:

```
python3 -m twine upload --repository testpypi dist/*
```

### Testing the package in a python virtual environment

From github repo:

```
cd /tmp
python3 -m venv ./droid-test
source ./droid-test/bin/activate
pip3 install git+https://github.com/cryptax/droidlysis
```

From test pypi:
```
cd /tmp
python3 -m venv ./droid-test
source ./droid-test/bin/activate
pip3 install -i https://test.pypi.org/simple/ droidlysis
```

You might need to install the requirements...

```
which droidlysis
droidlysis --version
```

Run droidlysis using default config from Python virtual environment: 

```
droidlysis --config ./lib/python3.10/site-packages/conf/general.conf --input yourapk.apk --output /tmp/outputdir
```


### Testing the package in a Docker container

In Alpine:

```
$ docker run -it --rm alpine:latest /bin/sh
/ # apk add bash python3 py3-setuptools py3-pip git libxml2 libxslt-dev
# pip3 install --upgrade pip
# pip3 install --extra-index-url https://testpypi.python.org/pypi --no-deps droidlysis

```

Or with Ubuntu:

```
docker run -it --rm ubuntu:latest /bin/bash
# apt update
# apt install python3 python3-pip python3-venv
# pip3 install --upgrade pip
# python3 -m venv droidlysis
# pip3 install --extra-index-url https://testpypi.python.org/pypi --no-deps droidlysis
```

### Final upload

When ready, upload on the real pypi: `twine upload dist/*`

Make sure to use ~/.pypirc with API token.

