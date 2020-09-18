# Dev notes

Packaging:
```
python3 setup.py sdist bdist_wheel
python3 -m pip install --user --upgrade twine
python3 -m twine upload --repository testpypi dist/*
```

on pypi: `twine upload dist/*`

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
