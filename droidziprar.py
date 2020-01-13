#!/usr/bin/env python3

"""
__author__ = "Axelle Apvrille"
__status__ = "In progress"
__license__ = "MIT License"
"""
import zipfile
import rarfile # install from https://github.com/markokr/rarfile
import re
import droidutil
import struct
import subprocess

class droidziprar:

    def __init__(self, archive, zipmode=True, verbose=False):
        """Returns the archive file handle - don't forget to close it once you've finished with the file"""
        self.verbose = verbose
        self.zipmode = zipmode # True for a zip, False for a Rar
        self.password = 'infected'
        self.handle = None
        self.archive_name = archive

        # File type is not fully certain until get_type() has been called
        if self.zipmode:
            self.filetype = droidutil.ZIP
        else:
            self.filetype = droidutil.RAR

        self.open(archive)


    def open(self, filename):
        try:
            if self.zipmode:
                if self.verbose:
                    print( "Opening Zip archive "+filename)
                self.handle = zipfile.ZipFile(filename, 'r')
            else:
                if self.verbose:
                    print( "Opening Rar archive "+filename)
                self.handle = rarfile.RarFile(filename, 'r')

        except (struct.error, zipfile.BadZipfile, zipfile.LargeZipFile, IOError) as e:
            if self.verbose:
                print( "Exception caught in ZipFile: %s" % (repr(e)))
            self.handle = None

        return self.handle

    def get_type(self):
        """A ZIP file can be really an APK, a JAR, or a real ZIP
        Calling this function reallys sets the appropriate type for the archive.
        Returns:
        - the file type: APK, CLASS or ZIP
        - a list of inner zips/rars if any
        """
        assert self.handle != None, "zip/rar file handle has been closed"

        innerzips = [] # default value
        files_in_zip = self.handle.namelist()

        # guess file type based on contents
        if [x for x in files_in_zip if re.search("classes\.dex|AndroidManifest\.xml|resources\.arsc|assets/|res/", x)]:
            self.filetype = droidutil.APK
        else:
            innerzips = [x for x in files_in_zip if re.search("\.apk|\.zip|\.rar", x)]
            if innerzips:
                if self.zipmode:
                    self.filetype = droidutil.ZIP
                else:
                    self.filetype = droidutil.RAR
            else:
                if [x for x in files_in_zip if re.search("\.class", x)]:
                    self.filetype = droidutil.CLASS
        return self.filetype, innerzips

    def extract_one_file(self, filename, outdir):
        """Extracts from a ZIP or a RAR
        - file: file to extract
        - outdir: directory to extract to
        Will use a password if necessary
        """
        if self.zipmode:
            # the unzip command works better... (manages to unzip more)
            subprocess.call([ "/usr/bin/unzip" , "-o", "-qq", "-P", self.password, "-d", outdir, self.archive_name, filename])
        else:
            assert self.handle != None, "zip/rar file handle has been closed"
            # beware this may raise errors KeyError, RuntimeError...
            self.handle.extract(filename, outdir, pwd=self.password)

    

    def extract_all(self, outdir):
        if self.zipmode:
            print( 'Launching unzip process on %s with output dir=%s' % (self.archive_name, outdir))
            subprocess.call([ "/usr/bin/unzip" , "-o", "-qq", "-P", self.password, self.archive_name, "-d", outdir ])
        else:
            assert self.handle != None, "zip/rar file handle has been closed"
            self.handle.extractall(path=outdir, pwd=self.password)

    def extract_pattern(self, outdir, pattern):
        """Unzips (or unrars) files matching a given regexp to a given output directory.
        Returns a list of what has been unzipped.
        """
        assert self.handle != None, "zip/rar file handle has been closed"
        all_files = self.handle.namelist()
        list = [x for x in all_files if re.search(pattern, x)]
        
        for file in list:
            self.extract_one_file(file, outdir)

        return list

    def get_date(self, filename):
        """Gets the time at which filename was created"""
        assert self.handle != None, "zip/rar file handle has been closed"
        try:
            metainfo = self.handle.getinfo(filename)
            return metainfo.date_time
        except (KeyError, rarfile.NoRarEntry) as e:
            if self.verbose:
                print( "%s does not exist in %s" % (filename, self.archive_name))
        return None

    def close(self):
        if self.handle == None:
            pass
        else:
            self.handle.close()
            if self.verbose:
                print( "Closing archive: " + self.archive_name)
    
