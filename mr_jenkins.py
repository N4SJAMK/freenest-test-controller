#! /usr/bin/python

import xmlrpclib
import sys, os

if __name__ == "__main__":
	#arguments
	#s = sys.argv[1] + " " + sys.argv[2] #+ " " + sys.argv[3]
	#print s

	proxy = xmlrpclib.ServerProxy("http://localhost:8000/")
	results = proxy.executeTestCase({'testPlanID': '7', 'executionMode': 'now', 'platformID': 0, 'testCaseID': '3060', 'buildID': 2, 'testCaseVersionID': 3061, 'testCaseName': 'list_regression_tests', 'testProjectID': '6'})
	#results = proxy.executeTestCase({'testPlanID': '2372', 'executionMode': 'now', 'platformID': 0, 'testCaseID': '2082', 'buildID': 7, 'testCaseVersionID': 2753, 'testCaseName': 'CreatePaste', 'testProjectID': '1769'})
	print results['notes']
	
	if results['result'] == "p":
		sys.exit(0)
	else:
		sys.exit(-1)
