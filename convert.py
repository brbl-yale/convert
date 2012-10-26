#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import shutil
import errno
import sys
import optparse
import string
import smtplib
import datetime
from datetime import date
import subprocess
from thread_pool import ThreadPool
from application_lock import ApplicationLock


"""
Verbosity
"""
VERBOSE=True


"""
Debug
"""
DEBUG=False # = Remove empty folders after processing


"""
Log File
"""
LOGFILE='/tmp/convert_' + datetime.datetime.now().strftime("%Y-%b-%d_%H-%M-%S") + '.log'


"""
Conversion options
"""
TIF_TO_JP2=True
JP2_TO_JPEG=True


"""
Conversion tools
"""
JP2_TOOL='kdu_compress'
JPEG_TOOL='convert'


"""
Kakadu kdu_compress runtime options
"""
KDU_OPTIONS = \
     '-quiet -rate 1.5 Creversible=yes Clayers=1 Clevels=7 \"Cprecincts={256,256},{256,256},{128,128}\" \"Corder=RPCL\" \"ORGgen_plt=yes\" \"ORGtparts=R\" \"Cblk={64,64}\" Cuse_sop=yes'


"""
ImageMagick convert runtime options
"""
JPEG_DEST_FILES    = [['half.jpg', '1500x2100'],['quarter.jpg', 
                      '1200x1500'], ['thumb.jpg', '200x200']]


"""
Email alert using GMail
"""
EMAIL           = 'email@email.edu'
SUBJECT         = 'Image Convert Report ' + str(date.today())
FROM_EMAIL      = 'email@gmail.com'
USERNAME        = 'email'
PASSWORD        = 'password'


"""
END configuration options
"""



class logBuffer:

    def __init__(self):
        self.content = []

    def write(self, string):
        self.content.append(string)


emaillog = logBuffer()


""" 
  Parse variables passed to the program 
"""
def parseOptions():
    usage = 'usage: %prog [options]'
    description = 'Process a directory containing image files and convert from TIFF to JPEG2000, and JPEG2000 to a variety of JPEG derivatives.  Prerequisites include Kakadu kdu_compress and ImageMagick compiled with JasPer (for JPEG2000 support).  The application supports multi-threading for multi proc/core systems.  Email, command line options, verbosity, and other configuration options can be modified directly in convert.py'
    parser = optparse.OptionParser(usage=usage, description=description)
    parser.add_option(  
        '-s',
        '--source',
        action='store',
        dest='source',
        default='',
        help='Source directory to be processed: Absolute or relative path.'
        )
    parser.add_option(
	'-d',
	'--destination',
	action='store',
	dest='destination',
	default='',
	help='Destination directory of processed images: Absolute or relative path.'
	)
    parser.add_option(
        '-t',
        '--threads',
        action='store',
        dest='threads',
        default=12,
        help='Set number of threads to execute at once.   default = 12'
        )
    parser.add_option(
        '-b',
        '--broken',
        action='store',
        dest='broken',
        default='_broken',
        help='Directory to place files left unprocessed due to error.  Absolute or relative path.  default destination/_broken'
        )
    return parser.parse_args()

"""
  Send an email using the appropriate global configuration

  @param      _message         Message to be sent via email
"""
def sendEmail(_message):
    body = string.join(('From: %s' % FROM_EMAIL, 'To: %s' % EMAIL,
                        'Subject: %s' % SUBJECT, '', _message), '\r\n')
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(USERNAME,PASSWORD)

    # server.set_debuglevel(1)

    server.sendmail(FROM_EMAIL, EMAIL, body)
    server.quit()


"""
  Log output to local filesystem
"""
def logOutput(_message):
    f = open(LOGFILE, 'w')
    f.write(_message)
    f.close()


