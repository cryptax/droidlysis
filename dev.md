# Dev notes

Testing in a Docker container:

```
$ docker run -it --rm alpine:latest /bin/sh
/ # apk add bash python3 py3-setuptools py3-pip git
/ # pip3 install virtualenv
/ # python3 -m venv droidlysis
/ # cd droidlysis/
/droidlysis # source ./bin/activate
(droidlysis) /droidlysis # pip3 install --upgrade pip
(droidlysis) /droidlysis # pip3 install --extra-index-url https://testpypi.python.org/pypi --no-deps droidlysis
```
