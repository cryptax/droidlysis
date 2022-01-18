#!/usr/bin/env python3
# $Source$
"""
__author__ = "Axelle Apvrille"
__license__ = "MIT License"
"""
import os
import droidproperties
import droidutil
import xml.dom.minidom
import re

class droidversion:
    """A small class to hold different versions of Android"""
    def __init__(self, versionstring, apilevel, codename=''):
        self.codename = codename
        self.version = versionstring
        self.apilevel = apilevel

    def __str__(self):
        return "Android %s - %s (API level %d)" % (versionstring, codename, apilevel)
  
versions = [ droidversion( '1.0', 1 ),
             droidversion( '1.1', 2 ),
             droidversion( '1.5', 3, 'Cupcake' ),
             droidversion( '1.6', 4, 'Donut' ),
             droidversion( '2.0', 5, 'Eclair' ),
             droidversion( '2.0.1', 6, 'Eclair'),
             droidversion( '2.1', 7, 'Eclair'),
             droidversion( '2.2', 8, 'Froyo'),
             droidversion( '2.3', 9, 'Gingerbread'),
             droidversion( '2.3.3', 10, 'Gingerbread'),
             droidversion( '3.0', 11, 'Honeycomb'),
             droidversion( '3.1', 12, 'Honeycomb'),
             droidversion( '3.2', 13, 'Honeycomb'),
             droidversion( '4.0', 14, 'Ice Cream Sandwich'),
             droidversion( '4.0.3', 15, 'Ice Cream Sandwich'),
             droidversion( '4.1', 16, 'Jelly Bean'),
             droidversion( '4.2', 17, 'Jelly Bean'),
             droidversion( '4.3', 18, 'Jelly Bean'),
             droidversion( '4.4', 19, 'KitKat'),
             droidversion( '5.0', 21, 'Lollipop'),
             droidversion( '5.1', 22, 'Lollipop'),
             droidversion( '6.0', 23, 'Marshmallow'),
             droidversion( '7.0', 24, 'Nougat'),
             droidversion( '7.1', 25, 'Nougat'),
             droidversion( '8.0', 26, 'Oreo'),
             droidversion( '8.1', 27, 'Oreo'),
             droidversion( '9.0', 28, 'Pie'),
             droidversion( '10.0', 29, 'Q'),
             droidversion( '11.0', 30, 'R'),
             ]

# ------------------------------------------------------

