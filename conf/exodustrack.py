#!/usr/bin/env python3

"""
__author__ = "Axelle Apvrille"
__license__ = "MIT License"
"""

import argparse
import requests
import configparser
import json
import re

__version__ = '0.1.0'

def get_arguments():
    parser =  argparse.ArgumentParser(description="Import missing Exodus Trackers in DroidLysis Kits", prog='exodustrack', epilog='Version '+__version__+' - Greetz from Axelle Apvrille')
    parser.add_argument('-i', '--input', help='DroidLysis kit.conf file', action='store', default='./kit.conf')
    parser.add_argument('-v', '--verbose', help='get more detailed messages', action='store_true')
    args = parser.parse_args()
    return args

def get_exodus_trackers(verbose=False):
    r = requests.get('https://etip.exodus-privacy.eu.org/trackers/export',timeout=2)
    assert r.status_code == 200, "Cannot retrieve Exodus Trackers JSON"
    if verbose:
        print("get_exodus_trackers(): status={}".format(r.status_code))
    return r.json()['trackers']

def conf2json(kitfile='./conf/kit.conf', verbose=False):
    parser = configparser.RawConfigParser()
    parser.read(kitfile)
    thelist = []
    for section in parser.sections():
        pattern = parser.get(section, 'pattern')
        try:
            description = parser.get(section, 'description')
        except configparser.NoOptionError as e:
            if verbose:
                print("config2json(): section {} has no description".format(section))
            description = ''
            
        thelist.append( { "section" : section, "pattern" : pattern, "description" : description } )
    return json.loads(json.dumps(thelist))

def compare(exodus, droidlysis, verbose=False):
    # we are going to suggestion addition of any tracker in exodus that is not in droidlysis
    for tracker in exodus:
        if tracker['code_signature'] == '':
            if verbose:
                print("compare(): {} has no code_signature".format(tracker['name']))
        else:
            # convert . to /
            # remove leading and trailing spaces
            # remove trailing /
            # only consider the first pattern when separated by |
            sig = tracker['code_signature'].split('|')[0].replace('.','/').strip().strip('/')
            assert (' ' in sig) == False, "There is a space in sig"
                      
            # search droidlysis patterns
            found = False
            for item in droidlysis:
                for p in item['pattern'].split('|'):
                    if item['pattern'].startswith(sig) or sig.startswith(p):
                        if verbose:
                            print("compare(): {} (sig={}) found in {} (pattern={})".format(tracker['name'],sig, item['section'], p))
                        found = True
                        break

            if not found:
                # this is what you should consider adding
                section_name = ''.join(re.findall('[a-z0-9]',tracker['name'].lower()))
                print("[{}]".format(section_name))
                print("pattern={}".format(sig))
                print("")
            

def main():
    args = get_arguments()
    exodus = get_exodus_trackers(args.verbose)
    droidlysis = conf2json(args.input, args.verbose)
    compare(exodus, droidlysis, args.verbose)
            
if __name__ == "__main__":
    main()
        


