# DroidLysis

DroidLysis is a **property extractor for Android apps**.
It automatically disassembles the Android application and looks for various properties within the package or its disassembly.

**Just moved to Python 3**. It works, but expect a few bugs...

## Install

### Requirements

- Python 3
- python-setuptools
-  **rarfile** Python library from https://github.com/markokr/rarfile (or `python3-rarfile`)
-  **unrar**: `apt-get install unrar-free`
-  **python3-magic** >= 0.4.6 from https://github.com/ahupp/python-magic
- **apktool** https://ibotpeaches.github.io/Apktool/
- **baksmali** https://bitbucket.org/JesusFreke/smali/downloads
- **dex2jar** https://github.com/pxb1988/dex2jar
- **procyon** https://bitbucket.org/mstrobel/procyon/wiki/Java%20Decompiler
- AXMLPrinter2.jar https://code.google.com/p/android4me/
- Java >= 1.7.0
- SQLAlchemy: `easy_install SQLAlchemy` or `pip install SQLAlchemy` or `apt-get install python3-sqlalchemy`

### Configuration

Configure `droidconfig.py`
Set the appropriate directory for each tool: APKTOOL_JAR, AXMLPRINTER_JAR etc.
Example:

```python
APKTOOL_JAR = os.path.join( os.path.expanduser("~/softs"), "apktool_2.3.0.jar")
```

This tells DroidLysis to use Apktool from `~/softs/apktool_2.3.0.jar`.


## Usage

Usage: `python ./droidlysis3.py --help`.
The most typical usage is: `python ./droidlysis.py --input yourapk --output ./outdir`.
Where this will analyze your APK (`yourapk`) and put the result of the analysis as a subdirectory of `./outdir`.

