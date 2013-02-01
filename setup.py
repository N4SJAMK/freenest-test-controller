#import os
#from setuptools import setup
 #
 # Utility function to read the README file.
 # Used for the long_description.  It's nice, because now 1) we have a top level
 # README file and 2) it's easier to type in the README file than to put a raw
 # string in below ...
#def read(fname):
#    return open(os.path.join(os.path.dirname(__file__), fname)).read()

#setup(
    #name = "fntc",
    #version = "0.0.1",
    #author = "Mikko Ojala & Niko Korhonen",
    #author_email = "mikko.ojala@jamk.fi",
    #description = ("FreeNest test client"),
    #license = "GPLv2",
    #keywords = "FreeNest Testlink",
    #url = "http://",
    #packages=['fntc'],
    #py_modules=['fntc'],
    #scripts=['scripts/fntc'],
    #long_description=read('README'),
    #classifiers=[
#        "Development Status :: 2 - Pre-Alpha",
        #"Topic :: Utilities",
        #"License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        #"Environment :: Console",
        #"Intended Audience :: Manufacturing",
#        
    #],	
	#data_files=[('/etc/fntc', ['data/fntc.cnf']),				
				#('/var/www/fntc', ['php/class-IXR.php','php/XMLRPCTestRunner.php'])],
#	
#)

#!/usr/bin/env python

from distutils.core import setup

setup(name='fntc',
      version='0.1',
      description='FreeNest Test Client',
      author='Mikko Ojala',
      author_email='mikko.ojala@jamk.fi',
      url='http://www.freenest.org/',
      packages=['fntc'],
      py_modules=['fntc'],
      scripts=['scripts/fntc'],
	  data_files=[('/etc/fntc', ['data/fntc.cnf']),				
				('/var/www/fntc', ['php/class-IXR.php','php/XMLRPCTestRunner.php'])],      
      
     )
