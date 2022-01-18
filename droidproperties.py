#!/usr/bin/env python3

"""
__author__ = "Axelle Apvrille"
__status__ = "Alpha"
__license__ = "MIT License"
"""

import droidutil
import droidconfig
import droidcountry
import droidsql
import re
import os
import argparse
import json
from sqlalchemy.orm import sessionmaker
import sqlalchemy.exc

"""This is where to set whether given fields have a meaning or not for a given file type"""
applicability = { 'file_size' : [ droidutil.APK, droidutil.DEX, droidutil.ARM, droidutil.CLASS, droidutil.ZIP, droidutil.RAR ], \
                      'file_small' : [ droidutil.APK, droidutil.DEX, droidutil.ARM, droidutil.CLASS, droidutil.ZIP, droidutil.RAR ],\
                      'file_nb_classes' : [ droidutil.APK, droidutil.DEX ],\
                      'file_nb_dir' : [ droidutil.APK, droidutil.DEX ],\
                      'file_innerzips' : [ droidutil.APK, droidutil.ZIP, droidutil.RAR ],\
                      'cert' : [droidutil.APK ],\
                      'manifest' : [droidutil.APK], \
                      'smali' : [droidutil.APK, droidutil.DEX], \
                      'wide' : [droidutil.APK, droidutil.DEX], \
                      'arm' : [droidutil.APK, droidutil.ARM], \
                      'dex' : [droidutil.APK, droidutil.DEX], \
                      'kit' : [droidutil.APK, droidutil.DEX], \
                      }

class droidproperties:
    verbose = False
    """Extracted properties"""

    """Field allocation"""
    certificate = { }
    manifest = { }
    smali = { }
    wide = { }
    arm = { }
    dex = { }
    kits = { }

    def __init__(self, samplename='', sha256='', verbose=False):
        """Properties concern a given sample identified by a basename (to be helpful) and a sha256 (real reference)"""
        self.verbose = verbose
        self.sha256 = sha256
        self.sanitized_basename = samplename
        self.clear_fields()


    def clear_fields(self):
        """Re-initialize all fields of the object - to default values"""
        self.file_nb_classes = 0
        self.file_nb_dir = 0
        self.file_size = 0
        self.file_small = False
        self.filetype = droidutil.UNKNOWN
        self.file_innerzips = False

        self.certificate.clear()
        self.certificate = {  'av' : False, \
                              'algo' : None, \
                              'debug': False, \
                              'dev' : False, \
                              'famous' : False, \
                              'serialno' : None, \
                              'country': droidcountry.country['unknown'],\
                              'owner' : None,\
                              'timestamp' : None, \
                              'year' : 0,\
                              'unknown_country' : False }

        self.manifest.clear()
        self.manifest = {
            'activities' : [], \
            'libraries' : [], \
            'listens_incoming_sms' : False,\
            'listens_outgoing_call' : False,\
            'maxSDK' : 0,\
            'main_activity': None, \
            'minSDK' : 0,\
            'package_name' : None, \
            'permissions' : [], \
            'providers' : [], \
            'receivers' : [], \
            'services' : [], \
            'swf' : False,\
            'targetSDK' : 0 }

        # automatically adding smali properties. 
        self.smali.clear()
        self.smaliconfig = droidconfig.droidconfig(droidconfig.SMALI_CONFIGFILE, self.verbose)
        for section in self.smaliconfig.get_sections():
            self.smali[section] = False

        self.smali['packed'] = False # This property is not in conf section as it is deduced from no main activity + loading DEX dynamically
        self.smali['multidex']= []

        # automatically adding wide properties
        self.wide.clear()
        self.wide['app_name'] = None
        self.wide['phonenumbers'] = []
        self.wide['urls'] = []
        self.wide['base64_strings'] = []
        self.wide['apk_zip_url'] = False
        self.wideconfig = droidconfig.droidconfig(droidconfig.WIDE_CONFIGFILE, self.verbose)
        for section in self.wideconfig.get_sections():
            self.wide[section] = False

        # automatically add ARM properties
        self.arm.clear()
        self.armconfig = droidconfig.droidconfig(droidconfig.ARM_CONFIGFILE, self.verbose)
        for section in self.armconfig.get_sections():
            self.arm[section] = False

        self.dex.clear()
        self.dex = { 'magic' : 0, \
                     'odex' : False, \
                    'magic_unknown' : False,\
                    'bad_sha1' : False,\
                    'bad_adler32' : False,\
                    'big_header': False,\
                    'thuxnder' : False
                    }

        # automatically set to False kit properties
        self.kits.clear()
        self.kitsconfig = droidconfig.droidconfig(droidconfig.KIT_CONFIGFILE, self.verbose)
        for section in self.kitsconfig.get_sections():
            self.kits[section] = False
        
        # END OF reinit to default values

    def write(self):
        Session = sessionmaker(bind=droidsql.engine)
        session = Session()
        sample = droidsql.Sample(sha256=self.sha256, \
                                 sanitized_basename=self.sanitized_basename, \
                                 file_nb_classes=self.file_nb_classes, \
                                 file_nb_dir=self.file_nb_dir,\
                                 file_size=self.file_size,\
                                 file_small=self.file_small,\
                                 filetype=self.filetype,\
                                 file_innerzips=self.file_innerzips,\
                                 manifest_properties=json.dumps(self.manifest), \
                                 smali_properties=json.dumps(self.smali),\
                                 wide_properties=json.dumps(self.wide),\
                                 arm_properties=json.dumps(self.arm),\
                                 dex_properties=json.dumps(self.dex),\
                                 kits=json.dumps(self.kits))
        session.add(sample)
        try:
            session.commit()
        except sqlalchemy.exc.IntegrityError:
            # occurs when the sample with the same sha256 is already in
            if self.verbose:
                print("Sample is already in the database")

    def dump_json(self, filename='report.json'):
        data = { 'sanitized_basename' : self.sanitized_basename, \
                 'file_nb_classes' : self.file_nb_classes, \
                 'file_nb_dir' : self.file_nb_dir, \
                 'file_size' : self.file_size, \
                 'file_small' : self.file_small, \
                 'filetype' : self.filetype, \
                 'file_innerzips' : self.file_innerzips,\
                 'manifest_properties' : self.manifest, \
                'smali_properties' : self.smali,\
                 'wide_properties' : self.wide,\
                 'arm_properties' : self.arm,\
                 'dex_properties' : self.dex,\
                 'kits' : self.kits }
        if self.verbose:
            print("-------------")
            print("Dumping to JSON file {}".format(filename))
        f = open(filename, 'w') 
        f.write(json.dumps(data))
        f.close()
        
                 
        

