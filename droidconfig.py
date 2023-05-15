import os
import configparser
import logging
import shutil
from platformdirs import *


logging.basicConfig(format='%(levelname)s:%(filename)s:%(message)s',
                    level=logging.INFO)


# ------------------------- Reading *.conf configuration files -----------
class generalconfig:
    def __init__(self, filename='./conf/general.conf', verbose=False):
        self.config = configparser.ConfigParser()
        self.config.read(filename)

        # get config
        self.APKTOOL_JAR = os.path.expanduser(self.config['tools']['apktool'])
        self.BAKSMALI_JAR = os.path.expanduser(self.config['tools']['baksmali'])
        self.DEX2JAR_CMD = os.path.expanduser(self.config['tools']['dex2jar'])
        self.PROCYON_JAR = os.path.expanduser(self.config['tools']['procyon'])
        self.KEYTOOL = os.path.expanduser(self.config['tools']['keytool'])
        self.SMALI_CONFIGFILE = os.path.join(os.path.dirname(filename),
                                             self.config['general']['smali_config'])
        self.WIDE_CONFIGFILE = os.path.join(os.path.dirname(filename),
                                            self.config['general']['wide_config'])
        self.ARM_CONFIGFILE = os.path.join(os.path.dirname(filename),
                                           self.config['general']['arm_config'])
        self.DISTRIB_KIT_CONFIGFILE = os.path.join(os.path.dirname(filename),
                                                   self.config['general']['kit_config'])

        # duplicate kit configuration for edition
        cache_dir = user_cache_dir('droidlysis', 'cryptax')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        self.KIT_CONFIGFILE = os.path.join(cache_dir,
                                           self.config['general']['kit_config'])
        if not os.path.exists(self.KIT_CONFIGFILE):
            logging.verbose(f'Copying {self.DISTRIB_KIT_CONFIGFILE}'
                            'to {self.KIT_CONFIGFILE}')
            shutil.copyfile(self.DISTRIB_KIT_CONFIGFILE, self.KIT_CONFIGFILE)

        self.SQLALCHEMY = f'sqlite:///{self.config["general"]["db_file"]}'

        # check files are accessible
        for f in [self.APKTOOL_JAR, self.BAKSMALI_JAR,
                  self.DEX2JAR_CMD, self.PROCYON_JAR,
                  self.SMALI_CONFIGFILE, self.WIDE_CONFIGFILE,
                  self.ARM_CONFIGFILE, self.KIT_CONFIGFILE]:
            if not os.access(f, os.R_OK):
                logging.warning(f'Cannot access {f} - check your configuration file {filename}')

        if not os.access(self.KEYTOOL, os.X_OK):
            logging.warning(f'Cannot access keytool at {self.KEYTOOL} - check your configuration file {filename}')


class droidconfig:
    def __init__(self, filename, verbose=False):
        assert filename is not None, "Filename is invalid"
        assert os.access(filename, os.R_OK) is not False, "File {0} is not readable".format(filename)

        self.filename = filename
        self.configparser = configparser.RawConfigParser()
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Reading configuration file: '%s'" % (filename))
        self.configparser.read(filename)

    def get_sections(self):
        return self.configparser.sections()

    def get_pattern(self, section):
        return self.configparser.get(section, 'pattern')

    def get_description(self, section):
        try:
            return self.configparser.get(section, 'description')
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass
        return None

    def is_pattern_present(self, pattern):
        for section in self.get_sections():
            section_patterns = self.get_pattern(section).split('|')
            if pattern in section_patterns:
                return True
            for p in section_patterns:
                if p in pattern:
                    # our pattern is more generic
                    return True
        return False

    def get_all_regexp(self):
        # reads the config file and returns a list
        # of all patterns for all sections
        # the patterns are concatenated with a |
        # throws NoSectionError, NoOptionError
        allpatterns = ''
        for section in self.configparser.sections():
            if allpatterns == '':
                allpatterns = self.configparser.get(section, 'pattern')
            else:
                allpatterns = self.configparser.get(section, 'pattern') + '|' + allpatterns
        return bytes(allpatterns, 'utf-8')

    def match_properties(self, match, properties):
        """
        Call this when the recursive search has been done to analyze the results
        and understand which properties have been spotted.

        @param match: returned by droidutil.recursive_search. This is a dictionary
        of matching lines ordered by matching keyword (pattern)

        @param properties: dictionary of properties where the key is the property name
        and the value will be False/True if set or not

        throws NoSessionError, NoOptionError
        """
        for section in self.configparser.sections():
            pattern_list = self.configparser.get(section, 'pattern').split('|')
            properties[section] = False
            for pattern in pattern_list:
                # beware when pattern has blah\$binz, the matching key is blah$binz
                if match[pattern.replace('\\', '')]:
                    logging.debug("Setting properties[%s] = True (matches %s)" % (section, pattern))
                    properties[section] = True
                    break

                
