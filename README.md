convert
=======


    python convert.py --help
    Usage: convert.py [options]

    Process a directory containing image files and convert from TIFF to JPEG2000,
    and JPEG2000 to a variety of JPEG derivatives.  Prerequisites include Kakadu
    kdu_compress and ImageMagick compiled with JasPer (for JPEG2000 support).  The
    application supports multi-threading for multi proc/core systems.  Images will
    be removed from the source directory when processed correctly.
  
    Options:
      -h, --help            show this help message and exit
      -s SOURCE, --source=SOURCE
                            Source directory to be processed: Absolute or relative
                            path.
      -d DESTINATION, --destination=DESTINATION
                            Destination directory of processed images: Absolute or
                            relative path.
      -c JP2CONVERSION, --jp2conversion=JP2CONVERSION
                            Set TIFF to JPEG2000 program.  default kdu_compress
      -j JPEGCONVERSION, --jpegconversion=JPEGCONVERSION
                            Set JPEG2000 to JPEG program.  default ImageMagick
                            convert with JasPer JPEG2000 support
      -t THREADS, --threads=THREADS
                            Set number of threads to execute at once.   default  =
                            12
      -b BROKEN, --broken=BROKEN
                            Directory to place files left unprocessed due to
                            error.  Absolute or relative path.  default
                            destination/_broken

Prerequisites
------------
* Kakadu Software : [http://www.kakadusoftware.com/]
* ImageMagick : [http://www.imagemagick.org/]
* JasPer : [http://www.ece.uvic.ca/~frodo/jasper/]
