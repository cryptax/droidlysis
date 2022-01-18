#!/usr/bin/env python

"""
__author__ = "Axelle Apvrille"
__license__ = "MIT License"
__version__ = '3.4.0'
"""
import hashlib
import base64
import os
import re
import itertools
import sys
import string
import struct
import zlib
import shutil
import subprocess
import xml.dom.minidom
import droidutil
import droidlysis3
import droidconfig
import droidcountry
import droidproperties
import droidziprar
import droidurl
import xml.parsers.expat as expat

class droidsample:
    """Base class for an Android sample to analyze"""
    
    def __init__(self, filename, output='/tmp/analysis', verbose=False, clear=False, enable_procyon=False, disable_description=False, silent=False, no_kit_exception=False):
        """Setup analysis of a given sample. This does not perform the analysis in itself."""

        assert filename != None, "Filename is invalid"

        self.absolute_filename = filename
        self.verbose = verbose
        self.clear = clear
        self.enable_procyon = enable_procyon
        self.disable_description = disable_description # we need those for recursive calls to process_file
        self.silent = silent
        self.no_kit_exception = no_kit_exception
        self.ziprar = None # zip file or rar file file handle

        sanitized_basename = droidutil.sanitize_filename(os.path.basename(filename))
        if not silent:
            print("Filename: "+filename)
        self.properties = droidproperties.droidproperties(samplename=sanitized_basename,\
                                                              sha256=droidutil.sha256sum(filename), \
                                                              verbose=self.verbose)
        if verbose:
            print( "SHA256: %s" % (self.properties.sha256))

        """Computing the SHA1 of a file is only useful to help out the analyst. 
        The digest is written to the automatic analysis/description of the sample. That
        description is located in the output analysis directory, so obviously, if the
        end-user specifies he wants the output analysis directory erased, he obviously
        does not want to know about the SHA1 digest, and thus it's useless to compute it."""
        if not clear: 
            sha1 = droidutil.sha1sum(filename)
            if verbose:
                print( "SHA1: %s" % (sha1))


        # Creating the output analysis directory
        self.outdir = os.path.join(output, '{filename}-{hash}'.format(\
                filename=sanitized_basename,\
                hash=self.properties.sha256))

        if verbose:
            print( "Output analysis directory: " + self.outdir )

        if os.path.exists(self.outdir):
            try:
                shutil.rmtree(self.outdir, ignore_errors=droidutil.on_rm_tree_error)
                os.makedirs(self.outdir)
            except RuntimeError:
                if verbose:
                    print( "Failed to remove directory - rmtree / RuntimeError" )
        else:
            os.makedirs(self.outdir)

        # standard output for shell commands
        if self.verbose:
            self.process_output = None
        else:
            self.process_output = open("/dev/null", 'w')

    def close(self):
        if self.process_output != None:
            self.process_output.close()
        

    def unzip(self):
        """
        This method will unzip/unrar the sample, and recursively unzip/unrar inner zips/rars.
        If we are not removing the analysis directory (clearoutput option), then we also
        unzip the sample in outdir/unzipped subdirectory.
        If the sample is password protected, we try 'infected' as password.
        
        Returns the file type of the sample: droidutil.<FILE CONSTANT> (UNKNOWN, APK, DEX, ...)
        """
        if self.verbose:
            print("------------- Unzipping %s" % (self.absolute_filename))
            
        self.properties.filetype = droidutil.get_filetype(self.absolute_filename)

        if self.properties.filetype == droidutil.ARM or \
           self.properties.filetype == droidutil.UNKNOWN or \
           self.properties.filetype == droidutil.DEX:
            if self.verbose:
                print( "This is a %s. Nothing to unzip for %s" % (droidutil.str_filetype(self.properties.filetype), self.absolute_filename) )
            return self.properties.filetype

        if self.properties.filetype == droidutil.ZIP or \
                self.properties.filetype == droidutil.RAR:
            if self.properties.filetype == droidutil.ZIP:
                self.ziprar = droidziprar.droidziprar(self.absolute_filename, \
                                                          zipmode=True, verbose=self.verbose)
            else:
                self.ziprar = droidziprar.droidziprar(self.absolute_filename, \
                                                          zipmode=False, verbose=self.verbose)
            if self.ziprar.handle == None:
                self.properties.filetype = droidutil.UNKNOWN # damaged zip/rar
                if self.verbose:
                    print( "We are unable to unzip/unrar %s because of errors" % (self.absolute_filename) )
                return droidutil.UNKNOWN
            # Now, we know self.ziprar is valid and open.
            self.properties.filetype, innerzips = self.ziprar.get_type()
            if innerzips:
                self.properties.file_innerzips = True
                if self.verbose:
                    print( "There are inner zips/rars in " + self.absolute_filename )

                for element in innerzips:
                    # extract the inner zip/rar
                    if self.verbose:
                        print( "Extracting " + element + " inside " + self.absolute_filename )
                    try:
                        self.ziprar.extract_one_file(element, self.outdir)
                        if self.verbose:
                            print( "Recursively processing " + os.path.join(self.outdir, element) )
                        droidlysis3.process_file(os.path.join(self.outdir, element), self.outdir, self.verbose, self.clear, self.enable_procyon, self.disable_description, self.no_kit_exception)
                    except:
                        print( "Cannot extract %s : %s" % (element, sys.exc_info()[0]) )
            
        if self.properties.filetype == droidutil.APK:
            # our zip actually is an APK
            if not self.clear:
                # let's unzip
                if self.verbose:
                    print( "Unzipping " + self.absolute_filename + " to " + os.path.join(self.outdir, 'unzipped'))
                try:
                    self.ziprar.extract_all(outdir=os.path.join(self.outdir, 'unzipped'))
                except:
                    print( "Unzipping failed (catching exception): %s" % (sys.exc_info()[0]))

        return self.properties.filetype

    def disassemble(self):
        """
        Disassembles the sample (as much as possible), and if the end-user is interested in output (clear unset)
        also decompiles it (as much as possible).
        
        APK: 
                java -jar apktool.jar [-q] d file.apk outdir/apktool
                if apktool failed
                      java -jar baksmali.jar -o outdir/smali classes.dex in file.apk
                      androaxml.py --input binary-manifest in file.apk --output outdir/AndroidManifest.text.xml
                if clear unset,
                      unzip file.apk -d outdir/unzipped
                else
                      just unzip META-INF/

        DEX:
                java -jar baksmali.jar -o outdir/smali classes.dex
                if clear unset,
                      make sure classes.dex is readable
                      dex2jar classes.dex -o classes-dex2jar.jar
                      unzip -qq classes-dex2jar.jar -d outdir/unjarred
                      procyon classes-dex2jar.jar -o outdir/procyon

        What we'll find:
        APK, clear unset: ./smali AndroidManifest.xml ./unzipped classes.dex classes-dex2jar.jar ./unjarred ./procyon
        APK, clear set  : ./smali AndroidManifest.xml classes.dex

        DEX, clear unset: classes.dex ./smali
        DEX, clear set  : classes.dex ./smali classes-dex2jar.jar ./unjarred ./procyon

        """
        if self.verbose:
            print("------------- Disassembling")
            
        if self.properties.filetype == droidutil.ARM or \
                self.properties.filetype == droidutil.RAR or \
                self.properties.filetype == droidutil.CLASS or \
                self.properties.filetype == droidutil.UNKNOWN:
            # TODO: we could be running procyon on a class file.
            if self.verbose:
                print("Nothing to disassemble for " + self.absolute_filename)
            return 

        if self.properties.filetype == droidutil.APK:
            # APKTOOL won't output to an existing dir unless you use the -f switch. But then, -f erases the contents
            # of the output dir... So we can't do this directly on self.outdir
            apktool_outdir = os.path.join(self.outdir, "apktool")
            if self.verbose:
                print("Running apktool on inputfile=" + self.absolute_filename)

            if self.verbose:
                print("Apktool command: java -jar %s d -f %s %s" % (droidconfig.APKTOOL_JAR, self.absolute_filename, apktool_outdir))
                subprocess.call(["java", "-jar", droidconfig.APKTOOL_JAR, \
                                 "d", "-f", self.absolute_filename,  \
                                 "-o", apktool_outdir ])
            else:
                # with quiet option
                subprocess.call(["java", "-jar", droidconfig.APKTOOL_JAR, \
                                 "-q", "d", "-f", self.absolute_filename,  \
                                 "-o", apktool_outdir ], stdout=self.process_output, stderr=self.process_output)

            if os.path.isdir(apktool_outdir):
                droidutil.move_dir(apktool_outdir, self.outdir)

            # we want all smali_classes? dir in smali
            if os.path.exists(os.path.join(self.outdir, "smali_classes2")):
                # we have multidex - we are going to move all smali classes in the same directory
                if self.verbose:
                    print("Moving multidex smali classes to ./smali")

                os.system("cp -R "+ os.path.join(self.outdir, "./smali_classes?/*") + " " + os.path.join(self.outdir, "./smali") )
                os.system("rm -r "+ os.path.join(self.outdir, "./smali_classes?") )
                
            if self.verbose:
                print( "Apktool finished" )

            # extract classes.dex whatever happens, we'll use it
            if self.verbose:
                print( "Extracting classes*.dex" )
            try:
                self.ziprar.extract_one_file('classes.dex', self.outdir)
                for i in range(2,10):
                    self.ziprar.extract_one_file('classes{}.dex'.format(i), self.outdir)
                    if not os.path.exists(os.path.join(self.outdir, 'classes{}.dex'.format(i))):
                        break
                    self.properties.smali['multidex'].append('classes{}.dex'.format(i))
                    
            except:
                if self.verbose:
                    print( "Extracting classes.dex failed: %s" % (sys.exc_info()[0]))
                else:
                    print( "Extracting classes.dex failed")

        # Disassemble the DEX(es)
        dex_files = []
        if self.properties.filetype == droidutil.DEX:
            dex_files.append( self.absolute_filename )
        else:
            if len(self.properties.smali['multidex']) > 0:
                for d in self.properties.smali['multidex']:
                    dex_files.append(os.path.join(self.outdir, d))
            else:
                dex_files.append(os.path.join(self.outdir, 'classes.dex'))

        smali_dir = os.path.join( self.outdir, 'smali' )

        if (not os.access( smali_dir, os.R_OK) or \
                (os.access(smali_dir, os.R_OK) and not os.listdir(smali_dir))):
            # we only do this if apktool didn't baksmali correctly
            for d in dex_files:
                if os.access(d, os.R_OK):
                    if self.verbose:
                        print( "Baksmali on {} -> {}".format(d, smali_dir))
                    try:
                        subprocess.call( [ "java", "-jar", droidconfig.BAKSMALI_JAR, \
                                           "d", "-o", smali_dir, d ], \
                                         stdout=self.process_output, stderr=self.process_output)
                    except:
                        print( "[-] Baksmali failed for {}".format(d) )

        # Decompile the DEX(es)
        if self.verbose:
            print("------------- Decompiling")

        if not self.clear:
            for d in dex_files:
                if os.access(d, os.R_OK):
                    jar_file = os.path.join(self.outdir, '{}-dex2jar.jar'.format(os.path.splitext(os.path.basename(d))[0]))
                    if os.access( droidconfig.DEX2JAR_CMD, os.X_OK):
                        if self.verbose:
                            print( "Dex2jar on " + d )
                            try:
                                subprocess.call( [ droidconfig.DEX2JAR_CMD, "--force", d, "-o", jar_file ], \
                                                 stdout=self.process_output, stderr=self.process_output)
                            except:
                                if self.verbose:
                                    print("[-] Dex2jar failed on {}".format(d))
                        else:
                            if self.verbose:
                                print("Dex2jar software is not executable, skipping (file: {0})".format(droidconfig.DEX2JAR_CMD))
                    
                    if os.access( jar_file, os.R_OK ):
                        if self.enable_procyon and os.access( droidconfig.PROCYON_JAR, os.R_OK ):
                            if self.verbose:
                                print( "Procyon decompiler on " + jar_file )
                            subprocess.call( [ "java", "-jar", droidconfig.PROCYON_JAR, \
                                               jar_file, "-o", os.path.join(self.outdir, 'procyon') ], \
                                             stdout=self.process_output, stderr=self.process_output)

                    if self.verbose:
                        print( "Unjarring " + jar_file )
                    jarziprar = droidziprar.droidziprar(jar_file, zipmode=True, verbose=self.verbose)
                    if jarziprar.handle == None:
                        if self.verbose:
                            print( "Bad Jar / Failed to unjar " + jar_file )
                    else:
                        try:
                            jarziprar.extract_all(os.path.join(self.outdir, 'unjarred'))
                        except:
                            print( "Failed to unjar: %s" % (sys.exc_info()[0]) )
                        jarziprar.close()

        # Convert binary Manifest
        if self.properties.filetype == droidutil.APK:
            manifest = os.path.join( self.outdir, 'AndroidManifest.xml')
            if not os.access( manifest, os.R_OK) or os.path.getsize(manifest)==0:
                if self.verbose: 
                    print( "Extracting binary AndroidManifest.xml")
                try:
                    self.ziprar.extract_one_file('AndroidManifest.xml', self.outdir)
                except:
                    print("Failed to extract binary manifest: %s" % (sys.exc_info()[0]))
                if os.access( manifest, os.R_OK) and os.path.getsize(manifest)>0:
                    textmanifest = os.path.join( self.outdir, 'AndroidManifest.text.xml')
                    subprocess.call( [ "androaxml.py", "--input", manifest, \
                                           "--output", textmanifest ], \
                                         stdout=self.process_output, stderr=self.process_output)
                    if os.access( textmanifest, os.R_OK ):
                        # overwrite the binary manifest with the converted text one
                        os.rename(textmanifest, manifest)
 
    def extract_file_properties(self):
        """Extracts file size, 
        nb of dirs and classes in smali dir"""
        if self.verbose:
            print("------------- Extracting file properties")
            
        self.properties.file_size = os.stat(self.absolute_filename).st_size

        if self.properties.file_size < 70000:
            self.properties.file_small = True
        
        smali_dir = os.path.join(self.outdir, "smali")

        if os.access(smali_dir, os.R_OK):
            self.properties.file_nb_dir, self.properties.file_nb_classes = droidutil.count_filedirs(smali_dir)

        if self.verbose:
            print( "Filesize: %d" % (self.properties.file_size))
            print( "Is Small: %d" % (self.properties.file_small))
            print( "Nb Class: %d" % (self.properties.file_nb_classes))
            print( "Nb Dir  : %d" % (self.properties.file_nb_dir))

    def extract_meta_properties(self):
        """Extracting meta-data related to APK's signature timestamp and signing certificate"""
        if self.properties.filetype == droidutil.APK:
            self.properties.certificate['timestamp'] = self.ziprar.get_date('META-INF/MANIFEST.MF')
            if self.properties.certificate['timestamp'] != None:
                self.properties.certificate['year'] = self.properties.certificate['timestamp'][0]
                if self.verbose:
                    print( "APK timestamp: %d" % (self.properties.certificate['timestamp'][0]))

            # extract properties from the certificate
            if self.verbose:
                print( "------------- Extracting properties from certificate")

            list = []
            try:
                list = self.ziprar.extract_pattern(self.outdir, 'META-INF/.*\.RSA')
                if not list:
                    list = self.ziprar.extract_pattern(self.outdir, 'META-INF/.*\.DSA')
            except:
                if self.verbose:
                    print( "Error at extraction: %s" % (sys.exc_info()[0]))

            if list:
                try: 
                    keyout = subprocess.check_output( [ droidconfig.KEYTOOL, "-printcert",  "-file", \
                                                       os.path.join(self.outdir, list[0]) ], \
                                                     stderr=self.process_output).decode('utf-8')
                    keyout = re.sub(': ', '#', keyout)
                    keyout = re.sub('\t| ', '', keyout)
                    keyout = re.sub('until#', '\nUntil#', keyout)
                    keysplit = re.split('#|\n', keyout)
                    try:
                        index = keysplit.index("Owner")
                        self.properties.certificate['owner'] = keysplit[index+1]
                        if self.verbose:
                            print( "Certificate Owner: "+self.properties.certificate['owner'])
                        self.extract_certificate_owner_properties(self.properties.certificate['owner'])
                            
                    except ValueError:
                        if self.verbose:
                            print( "Certificate Owner not present")
                    try:
                        index = keysplit.index("Serialnumber")
                        self.properties.certificate['serialno'] = keysplit[index+1]
                        if self.verbose:
                            print( "Certificate Serial no: "+self.properties.certificate['serialno'])

                        # detect typical dev certificate
                        if re.search('936eacbe07f201df', self.properties.certificate['serialno'], re.IGNORECASE):
                            self.properties.certificate['dev'] = True
                            if self.verbose:
                                print( "Dev certificate detected")
                    except ValueError:
                        if self.verbose:
                            print( "Serial number not present")
                    try:
                        index = keysplit.index("Signaturealgorithmname")
                        self.properties.certificate['algo'] = keysplit[index+1]
                        if self.verbose:
                            print( "Algo: "+self.properties.certificate['algo'] )
                    except ValueError:
                        if self.verbose:
                            print( "Signature algorithm name not present")
                except subprocess.CalledProcessError as e:
                    if self.verbose:
                        print( "Caught CalledProcessError: ", e.output)
                        print( "Probably an invalid certificate" )
            else:
                if self.verbose:
                    print( "No certificate found" )

    def extract_certificate_owner_properties(self, owner):
        # owner should not be null
        m = re.search('C=(\w*)', owner, re.IGNORECASE)
        if m != None:
            cert_country = m.group(0)[2:]
            if re.search('Unknown', cert_country, re.IGNORECASE):
                self.properties.certificate['unknown_country'] = True
            else:
                self.properties.certificate['country'] = droidcountry.to_int(cert_country)
                if self.verbose:
                    print( "Certificate Country = %s (%d)" % (cert_country, self.properties.certificate['country']) )

        # Debug certificate
        m = re.search('OU=Android  O=Android L=Mountain View', owner, re.IGNORECASE)
        if m != None:
            self.properties.certificate['debug'] = True
            
        # AV owner
        av_list = ('O=www.netqin.com',\
                   'OU=Symantec',\
                   'CN=Fortinet Android  OU=Android  O=Fortinet  L=Burnaby  ST=British Columbia  C=BC',\
                   'OU=Engineering  O=Webroot Software Inc  L=Boulder  ST=Colorado  C=US|CN=James Burgess',\
                   'OU=Mobile Security, O=Flexilis, L=Los Angeles, ST=CA, C=US|O=Sophos Ltd.  L=Abingdon  C=UK',\
                   'OU=Application Development  O=G Data Software AG  L=Bochum  ST=NRW  C=DE',\
                   'CN=VIRUSTOTAL  OU=VIRUSTOTAL  O=VIRUSTOTAL  L=Malaga  ST=Malaga  C=ES',\
                   'CN=Qihoo  OU=Qihoo 360 Technology Co Ltd  O=Qihoo 360 Technology Co Ltd  L=Chaoyang  ST=Beijing  C=CN',\
                   'CN=KAIDI,OU=KAIDI,O=KAIDI,L=Beijing,ST=Beijing,C=86',\
                   'EMAILADDRESS=android\@avast.com  CN=avast! Android  O=AVAST Software a.s.  L=Prague  ST=Prague  C=CZ')

        for av in av_list:
            m = re.search(av, owner, re.IGNORECASE)
            if m != None:
                if self.verbose:
                    print( "Certificate owner matches AV : "+m.group(0) )
                self.certificate['av'] = True

        # Companies
        famous_list = ('CN=Android  OU=Android  O=Google Inc\.  L=Moutain View  ST=California  C=US',\
                       'O=Rovio Mobile Ltd  L=Helsinki  C=FI',\
                       'CN=Facebook Corporation  OU=Facebook  O=Facebook Mobile  L=Palo Alto  ST=CA  C=US')
        for f in famous_list:
            m = re.search(f, owner, re.IGNORECASE)
            if m != None:
                if self.verbose:
                    print( "Certificate owner matches Famous : "+m.group(0) )
                self.certificate['famous'] = True

    def is_packed(self):
        """
        We assume a sample is packed if the main activity its manifest references cannot be found in the DEX + DexClassLoader or Dex File
        This test is far from perfect
        """
        smali_dir = os.path.join(self.outdir, 'smali')
        missing = False
        if self.properties.manifest['main_activity'] != None:
            filename = os.path.join(smali_dir, self.properties.manifest['main_activity'].replace('.', os.path.sep).replace('\'','') + '.smali')
            if not os.access(filename, os.R_OK):
                if self.verbose:
                    print("Unable to find Main Activitity: {} filename={}".format(self.properties.manifest['main_activity'],filename))
                missing = True

        if missing and (self.properties.smali['dex_class_loader'] or self.properties.smali['dex_file']):
            self.properties.smali['packed'] = True
                

    def extract_manifest_properties(self):
        """Extracting services, receivers, activities etc from manifest"""
        manifest = os.path.join(self.outdir, 'AndroidManifest.xml')
        if self.properties.filetype == droidutil.APK and os.access(manifest, os.R_OK) and os.path.getsize(manifest)>0:
            try:
                xmldoc = xml.dom.minidom.parse(manifest)
            except expat.ExpatError:
                if self.verbose:
                    print( "XML parsing error" )
                return;

            # getting package's name
            self.properties.manifest['package_name'] = xmldoc.documentElement.getAttribute('package')


            tab = droidutil.get_elements(xmldoc, 'service', 'android:name')
            tab.extend(droidutil.get_elements(xmldoc, 'service', 'obfuscation:name'))
            for t in tab:
                name = re.sub(r"u'(?P<name>.*)'", r"\g<name>", t)
                if name != "''":
                    self.properties.manifest['services'].append(name)
                                                            
            tab = droidutil.get_elements(xmldoc, 'receiver', 'android:name')
            tab.extend(droidutil.get_elements(xmldoc, 'receiver', 'obfuscation:name'))
            for t in tab:
                name = re.sub(r"u'(?P<name>.*)'", r"\g<name>", t)
                if name != "''" :
                    self.properties.manifest['receivers'].append(name)

            tab = droidutil.get_elements(xmldoc, 'activity', 'android:name')
            tab.extend(droidutil.get_elements(xmldoc, 'activity', 'obfuscation:name'))
            for t in tab:
                name = re.sub(r"u'(?P<name>.*)'", r"\g<name>", t)
                if name != "''" :
                    self.properties.manifest['activities'].append(name)

            tab = droidutil.get_elements(xmldoc, 'provider', 'android:name')
            tab.extend(droidutil.get_elements(xmldoc, 'provider', 'obfuscation:name'))
            for t in tab:
                name = re.sub(r"u'(?P<name>.*)'", r"\g<name>", t)
                if name != "''" :
                    self.properties.manifest['providers'].append(name)

            tab = droidutil.get_elements(xmldoc, 'uses-library', 'android:name')
            for t in tab:
                self.properties.manifest['libraries'].append(re.sub(r"u'(?P<nom>.*)'", r"\g<nom>", t))

            tab = droidutil.get_elements(xmldoc, 'uses-permission', 'android:name')
            tab.extend(droidutil.get_elements(xmldoc, 'uses-permission', 'obfuscation:name'))
            for t in tab:
                name = t.replace('android.permission.','').replace("u'", '').replace("'", '')
                if name != '':
                    self.properties.manifest['permissions'].append(name)

            tab = droidutil.get_elements(xmldoc, 'application', 'obfuscation:name')
            tab.extend(droidutil.get_elements(xmldoc, 'application', 'android:name'))
            for t in tab:
                if 'multidex' in t:
                    self.properties.manifest['multidex'] = True
                    break

            self.properties.manifest['maxSDK'] = droidutil.get_element(xmldoc, 'uses-sdk', 'android:maxSdkVersion')
            self.properties.manifest['minSDK'] = droidutil.get_element(xmldoc, 'uses-sdk', 'android:minSdkVersion')
            self.properties.manifest['targetSDK'] = droidutil.get_element(xmldoc, 'uses-sdk', 'android:targetSdkVersion')
            droidutil.get_elements(xmldoc, 'meta-data', 'android:value')

            if self.verbose:
                print( "MinSDK=%s MaxSDK=%s TargetSDK=%s" % (self.properties.manifest['minSDK'], self.properties.manifest['maxSDK'], self.properties.manifest['targetSDK']))
                for perm in self.properties.manifest['permissions']:
                    print( "Requires permission " + perm)

            # get main activity
            for actitem in xmldoc.getElementsByTagName('activity'):
                for a in actitem.getElementsByTagName('action'):
                    if a.getAttribute( 'android:name' ) == 'android.intent.action.MAIN' or a.getAttribute('obfuscation:name') ==  'android.intent.action.MAIN':
                        for b in actitem.getElementsByTagName('category'):
                            if b.getAttribute( 'android:name' ) == 'android.intent.category.LAUNCHER' or b.getAttribute('obfuscation:name') ==  'android.intent.category.LAUNCHER':
                                if actitem.getAttribute('android:name') != '':
                                    self.properties.manifest['main_activity'] = actitem.getAttribute( 'android:name' )
                                else:
                                    self.properties.manifest['main_activity'] = actitem.getAttribute( 'obfuscation:name' )                  
            if self.verbose and self.properties.manifest['main_activity'] != None:
                print( "Main activity: " + self.properties.manifest['main_activity'])

            # search for swf
            metalist = droidutil.get_elements(xmldoc, 'meta-data', 'android:value')
            for item in metalist:
                if re.search('\.swf', item):
                    self.properties.manifest['swf'] = True

            # get sms listener
            for r in xmldoc.getElementsByTagName('receiver'):
                for i in r.getElementsByTagName('intent-filter'):
                    for a in i.getElementsByTagName('action'):
                        if a.getAttribute( 'android:name' ) == 'android.provider.Telephony.SMS_RECEIVED':
                            self.properties.manifest['listens_incoming_sms'] = True
                        if a.getAttribute( 'android:name' ) == 'android.intent.action.NEW_OUTGOING_CALL':
                            self.properties.manifest['listens_outgoing_call'] = True

            if self.verbose:
                print( "Listens to incoming SMS  : %d" % (self.properties.manifest['listens_incoming_sms']))
                print( "Listens to outgoing calls: %d" % (self.properties.manifest['listens_outgoing_call']))
                

    def extract_kit_properties(self):
        """
        Detects which kits are present in the sample currently analyzed
        Returns something like: ['apperhand', 'jackson', 'applovin', 'leadbolt', 'airpush']
        """
        list = []
        if self.properties.filetype == droidutil.APK or self.properties.filetype == droidutil.DEX:
            smali_dir = os.path.join(self.outdir, "smali")
            if os.access(smali_dir, os.R_OK):
                for section in self.properties.kitsconfig.get_sections():
                    pattern_list = self.properties.kitsconfig.get_pattern(section).split('|')
                    for pattern in pattern_list:
                        for root, dirs, fname in os.walk(smali_dir):
                            if pattern in root:
                                if self.verbose:
                                    print("kits[%s] = True (detected pattern: %s)" % (section, pattern))
                                list.append(section)
                                self.properties.kits[ section ] = True
                                break # break one level
                        if self.properties.kits[ section ] == True:
                            break # break another level
        return list

    def extract_dex_properties(self):
        """Extracts information at DEX level. Requires read access to the DEX file. """
        if self.properties.filetype == droidutil.APK or self.properties.filetype == droidutil.DEX:
            if self.properties.filetype == droidutil.DEX:
                dex_file = self.absolute_filename
            else:
                dex_file = os.path.join(self.outdir, 'classes.dex')

            if os.access(dex_file, os.R_OK) and os.stat(dex_file).st_size > 0:
                file = open(dex_file, 'rb')
                magic = file.read(8)
                self.properties.dex['magic_unknown'] = True
                if magic[0:3] == 'dey':
                    self.properties.dex['odex'] = True
                for i in range(35,39):
                    if magic[4:7] == (b'0%d' % (i)):
                        self.properties.dex['magic'] = i
                        self.properties.dex['magic_unknown'] = False

                if self.verbose:
                    print( "DEX Magic: %s" % (repr(magic)))

                checksum = file.read(4)
                sha1 = file.read(20)

                # check sha1 of file
                if sha1 != '':
                    computed_sha1 = hashlib.sha1(file.read()).hexdigest()
                    if sha1.hex() != computed_sha1:
                        self.properties.dex['bad_sha1'] = True

                        if self.verbose:
                            print( "DEX SHA1 read    : %s" % sha1.hex())
                            print( "DEX SHA1 computed: %s" % (computed_sha1))
                else:
                    if self.verbose:
                        print( "Impossible to read file's SHA1 => impossible to check")

                # check checksum
                if checksum != '':
                    file.seek(8+4, 0) # 0 = from beginning, skip magic and checksum
                    computed_adler32 = zlib.adler32(file.read()) & 0xffffffff # beware, adler32 returns an INTEGER
                    if computed_adler32 != struct.unpack("<I", checksum)[0]: # converting both numbers to integers
                        self.properties.dex['bad_adler32'] = True

                    if self.verbose:
                        print( "DEX checksum read    : %s (reverse order)" % ( checksum.hex() ))
                        print( "DEX checksum computed: %s" % (hex(computed_adler32)))
                else:
                    if self.verbose:
                        print( "Impossible to read file's checksum => impossible to check" )

                # check header size
                file.seek(8+4+20+4, 0)
                header_size = struct.unpack("<I", file.read(4))[0]
                if header_size > 0x70:
                    if self.verbose:
                        print( "DEX header is bigger than expected: %d (HoseDex2Jar?)" % (header_size) )
                    self.properties.dex['big_header'] = True

                # look for 0 0x0 if-eq v0, v0, +9
                #1 0x4 fill-array-data v0, +3 (0x7)
                #2 0xa fill-array-data-payload 
                # See http://www.dexlabs.org/blog/bytecode-obfuscation
                file.seek(0x68, 0)
                data_size = struct.unpack("<I", file.read(4))[0]
                data_offset = struct.unpack("<I", file.read(4))[0]
                file.seek(data_offset, 0)
                buffer = file.read(data_size)
                fill_array_pattern = re.compile(b"\x32\x00\x09\x00\x26\x00\x03\x00\x00\x00")
                match = fill_array_pattern.search(buffer)
                if match != None:
                    if self.verbose:
                        print( "fill-array-data trick located at offset=%d" % (data_offset + match.start()) )
                        # to print the matching string: ''.join( [ "%02X " % ord( x ) for x in buffer[match.start():match.end() ] ).strip()
                    self.properties.dex['thuxnder'] = True
                
                file.close()            
            else:
                if self.verbose:
                    print( "Dex file %s is missing or empty" % (dex_file))

    def extract_smali_properties(self, list_of_kits):
        if self.properties.filetype != droidutil.APK and\
                self.properties.filetype != droidutil.DEX:
            # no smali properties to extract in that type of file
            return

        if self.verbose:
            print("------------- Extracting Smali properties")

        smali_dir = os.path.join(self.outdir, 'smali')
        if os.access(smali_dir, os.R_OK) and os.listdir(smali_dir) != []: 
            exceptions = []
            for kit in list_of_kits:
                pattern_list = self.properties.kitsconfig.get_pattern(kit).split('|')
                for pattern in pattern_list:
                    if pattern != None and pattern != '':
                        exceptions.append(pattern) # pattern may be part of a path so do not prefix with smali_dir
                    else:
                        if self.verbose:
                            print( "WARNING: configuration file error: empty pattern for %s" % (kit) )
                              
            smali_regexp = self.properties.smaliconfig.get_all_regexp()
            match = droidutil.recursive_search(smali_regexp, smali_dir, exceptions, False)
            
            analysis_file = open(os.path.join(self.outdir, droidlysis3.property_dump_file), 'a')
            analysis_file.write('# Smali keywords\n')
            analysis_file.close()

            self.properties.smaliconfig.match_properties(match, self.properties.smali)
            for mykey in match.keys():
                '''if self.verbose:
                    for element in match[mykey]:
                        print("- keyword=%s detected: %s" % (mykey, str(element)))'''
                if mykey.find('android_id') >= 0 and match[mykey]:
                    # this matches const-string v[0-9]*, "android_id"/'
                    self.properties.smali['android_id'] = True

                if mykey.find('scp') >= 0 and mykey.find('const-string') >=0 and match[mykey]:
                    # const-string v[0-9]*, ".*scp.*"
                    self.properties.smali['scp'] = True

                if mykey.find('ssh') >= 0 and mykey.find('const-string') >= 0 and match[mykey]:
                    # const-string v[0-9]*, ".*ssh.*'
                    self.properties.smali['ssh'] = True

                analysis_file = open(os.path.join(self.outdir, droidlysis3.property_dump_file), 'a')
                # let's not dump for nops
                if not (mykey == ' nop'):
                    if match[mykey]:
                        analysis_file.write("## %s\n" % (mykey))
                    for element in match[mykey]:
                        analysis_file.write("- "+str(element)+"\n")
                    analysis_file.write('\n')
                    analysis_file.close()

            # test if sample is likely to be packed
            self.is_packed()
        else:
            if self.verbose:
                print( "Cannot extract smali properties, because directory %s not found" % (smali_dir))
            # all smali properties should then be set to unknown
            for key in sorted(self.properties.smali.keys()):
                self.properties.smali[key] = 'unknown'
                                 
    def extract_wide_properties(self, list_of_kits):
        """Will look for given properties (e.g GPS usage, presence of executables
        in all subdirectories (smali, assets, resources, library...)"""

        if self.verbose:
            print("------------- Extracting Wide properties")        

        # detecting presence of ijiami packer
        ijiami = os.path.join(self.outdir, 'unzipped/assets/ijiami.dat')
        if os.access(ijiami, os.R_OK):
            self.properties.wide['ijiami'] = True

        # detect executables in resources
        self.find_exec_in_resources()

        # other properties
        if self.properties.filetype == droidutil.APK or self.properties.filetype == droidutil.DEX:
            exceptions = []
            for kit in list_of_kits:
                pattern_list = self.properties.kitsconfig.get_pattern(kit).split('|')
                for pattern in pattern_list:
                    exceptions.append(pattern)
            exceptions.append("/unjarred")
            exceptions.append("/unzipped")
            exceptions.append("/unknown")
            exceptions.append("classes.dex")
            exceptions.append('details.md')

            wide_regexp = self.properties.wideconfig.get_all_regexp()
            match = droidutil.recursive_search(wide_regexp, self.outdir, exceptions, False)
            analysis_file = open(os.path.join(self.outdir, droidlysis3.property_dump_file), 'a')
            analysis_file.write('# Keywords in resources, assets, lib\n\n')
            analysis_file.close()

            self.properties.wideconfig.match_properties(match, self.properties.wide)

            for mykey in match.keys(): # remember mykey is the matched value not the pattern
                if match[mykey]:
                    analysis_file = open(os.path.join(self.outdir, droidlysis3.property_dump_file), 'a')
                    analysis_file.write("- "+str(mykey)+"\n")
                    analysis_file.close()

                # put here keywords for which you need to do some processing on each match

                # keep a list of phonenumbers we detect
                # mykey will be the phonenumber
                # International phone number detector
                # actually, it should be \+[0-9]{1,3}[0-9]{1,14} but that
                # generates too many false positives (numbers for other reasons)
                # so I'm being conservative
                if mykey.startswith('+') and self.properties.wide['has_phonenumbers']: # mykey.startswith('+') and 
                    if re.search(b"\+[0-9]{1,3}[0-9]{10,14}", mykey):
                        self.properties.wide['phonenumbers'].append(mykey)
                        if self.verbose:
                            print( "Phone number spotted: " + mykey)
                        analysis_file = open(os.path.join(self.outdir, droidlysis3.property_dump_file), 'a')
                        analysis_file.write("- "+str(mykey)+"\n")
                        analysis_file.close()

                # we want to process each potential URL and IP address
                ip_pattern = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
                if ip_pattern.match(mykey):
                    if self.verbose:
                        print("IP address to check: {}".format(mykey))
                    self.interesting_url(mykey)
                    
                if mykey.find('http') >= 0 and match[mykey]:
                    self.interesting_url(mykey)

            analysis_file = open(os.path.join(self.outdir, droidlysis3.property_dump_file), 'a')
            analysis_file.write('\n\n')
            analysis_file.close()

            # detect base64 encoded string in resources
            self.find_base64_strings(self.outdir, exceptions, self.properties.wide['base64_strings'])

            # trying to grab the application's name
            if not self.clear:
                strings_file = os.path.join(self.outdir, "res/values/strings.xml")
                if os.access(strings_file, os.R_OK):
                    xmldoc = xml.dom.minidom.parse(strings_file)
                    sitems = xmldoc.getElementsByTagName('string')
                    if sitems != None:
                        for item in sitems:
                            if item.hasAttributes():
                                if item.getAttribute('name') == 'app_name':
                                    if item.hasChildNodes():
                                        self.properties.app_name = item.childNodes[0].data
                                        # rule out chinese characters: TODO: convert chinese characters to printable
                                        self.properties.app_name = re.sub('[^:print:]','', self.properties.app_name)
                                        break

    def extract_arm_properties(self, arm_filename=''):
        """Extracts properties from an ARM executable
        Either call this on a sample which is an ARM file. 
        Or from within an embedded ARM file inside an APK.
        """
        if self.properties.filetype == droidutil.ARM or arm_filename != '':
            if arm_filename == '':
                arm_filename = self.absolute_filename
            if self.verbose: 
                print( "Extracting properties from " + arm_filename)

            # Run "strings" on the executable
            proc = subprocess.Popen(['strings', arm_filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = proc.communicate()

            for section in self.properties.armconfig.get_sections():
                matches = re.findall(self.properties.armconfig.get_pattern(section), output[0].decode('utf-8'))
                if matches != None and len(matches) > 0:
                    self.properties.arm[section] = True
                    if self.verbose:
                        print( "Setting arm[%s]  = True" % (section))
                    if section == 'url_in_exec':
                        for m in matches:
                            self.interesting_url(m)

    def find_executables(self, dir):
        """Finds executables in a given directory. Does not parse recursively.
        Returns two lists:
        - ARM executables list (absolute filename)
        - APK executables list (absolute filename)
        """
        assert os.path.isdir(dir), "argument should be a directory"
        found_apk = []
        found_arm = []
        listing = os.listdir(dir)
        
        for file in listing:
            absolute_file = os.path.join(dir, file)
            if os.path.isfile(absolute_file):
                filetype = droidutil.get_filetype(absolute_file)
                if filetype == droidutil.ARM:
                    if self.verbose:
                        print( "%s is an ARM executable" % (absolute_file))
                    found_arm.append(absolute_file)
                else:
                    if filetype == droidutil.ZIP:
                        innerzip = droidziprar.droidziprar(absolute_file, True, self.verbose)
                        if innerzip.handle == None:
                            if self.verbose:
                                print( "%s is not a valid zip" % (absolute_file))
                            return found_apk, found_arm
                        filetype = innerzip.get_type()
                        innerzip.close()
                        if filetype == droidutil.APK:
                            if self.verbose:
                                print( "%s contains an APK" % (absolute_file))
                            found_apk.append(absolute_file)
                    else:
                        if filetype == droidutil.RAR:
                            innerzip = droidziprar.droidziprar(absolute_file, False, self.verbose)
                            if innerzip.handle == None:
                                if self.verbose:
                                    print( "%s is not a valid rar" % (absolute_file))
                                return found_apk, found_arm
                            filetype = innerzip.get_type()
                            innerzip.close()
                            if filetype == droidutil.APK:
                                if self.verbose:
                                    print( "%s contains an APK" % (absolute_file))
                                found_apk.append(absolute_file)
        return found_arm, found_apk

    def find_exec_in_resources(self):
        """Will detect embedded executables or zips in assets, raw resources and lib dir"""
        asset_dir = os.path.join(self.outdir, "assets")
        raw_dir = os.path.join(self.outdir, "res/raw")
        lib_dir = os.path.join(self.outdir, "lib/armeabi")
        lib2_dir = os.path.join(self.outdir, "lib/arm64-v8a")
        
        list_dir = [ asset_dir, raw_dir, lib_dir, lib2_dir ]

        for dir in list_dir:
            if os.access(dir, os.R_OK) and os.path.isdir(dir):
                if self.verbose:
                    print( "Parsing %s for embedded executables or zips... " % (dir))

                found_arm, found_apk = self.find_executables(dir)
                if found_arm or found_apk:
                    self.properties.wide['embed_exec'] = True
                    if self.verbose:
                        print( "Embedded executables/zip found in " + dir)
                    if found_arm:
                        for arm in found_arm:
                            if self.verbose:
                                print( "Recursively processing " + arm)
                            self.extract_arm_properties(arm)
                    if found_apk:
                        for apk in found_apk:
                            if self.verbose:
                                print( "Recursively processing " + apk)
                            droidlysis3.process_file(apk, self.outdir, self.verbose, self.clear, self.enable_procyon, self.disable_description, self.disable_dump, self.no_kit_exception)

    def interesting_url(self, url):
        """Rules out meaningless URLs to keep only those which might be useful for attackers.
        
        input: url - typically starting with http://
        output: self.properties.url list
        Will set self.properties. urls and some wide properties.
        """
        assert url != None, "Empty URL is not valid"
        url = re.sub('[,;" ].*', '', url) # remove after ",; or whitespace
        url = re.sub('\n.*','', url)
        url = re.sub('\r.*', '', url)
        url = re.sub('[^\x20-\x7e]','', url)
        
        url_regexp = '|'.join(droidurl.build_special_url_list())
        match = re.search(url_regexp, url) # only one match per line

        if match == None:
            # the url is not in the list of special URLs
            # let's check it hasn't been reported yet (unique URLs)
            if url not in self.properties.wide['urls']:
                self.properties.wide['urls'].append(url) 
                if self.verbose:
                    print( "URL: %s" % (url))

            # raise a warning if it downloads APKs or for dropbox
            search = re.findall("\.apk|\.zip",url)
            if search != None and len(search) > 0:
                if '\.apk' in search or '\.zip' in search:
                    self.properties.wide['apk_zip_url'] = True

        return self.properties.wide['urls']

    def find_base64_strings(self, thedir, exceptions, theproperty):
        '''
        To detect base64 strings, we spot all constants with potentially base64 encoded
        characters. Then, on these, we attempt to perform base 64 decoding.
        If that does not lead to an error (padding exception etc) and if the result is
        printable (~ makes potential sense), we assume this is a Base64 string
        '''
        # const-string v1, "xyz=="
        # this won't detect all base64 strings because they won't all finish with ==
        # but we'll get some...
        base64_regexp = bytes("const-string v[0-9]*, \"[a-zA-Z0-9/?=]*\"", 'utf-8')
        base64_strings = droidutil.recursive_search(base64_regexp, thedir, exceptions, False)

        if base64_strings is not None:
            printable_chars = bytes(string.printable, 'ascii')
            for s in base64_strings.keys():
                # remove the const-string vX part and trailing "
                thestr = re.sub('const-string v[0-9]*, "', '', s)
                thestr = re.sub('"','', thestr)
                    
                # try to decode the Base64 string
                try:
                    decoded = base64.b64decode(thestr)
                    
                    if all(c in printable_chars for c in decoded) and decoded != b'' and (not decoded.decode('utf-8') in theproperty):
                        # the decoded string is printable, so likely a valid decoded base64 info
                        # + the array contains unique strings only
                        theproperty.append(decoded.decode('utf-8'))
                        if self.verbose:
                            print("Base64 string: ", decoded)
                except Exception as e:
                    # this is not a base64 string
                    pass

            if len(theproperty) > 0:
                analysis_file = open(os.path.join(self.outdir, droidlysis3.property_dump_file), 'a')
                analysis_file.write("Base64 strings:\n")

                for b in theproperty:
                    analysis_file.write("- "+b+"\n")
                    
                analysis_file.close()

            
