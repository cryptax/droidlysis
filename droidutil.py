import os
import errno
import re
import shutil
import magic
import xml.dom.minidom
import hashlib
from collections import defaultdict

"""Those are my own utilities for sample analysis"""

def mkdir_if_necessary(path):
    """Creates the directory if it does not exist yet. 
    If it exists, does not do anything.
    If path is None (not filled), does not do anything."""

    if path != None:
        try:
            os.makedirs(path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise

def on_rm_tree_error(fn, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    rmtree fails in particular if the file to delete is read-only.
    to remove, we attempt to set all permissions and then retry.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    if fn is os.rmdir:
        os.chmod(path, 777)
        os.rmdir(path)
    elif fn is os.remove:
        os.chmod(path, 777)
        os.remove(path)

def move_dir(src,dst):
        """Move src directory to dst - works even if dst already exists."""
        assert os.path.isdir(src), "src must be an existing directory"
        os.system ("mv"+ " " + src + "/* " + dst)
        shutil.rmtree(src, onerror=on_rm_tree_error)

def sanitize_filename(filename):
    """Sanitizes a filename so that we can create the output analysis directory without any problem.
    We need to consider we might have filenames with Russian or Chinese characters. 
    
    filename is only the 'basename' not an absolute path

    Returns the sanitized name."""
    # we remove any character which is not letters, numbers, _ or .
    return re.sub('[^a-zA-Z0-9_\.]','', filename)

def listAll(dirName):
    filelist1=[]
    files = os.listdir(dirName)
    for f in files:
        if os.path.isfile(os.path.join(dirName,f)):
            filelist1.append(os.path.join(dirName,f))
        else:
            newlist=listAll(os.path.join(dirName,f));
            filelist1.extend(newlist)           
    return filelist1 



def count_filedirs(dirname):
    """Counts the number of directories and files in a given directory. Counts recursively.
    dirname must be readable.
    Returns:
    nb of directories
    nb of files
    
    This is somewhat the equivalent of: find ./smali -type d -print 
    or -type f
    """
    assert os.access(dirname, os.R_OK), "Can't access directory: "+dirname
    
    dirs = [name for name in os.listdir(dirname) if os.path.isdir(os.path.join(dirname, name))]
    nb_dirs = len(dirs)
    nb_files = len([name for name in os.listdir(dirname) if os.path.isfile(os.path.join(dirname, name))])
    for element in dirs:
        try:
            element_dirs, element_files = count_filedirs(os.path.join(dirname, element))
        except RuntimeError:
            # occurs when too many recursive dir
            element_dirs = 0
            element_files = 0
        nb_dirs += element_dirs
        nb_files += element_files

    return nb_dirs, nb_files

def sha256sum(input_file_name):
    """Computes the SHA256 hash of a binary file
    Returns the digest string or '' if an error occurred reading the file"""
    chunk_size = 1048576 # 1 MB
    file_sha256 = hashlib.sha256()
    try:
        with open(input_file_name, "rb") as f:
            byte = f.read(chunk_size)
            while byte:
                file_sha256.update(byte)
                byte = f.read(chunk_size)
    except IOError:
        print ('sha256sum: cannot open file: %s' % (input_file_name))
        return ''
    return file_sha256.hexdigest()

def sha1sum(input_file_name):
    """Computes the SHA1 hash of a binary file
    Returns the digest string or '' if an error occurred reading the file"""
    chunk_size = 1048576 # 1 MB
    file_sha1 = hashlib.sha1()
    try:
        with open(input_file_name, "rb") as f:
            byte = f.read(chunk_size)
            while byte:
                file_sha1.update(byte)
                byte = f.read(chunk_size)
    except IOError:
        print ('sha1sum: cannot open file: %s' % (input_file_name))
        return ''
    return file_sha1.hexdigest()

# -------------------------- File Constants -------------------------
"""Something else than the other file types. We do not support this file type."""
UNKNOWN=0 

"""An APK. It is not possible to differentiate a ZIP from an APK until we have looked inside the ZIP."""
APK=1    

"""A Dalvik Executable file. We do not check the file is valid/accepted by the verifier."""
DEX=2

"""An ARM ELF executable."""
ARM=3

"""A Java .class file"""
CLASS=4

"""A Zip file. Actually, this can also be a JAR or an APK until we have thoroughly checked."""
ZIP=5

"""A RARed file."""
RAR=6

"""We can probably add some more later: TAR, TGZ, BZ2..."""

def str_filetype(filetype):
    """Provide as input a droidutil filetype (APK, DEX, ARM...) and returns the corresponding string"""
    if filetype == APK:
        return "APK"
    if filetype == DEX:
        return "DEX"
    if filetype == ARM:
        return "ARM"
    if filetype == CLASS:
        return "CLASS"
    if filetype == ZIP:
        return "ZIP"
    if filetype == RAR:
        return "RAR"
    return "UNKNOWN"
    

def get_filetype(filename):
    """Returns an enumerate for the filetype corresponding to the given absolute filename.
    This function does not open the file or unzip it.
    It will return one of these:
    droidutil.ZIP
    droidutil.RAR
    droidutil.ARM
    droidutil.CLASS
    droidutil.DEX
    droidutil.UNKNOWN
    """
    filetype = magic.from_file(filename)
    if filetype == None:
        # this happens if magic is unable to find file type
        return UNKNOWN
    match = re.search('Zip archive data|zip|RAR archive data|executable, ARM|shared object, ARM|Java class|Dalvik dex|Java archive', filetype)
    if match == None:
        mytype = UNKNOWN
    else:
        typecase = { 'Zip archive data' : ZIP,
                     'zip' : ZIP,
                     'Java archive' : ZIP,
                     'RAR archive data' : RAR,
                     'executable, ARM' : ARM,
                     'shared object, ARM' : ARM,
                     'Java class' : CLASS,
                     'Dalvik dex' : DEX,
                     'None' : UNKNOWN   }
        mytype = typecase[match.group(0)]
    return mytype


def get_elements(xmldoc, tag_name, attribute):
    """Returns a list of elements"""
    l = []
    for item in xmldoc.getElementsByTagName(tag_name) :
        value = item.getAttribute(attribute)
        l.append( repr( value ) )
    return l

def get_element(xmldoc, tag_name, attribute):
    for item in xmldoc.getElementsByTagName(tag_name) :
        value = item.getAttribute(attribute)
        if len(value) > 0 :
            return value
    return None

"""Very simple exception to raise when we found something. For instance to break a loop."""
class Found(Exception): pass

class matchresult:
    """Match information"""

    def __init__(self, thefile, theline, thelineno):
        """Represents a match for a keyword.
        Made of a filename and a line"""
        self.file = thefile
        self.line = theline
        self.lineno = thelineno
    
    def __repr__(self):
        return 'file=%s lineno=%d line=%s' % (self.file, self.lineno, self.line)

    def __str__(self):
        if len(self.file) > 70:
            f = '...'+self.file[-70:]
        else:
            f = self.file
        return 'file=%50s no=%4d line=%30s' % (f, self.lineno, self.line)

def recursive_search(search_regexp, directory, exception_list=[], verbose=False):
    """Recursively search in a directory except in some subdirectories
    The exception list actually is a list of regexp for directories.
    
    Returns a dictionary of list of matches:
    match[ keyword ] = [ <'filename', 'matching line content', 'lineno'>,
                         <'filename', 'matching line content', 'lineno'>,
                         <'filename', 'matching line content', 'lineno'>, ]

    We can only have one match per line. Otherwise, this won't work we should be using re.findall
    """
    matches = defaultdict(list)

    if verbose:
        print("Searching in " + directory + " for " + search_regexp.decode('utf-8'))
        print("Exceptions: %s" % (str(exception_list)))

    for entry in os.listdir(directory):
        current_entry = os.path.join(directory, entry)
        try: 
            if os.path.isfile(current_entry):
                for exception in exception_list:
                    # TO DO: not entirely sure we need 'match'? perhaps if it is a regexp?
                    # Remember that "exception" can be part of a path e.g we want everything that matches blah/bloh
                    # then com/blah/bloh must match
                    match = re.search(exception, current_entry) # TO DO: not entirely sure we need the match
                    if match != None or exception in current_entry: 
                        # skip this file
                        raise Found

                # ok, this file must be searched
                lineno = 0
                for line in open(current_entry, 'rb'):
                    lineno += 1
                    match = re.search(search_regexp, line)
                    if match != None:
                        if verbose:
                            print("Match: File: " +entry+ " Keyword: " +match.group(0).decode('utf-8', errors='replace') + " Line: " + line.decode('utf-8', errors='replace'))
                        """match.group(0) only provides one match per line if we need more, 
                        re.search is not appropriate
                        and should be replaced by re.findall"""
                        matches[ match.group(0).decode('utf-8', errors='replace') ].append(matchresult(current_entry, line, lineno))


            if os.path.isdir(current_entry):
                for exception in exception_list:
                    match = re.search(exception, current_entry)
                    if match != None:
                        # skip this directory
                        raise Found

                # this directory is not in the exception list, we must search it recursively
                try:
                    hismatches = recursive_search(search_regexp, current_entry, exception_list, verbose)
                    # merge in those results
                    for key in hismatches.keys():
                        matches[ key ].extend( hismatches[ key ] )
                except RuntimeError:
                    # we get this when there are too many recursive dirs
                    pass # next


        except Found:
            pass # go to next entry

    return matches

