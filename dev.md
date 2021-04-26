# Dev notes

## Packaging

- check everything you need is in dist/

```
python3 setup.py sdist bdist_wheel
python3 -m pip install --user --upgrade twine
python3 -m twine upload --repository testpypi dist/*
```

## Testing in a Docker container

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

## Final upload

When ready, upload on the real pypi: `twine upload dist/*`
