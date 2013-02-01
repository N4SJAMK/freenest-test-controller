#! /usr/bin/python
import sys
from TestLinkAPI import TestlinkAPIClient

if __name__=="__main__":

	#import xmlrpclib
	import TestLinkAPI
	import sys, os
	import subprocess
	import logging
	import yaml
    
    
    #s = sys.argv[1] + " " + sys.argv[2] + " " + sys.argv[3] + " " + sys.argv[4] + " " + sys.argv[5] + " " + sys.argv[6] + " " + sys.argv[7] + " " + sys.argv[8]
    	devKey = "26a3c5ceb98f1f79793bcb419b0891e1"
	server = "http://strongbow.labranet.jamk.fi/ProjectTESTLINK/lib/api/xmlrpc.php"
    # substitute your Dev Key Here
	client = TestlinkAPIClient (devKey, server)
    # get info about the server
    	print client.getInfo()
	
    # retval = client.sayHello()
	if sys.argv[1] == '':
		print "testcaseexternalid, version, testprojectid, customfieldname, details"

    #retval = client.getProjects(devKey)
    	retval = client.getTestCaseCustomFieldDesignValue(devKey, sys.argv[1], sys.argv[2], sys.argv[3],sys.argv[4],sys.argv[5])

    	print 'retval: ', retval