class droidreport:
    def __init__(self, sample, console=True, report_to_file=True):
        # console means we want to display the result on the console
        # report file means we want to dump in the report file
        self.sample = sample
        self.console = console
        self.report_to_file = report_to_file
        

    def write(self, report_file, verbose=True):
        if verbose:
            print( "Writing report to " + report_file)
        if self.report_to_file:
            self.reportfile = open(report_file, 'w')
            self.reportfile.write("# %s\n\n" % (self.sample.properties.sha256))

        self.write_properties()

        if self.report_to_file:
            self.reportfile.close()

    def write_file(self, message):
        if self.report_to_file:
            self.reportfile.write(message)

    def write_console(self, message):
        if self.console:
            print(message)

    def write_properties(self):
        # Header / File info
        print("\033[1;36;1m============= Report ============\033[0m")
        self.write_file("{0:20.20}: {1}\n".format('Sanitized basename', self.sample.properties.sanitized_basename))
        self.write_console("{0:20.20}: \033[1;37;1m{1}\033[0m".format('Sanitized basename', self.sample.properties.sanitized_basename))
        
        self.write_file("{0:20.20}: {1}\n".format('SHA256', self.sample.properties.sha256))
        self.write_console("{0:20.20}: \033[1;37;1m{1}\033[0m".format('SHA256', self.sample.properties.sha256))

        self.write_file("{0:20.20}: {1} bytes\n".format('File size', self.sample.properties.file_size))
        self.write_console("{0:20.20}: \033[1;37;1m{1}\033[0m bytes".format('File size', self.sample.properties.file_size))

        self.write_file("{0:20.20}: {1}\n".format('Is small', self.sample.properties.file_small))
        self.write_console("{0:20.20}: \033[1;37;1m{1}\033[0m".format('Is small', self.sample.properties.file_small))

        self.write_file("{0:20.20}: {1}\n".format('Nb of classes', self.sample.properties.file_nb_classes))
        self.write_console("{0:20.20}: \033[1;37;1m{1}\033[0m".format('Nb of classes', self.sample.properties.file_nb_classes))

        self.write_file("{0:20.20}: {1}\n".format('Nb of directories', self.sample.properties.file_nb_dir))
        self.write_console("{0:20.20}: \033[1;37;1m{1}\033[0m".format('Nb of dirs', self.sample.properties.file_nb_dir))


        # Certificate properties
        self.write_file("\nCertificate properties:\n")
        self.write_console("\n\033[0;30;47mCertificate properties\033[0m")
        
        for key in self.sample.properties.certificate.keys():
            if self.sample.properties.certificate[key] is not False:
                self.write_console("{0:20.20}: \033[1;36;1m{1}\033[0m".format(key, self.sample.properties.certificate[key] ))
            self.write_file("{0:20.20}: {1}\n".format(key, self.sample.properties.certificate[key] ))

        # Manifest properties
        self.write_file("\nManifest properties:\n")
        self.write_console("\n\033[0;30;47mManifest properties\033[0m")
        for key in self.sample.properties.manifest.keys():
            if self.sample.properties.manifest[key] is not False and self.sample.properties.manifest[key] is not None and self.sample.properties.manifest[key] :
                self.write_file("{0:20.20}: {1}\n".format(key, self.sample.properties.manifest[key] ))
                self.write_console("{0:20.20}: \033[1;36;1m{1}\033[0m".format(key, self.sample.properties.manifest[key] ))
            else:
                self.write_file("{0:20.20}: {1}\n".format(key,     self.sample.properties.manifest[key] ))


        # Smali properties
        self.write_file("\nSmali properties\n")
        self.write_console("\n\033[0;30;47mSmali properties /  What the Dalvik code does\033[0m")
        for section in self.sample.properties.smali.keys():
            if self.sample.properties.smali[section] is not False:
                if (type(self.sample.properties.smali[section]) is list and len(self.sample.properties.smali[section]) > 0) or (type(self.sample.properties.smali[section]) is bool):
                    self.write_console("{0:20.20}: \033[1;31;1m{1} \033[1;33;40m({2})\033[0m".format(section, self.sample.properties.smali[section], self.sample.properties.smaliconfig.get_description(section)))
                    self.write_file("{0:20.20}: {1} ({2})\n".format(section, self.sample.properties.smali[section], self.sample.properties.smaliconfig.get_description(section)))
            else:
                self.write_file("{0:20.20}: {1}\n".format(section, self.sample.properties.smali[section]))

        # Wide properties
        self.write_file("\nWide properties\n")
        self.write_console("\n\033[0;30;47mWide properties /  What Resources/Assets do\033[0m")
        for section in self.sample.properties.wide.keys():
            if self.sample.properties.wide[section] is not False and self.sample.properties.wide[section] is not None and self.sample.properties.wide[section]:
                if self.sample.properties.wideconfig.get_description(section) is not None:
                    self.write_console("{0:20.20}: \033[1;31;1m{1} \033[1;33;40m({2})\033[0m".format(section, self.sample.properties.wide[section], self.sample.properties.wideconfig.get_description(section)))
                    self.write_file("{0:20.20}: {1} ({2})\n".format(section, self.sample.properties.wide[section], self.sample.properties.wideconfig.get_description(section)))
                else:
                    self.write_console("{0:20.20}: \033[1;31;1m{1}\033[0m".format(section, self.sample.properties.wide[section]))
                    self.write_file("{0:20.20}: {1}\n".format(section, self.sample.properties.wide[section]))
            else:
                # case where the property is False, or None.
                self.write_file("{0:20.20}: {1}\n".format(section, self.sample.properties.wide[section]))

        # ARM properties
        self.write_file("\nARM properties\n")
        self.write_console("\n\033[0;30;47mARM properties /  What native ARM libraries do\033[0m")
        for section in self.sample.properties.arm.keys():
            if self.sample.properties.arm[section] is not False and self.sample.properties.arm[section] is not None:
                if self.sample.properties.armconfig.get_description(section) is not None:
                    self.write_console("{0:20.20}: \033[1;31;1m{1} \033[1;33;40m({2})\033[0m".format(section, self.sample.properties.arm[section], self.sample.properties.armconfig.get_description(section)))
                    self.write_file("{0:20.20}: {1} ({2})\n".format(section, self.sample.properties.arm[section], self.sample.properties.armconfig.get_description(section)))
                else:
                    self.write_console("{0:20.20}: \033[1;31;1m{1}\033[0m".format(section, self.sample.properties.arm[section]))
                    self.write_file("{0:20.20}: {1}\n".format(section, self.sample.properties.arm[section]))
            else:
                # case where the property is False, or None.
                self.write_file("{0:20.20}: {1}\n".format(section, self.sample.properties.arm[section]))

        # DEX properties
        self.write_file("\nDEX properties\n")
        self.write_console("\n\033[0;30;47mDEX properties /  About classes.dex format\033[0m")
        for section in self.sample.properties.dex.keys():
            if self.sample.properties.dex[section] is not False and self.sample.properties.dex[section] is not None:
                self.write_console("{0:20.20}: \033[1;31;1m{1} \033[0m".format(section, self.sample.properties.dex[section]))
                self.write_file("{0:20.20}: {1}\n".format(section, self.sample.properties.dex[section]))
            else:
                # case where the property is False, or None.
                self.write_file("{0:20.20}: {1}\n".format(section, self.sample.properties.dex[section]))
                
        # Kits properties
        self.write_file("\nKit properties\n")
        self.write_console("\n\033[0;30;47mKit properties /  Detected 3rd party SDKs\033[0m")
        for section in self.sample.properties.kits.keys():
            if self.sample.properties.kits[section] is not False and self.sample.properties.kits[section] is not None:
                if self.sample.properties.kitsconfig.get_description(section) is not None:
                    self.write_console("{0:20.20}: \033[1;31;1m{1} \033[1;33;40m({2})\033[0m".format(section, self.sample.properties.kits[section], self.sample.properties.kitsconfig.get_description(section)))
                    self.write_file("{0:20.20}: {1} ({2})\n".format(section, self.sample.properties.kits[section], self.sample.properties.kitsconfig.get_description(section)))
                else:
                    self.write_console("{0:20.20}: \033[1;31;1m{1}\033[0m".format(section, self.sample.properties.kits[section]))
                    self.write_file("{0:20.20}: {1}\n".format(section, self.sample.properties.kits[section]))
            else:
                # case where the property is False, or None.
                self.write_file("{0:20.20}: {1}\n".format(section, self.sample.properties.kits[section]))
        
