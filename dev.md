# Dev notes

## Testing the git in a Docker container

```
$ docker run -it --rm ubuntu:latest /bin/bash
# sudo apt-get install default-jre git python3 python3-pip unzip wget libmagic-dev libxml2-dev libxslt-dev
# mkdir -p ~/softs
# cd ~/softs
# wget https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.5.0.jar
# wget https://bitbucket.org/JesusFreke/smali/downloads/baksmali-2.5.2.jar
# wget https://github.com/pxb1988/dex2jar/files/1867564/dex-tools-2.1-SNAPSHOT.zip
# unzip dex-tools-2.1-SNAPSHOT.zip
# rm -f dex-tools-2.1-SNAPSHOT.zip
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

```
cd /tmp
python3 -m venv ./droid-test
source ./droid-test/bin/activate
pip install androguard==3.3.5
pip install -i https://test.pypi.org/simple/ droidlysis
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