"""
  Make directory if it doesn't exist

  @param	_dir	Directory to be tested and created
"""
def makeDir(_dir):
    try:
        os.makedirs(_dir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
            print >>emaillog, 'Unable to create ' + _dir 
            sendEmail(''.join(emaillog.content))
            sys.exit()


"""
  Check if program exists in user path

  @param	_name	Name of application
"""
def checkProgram(_name):
    for dir in os.environ['PATH'].split(':'):
        prog = os.path.join(dir, _name)
        if os.path.exists(prog): 
            return prog


"""
  Converts TIFF to JP2

  @param	_threads	Number of concurrent threads to execute
  @param	_app		Application used to process, kdu_compress default
  @param	_source		Source directory (can include subdirectories)
  @param	_destination	Destination directory (does not need to exist)
  @param	_broken		Directory to store broken images that are left unprocessed
  @param	_options	Options to pass to _app
  @param	_verbose	Verbosity
"""
def tif_to_jp2(
    _threads,
    _app,
    _source,
    _destination,
    _broken,
    _options,
    _verbose
    ):
 
    testApp(_app)

    t = ThreadPool(_threads)

    for (root, dirs, files) in os.walk(_source):
        subpath = root.replace(_source, '').lstrip('/')
        if _broken not in subpath:  
            jp2Path = os.path.join(_destination,subpath)
            makeDir(jp2Path)
            if any(".tif" in s for s in files):
                print >>emaillog, 'Converting contents of ' + subpath + ' from TIF to JP2'
            for file in files:
                if file.endswith('.tif'):
                    tiff = os.path.join(root, file)
                    jp2 = os.path.join(_destination, subpath,
                                       os.path.splitext(file)[0] + '.jp2')
		    tiffcopy = os.path.join(_destination,subpath,file)
                    command = _app + ' -i ' + tiff + ' -o ' + jp2 + ' ' \
                        + _options
                    command_post = 'shutil.move(\'' + tiff + '\',\'' + tiffcopy + '\')'
		    if _verbose == True:
			print 'Creating ' + jp2
	            t.add_task(executeConversion,command,command_post,tiff,_destination,_broken,file,jp2)
        t.await_completion()


"""
  Converts JP2 to JPEG derivatives 

  @param        _threads        Number of concurrent threads to execute
  @param        _app            Application used to process, ImageMagick convert default
  @param        _source         Source directory (can include subdirectories)
  @param        _destination    Destination directory (does not need to exist)
  @param        _broken         Directory to store broken images that are left unprocessed
  @param	_jpegs		Array of names,sizes of various required derivatives
  @param	_verbose	Verbosity
"""
def jp2_to_jpeg(
    _threads,
    _app,
    _source,
    _destination,
    _broken,
    _jpegs,
    _verbose
    ):
    testApp(_app)

    t = ThreadPool(_threads)

    for (root, dirs, files) in os.walk(_destination):
        subpath = root.replace(_destination, '').lstrip('/')
        if _broken not in subpath:
            if any(".jp2" in s for s in files):
                print >>emaillog, 'Converting contents of ' + subpath + ' from JP2 to JPEG'
	    for (output_file, size) in _jpegs:
                for file in files:
                    if file.endswith('.jp2'):
                        jp2 = os.path.join(root, file)
                        newfile = os.path.join(root,
                                  os.path.splitext(file)[0]) + '_' \
                                  + output_file
                        command = _app + ' -size ' + size + " " + jp2 \
                                  + ' -resize ' + size + ' ' + newfile
                        if _verbose == True:
                            print 'Creating ' + newfile
			t.add_task(executeConversion,command,None,jp2,_source,_broken,file,newfile)
	        t.await_completion()

"""
  Tests application exists and exits if not found

  @param	_app	Application defined
"""
def testApp(_app):
    if str(checkProgram(_app)) == "None":
        print >>emaillog, _app + ' not found.  Exiting.'
        sendEmail(''.join(emaillog.content))
        sys.exit()
    else:
        print _app + ' found.'


"""
  Process conversion commands defined above and report errors

  @param	_command	Command to execute
  @param	_command_post	Post processing command to execute 
  @param	_srcfile	Full path + file name being performed upon
  @param        _destination   	Destination directory (does not need to exist)
  @param        _broken         Directory to store broken images that are left unprocessed
  @param	_file		File that command is acting upon
  @param	_create		File with full path that is being created

"""
def executeConversion(
    _command, 
    _command_post,
    _srcfile,
    _destination,
    _broken, 
    _file,
    _create
    ):
    proc = subprocess.Popen(_command, stdout=subprocess.PIPE,
		            stderr=subprocess.PIPE, shell=True )
    output = proc.stderr.read()
    if output:
        print >>emaillog, '\n--'
        print >>emaillog, 'Error encountered running the following command: '
        print >>emaillog, _command
        print >>emaillog, 'Output: '
        print >>emaillog, output
        print >>emaillog, 'Moved to following directory for inspection: \n' + os.path.join(_destination,_broken,_file)
        if (os.path.exists(_srcfile)):
            shutil.move(_srcfile, os.path.join(_destination,_broken,_file))
        print >>emaillog, 'Removing file created by this process: \n' + _create
        if (os.path.exists(_create)):
            os.remove(_create)
    else:
        if _command_post:
	    exec _command_post

def removeEmptyFolders(path):
  if not os.path.isdir(path):
    return
 
  # remove empty subfolders
  files = os.listdir(path)
  if len(files):
    for f in files:
      fullpath = os.path.join(path, f)
      if os.path.isdir(fullpath):
        removeEmptyFolders(fullpath)
 
  # if folder empty, delete it
  files = os.listdir(path)
  if len(files) == 0:
    print "Removing empty folder:", path
    os.rmdir(path)
        

def main():
  
  # Fetch those options
  
    (options, args) = parseOptions()

  # Test source exists
 
    if os.path.isdir(options.source):
 
      # Create destination if doesn't exist
  	if TIF_TO_JP2 == True:
            if not os.path.isdir(options.destination):
                print options.destination + ' does not exist.  Creating...'
                makeDir(options.destination)

      # Create broken directory if doesn't exist
        if not os.path.isdir(options.broken):
            print options.broken + ' does not exist.  Creating...'
            makeDir(os.path.join(options.destination,options.broken))

      # Process images 
	if TIF_TO_JP2 == True:
	    if VERBOSE == True:
		print 'Ready to begin TIFF to JP2 transformation.'
            tif_to_jp2(int(options.threads),JP2_TOOL,
                       options.source,options.destination,options.broken,
                       KDU_OPTIONS,VERBOSE)
        if JP2_TO_JPEG == True:
	    if VERBOSE == True:
		print 'Ready to begin JP2 to JPEG transformation.'
	    jp2_to_jpeg(int(options.threads),JPEG_TOOL,
                       options.source,options.destination,options.broken,
                       JPEG_DEST_FILES,VERBOSE)
 

      # Test if errors exist, email if true

        if emaillog.content:
            sendEmail(''.join(emaillog.content))
	    logOutput(''.join(emaillog.content))

      # Remove any empty directories in source or destination
	if DEBUG == False:
            removeEmptyFolders(options.source)
            removeEmptyFolders(options.destination)
	

if __name__ == '__main__':
    applock = ApplicationLock ('/tmp/convert.lock')
    if (applock.lock()):
        main()
        applock.unlock()
    else:
        print ('Unable to obtain lock, exiting')
