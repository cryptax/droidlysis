# DroidLysis

DroidLysis is a **pre-analysis tool for Android apps**: it performs repetitive and boring tasks we'd typically do at the beginning of any reverse engineering. It disassembles the Android sample, organizes output in directories, and searches for suspicious spots in the code to look at.
The output helps the reverse engineer speed up the first few steps of analysis.

DroidLysis can be used over Android packages (apk), Dalvik executables (dex), Zip files (zip), Rar files (rar) or directories of files.

<img src="https://img.shields.io/badge/PyPi%20-3.4.1-blue">

## Quick setup

Can't wait to use DroidLysis? Then, use a Docker container:

```
$ docker pull cryptax/droidlysis:2023.02
$ docker run -it --rm -v /tmp/share:/share cryptax/droidlysis:2023.02  /bin/bash
$ cd /opt/droidlysis
$ python3 ./droidlysis3.py --help
```

## Installing DroidLysis

1. Install required system packages
2. Install Android disassembly tools
3. Get DroidLysis from the Git repository (preferred) or from pip
4. Configure `conf/general.conf`

Install required system packages:

```
sudo apt-get install default-jre git python3 python3-pip unzip wget libmagic-dev libxml2-dev libxslt-dev
```

Install Android disassembly tools: [Apktool](https://ibotpeaches.github.io/Apktool/) , 
[Baksmali](https://bitbucket.org/JesusFreke/smali/downloads), and optionally 
[Dex2jar](https://github.com/pxb1988/dex2jar) and  
[Procyon](https://bitbucket.org/mstrobel/procyon/wiki/Java%20Decompiler) (note that Procyon only works with Java 8, not Java 11).

```
$ mkdir -p ~/softs
$ cd ~/softs
$ wget https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.7.0.jar
$ wget https://bitbucket.org/JesusFreke/smali/downloads/baksmali-2.5.2.jar
$ wget https://github.com/pxb1988/dex2jar/releases/download/v2.2-SNAPSHOT-2021-10-31/dex-tools-2.2-SNAPSHOT-2021-10-31.zip
$ unzip dex-tools-2.2-SNAPSHOT-2021-10-31.zip 
$ rm -f dex-tools-2.2-SNAPSHOT-2021-10-31.zip 
```

Install from Git in a Python virtual environment:

```
$ python3 -m venv venv
$ source ./venv/bin/activate
(venv) $ pip3 install git+https://github.com/cryptax/droidlysis
```

Run it:

```
cd droidlysis
./droidlysis --help
```

Alternatively, you can install DroidLysis directly from PyPi (`pip3 install droidlysis`).

## Configuration

If you used the default install commands & directories as specified above, you won't need any configuration. 

The configuration file is `./conf/general.conf` (you can switch to another file with the `--config` option).
This is where you configure the location of various external tools (e.g. Apktool), the name of pattern files 
(by default `./conf/smali.conf`, `./conf/wide.conf`, `./conf/arm.conf`, `./conf/kit.conf`) and the name of
the database file (only used if you specify `--enable-sql`)


## Usage

DroidLysis uses **Python 3**. To launch it and get options:

```
droidlysis --help
```

For example, test it on [Signal's APK](https://signal.org/android/apk/):

```
droidlysis --input Signal-website-universal-release-4.52.4.apk --output /tmp
```

![](./images/example.png)

DroidLysis outputs:

- A summary on the console (see image above)
- The unzipped, pre-processed sample in a subdirectory of your output dir. The subdirectory is named using the sample's filename and sha256 sum. For example, if we analyze the Signal application and set `--output /tmp`, the analysis will be written to `/tmp/Signalwebsiteuniversalrelease4.52.4.apk-f3c7d5e38df23925dd0b2fe1f44bfa12bac935a6bc8fe3a485a4436d4487a290`.
- A database (by default, SQLite `droidlysis.db`) containing properties it noticed.

## Options

Get usage with `droidlysis --help`

- The input can be a file or a directory of files to recursively look into. DroidLysis knows how to process Android packages, DEX, ODEX and ARM executables, ZIP, RAR. DroidLysis won't fail on other type of files (unless there is a bug...) but won't be able to understand the content.

- When processing directories of files, it is typically quite helpful to move processed samples to another location to know what has been processed. This is handled by option `--movein`.  Also, if you are only interested in statistics, you should probably clear the output directory which contains detailed information for each sample: this is option `--clearoutput`. If you want to store all statistics in a SQL database, use `--enable-sql` (see [here](#sqlite_database))

- DEX decompilation is quite long with Procyon, so this option is *disabled* by default. If you want to decompile to Java, use `--enable-procyon`.

- DroidLysis's analysis does not inspect known 3rd party SDK by default, i.e. for instance it won't report any suspicious activity from these. If you want them to be inspected, use option `--no-kit-exception`. This usually creates many more detected properties for the sample, as SDKs (e.g. advertisment) use lots of flagged APIs (get GPS location, get IMEI, get IMSI, HTTP POST...).

## Sample output directory (`--output DIR`)

This directory contains (when applicable):

- A readable `AndroidManifest.xml`
- Readable resources in `res`
- Libraries `lib`, assets `assets`
- Disassembled Smali code: `smali` (and others)
- Package meta information: `META-INF`
- Package contents when simply unzipped in `./unzipped`
- DEX executable `classes.dex` (and others), and converted to jar: `classes-dex2jar.jar`, and unjarred in `./unjarred`

The following files are generated by DroidLysis:

- `autoanalysis.md`: lists each pattern DroidLysis detected and where.
- `report.md`: same as what was printed on the console

If you do not need the sample output directory to be generated, use the option `--clearoutput`.

## SQLite database{#sqlite_database}

If you want to process a directory of samples, you'll probably like to store the properties DroidLysis found in a database, to easily parse and query the findings. In that case, use the option `--enable-sql`. This will automatically dump all results in a database named `droidlysis.db`, in a table named `samples`. Each entry in the table is relative to a given sample. Each column is properties DroidLysis tracks.

For example, to retrieve all filename, SHA256 sum and smali properties of the database:

```
sqlite> select sha256, sanitized_basename, smali_properties from samples;
f3c7d5e38df23925dd0b2fe1f44bfa12bac935a6bc8fe3a485a4436d4487a290|Signalwebsiteuniversalrelease4.52.4.apk|{"send_sms": true, "receive_sms": true, "abort_broadcast": true, "call": false, "email": false, "answer_call": false, "end_call": true, "phone_number": false, "intent_chooser": true, "get_accounts": true, "contacts": false, "get_imei": true, "get_external_storage_stage": false, "get_imsi": false, "get_network_operator": false, "get_active_network_info": false, "get_line_number": true, "get_sim_country_iso": true,
...
```

## Property patterns

What DroidLysis detects can be configured and extended in the files of the `./conf` directory.

A pattern consist of:

- a **tag** name: example `send_sms`. This is to name the property. Must be unique across the `.conf` file.
- a **pattern**: this is a regexp to be matched. Ex: `;->sendTextMessage|;->sendMultipartTextMessage|SmsManager;->sendDataMessage`. In the `smali.conf` file, this regexp is match on Smali code. In this particular case, there are 3 different ways to send SMS messages from the code: sendTextMessage, sendMultipartTextMessage and sendDataMessage.
- a **description** (optional): explains the importance of the property and what it means.

```
[send_sms]
pattern=;->sendTextMessage|;->sendMultipartTextMessage|SmsManager;->sendDataMessage
description=Sending SMS messages
```


## Importing Exodus Privacy Trackers

Exodus Privacy maintains a list of various SDKs which are interesting to rule out in our analysis via `conf/kit.conf`.
Add option `--import_exodus` to the droidlysis command line: this will parse existing trackers Exodus Privacy knows and which aren't yet in your `kit.conf`. Finally, it will **append** all new trackers to `kit.conf`.

Afterwards, you may want to sort your `kit.conf` file:

```python
import configparser
import collections

config = configparser.ConfigParser({}, collections.OrderedDict)
config.read('./conf/kit.conf')
# Order all sections alphabetically
config._sections = collections.OrderedDict(sorted(config._sections.items(), key=lambda t: t[0] ))
with open('sorted.conf','w') as f:
    config.write(f)
```    


## Updates

- v3.4.3 - Using configuration files
- v3.4.2 - Adding import of Exodus Privacy Trackers
- v3.4.1 - Removed dependency to Androguard
- v3.4.0 - Multidex support
- v3.3.1 - Improving detection of Base64 strings
- v3.3.0 - Dumping data to JSON
- v3.2.1 - IP address detection
- v3.2.0 - Dex2jar is optional
- v3.1.0 - Detection of Base64 strings


