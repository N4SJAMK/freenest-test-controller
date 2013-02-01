#! /usr/bin/python

"""
   Copyright (C) 2000-2012, JAMK University of Applied Sciences 

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, version 2.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>

"""

from twisted.web import xmlrpc, server
from twisted.application.internet import TCPServer
from twisted.application.service import Application
from twisted.internet import reactor
from twisted.python import log
from twisted.internet import threads


#   import xmlrpclib
import TestLinkAPI
import sys, os, time 
#import subprocess
from twisted.python import log  
import yaml 
#from config import conf
from datetime import datetime
from xml.etree import ElementTree as ET
from git_puller import gitpuller
#from engine_robot import robotEngine
#from engine import Engine
from fntc import fntc


class fntcService(xmlrpc.XMLRPC):
    """
    An example object to be published.
    """

    f = open('testlink_client.conf')
    conf = yaml.load(f)
    f.close

    vOutputdir = conf['testlink']['outputdirectory']
    vTestdir = conf['testlink']['testingdirectory']
    
    SERVER_URL = conf['testlink']['serverURL'] + "lib/api/xmlrpc.php"
    devKey = conf['testlink']['devkey']
    rResult = {}

    def executeTestCase(self, data):        
        log.msg('Got request from testlink')
        log.msg(data)
        log.msg('start testlink API')

	try:
        	# this starts up the Testlink API
        	client = TestLinkAPI.TestlinkAPIClient(self.SERVER_URL, self.devKey)

        	# polling some needed data from TL database using TestLink API
        	projectinfo=(client.getProjects())
        	log.msg('Got Testlink projects info: %s', projectinfo)
        	'''
        	 {'testPlanID': '1420', 'executionMode': 'now', 'platformID': 0, 'testCaseID': '1959',
        	  'buildID': 5, 'testCaseVersionID': 1960, 'testCaseName': 'LoginAdminUser', 'testProjectID': '15'}
        	'''

        
        	prefix = ""
        	i = 0
        	while prefix == "":
        	    if projectinfo[i]['id'] == data['testProjectID']:
        	        prefix = projectinfo[i]['prefix']
        	    else: 
        	        i = i + 1
        	
        	tcidlist=(client.getTestCaseIDByName(data['testCaseName']))
        	log.msg('Got test case IDs from poll: %s', tcidlist)
	
        	tcinfo=(client.getTestCase(prefix + "-" + tcidlist[0]['tc_external_id']))
        	log.msg('Got test case information from poll: %s', tcinfo)

        	tclist=(client.getTestCasesForTestPlan(data['buildID']))
        	log.msg('Got all test cases for Plan')

        	cfEngine=(client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[0]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "testingEngine", ""))
        	log.msg('Got engine from custom field: %s', cfEngine)

        	cfScripts=(client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[0]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "scriptNames", ""))
        	log.msg('Got runnable tests from custom field: %s', cfScripts)  
        
        	runtimes=(client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[0]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "runTimes", ""))
        	log.msg('Got runtimes from custom field: %s', runtimes)

        	tolerance=(client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[0]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "tolerance", ""))
        	log.msg('Got tolerance from custom field: %s', tolerance)

	except Exception, e:
                #TestlinkAPI might be broken
                log.msg('Getting data with TestlinkAPI failed:', str(e))
                log.msg('Using default values')

                cfEngine = "robotEngine"
                cfScripts = sys.argv[1] + ".txt"
                runtimes = 5
                tolerance = 80


       	
        puller = gitpuller()
        gitresult = puller.pull(self.vTestdir)
        if gitresult != "ok":
            log.msg('Git error, running old tests. ERROR:', gitresult)


        ''' talk with main program, send data and expect result '''
        log.msg('Running following scripts', cfScripts)
        f = fntc()
        try:
            runtimes = int(runtimes)
        except Exception, e:
            # runtimes is not a number
            log.msg('Custom field "RunTimes" contains an invalid value, tests will be run only once')
            runtimes = 1
        try:
            tolerance = int(tolerance)
        except Exception, e:
            log.msg('Custom field "Tolerance" contains an invalid value, resetting to default')
            tolerance = 100

        (result, notes, timestamp) = f.fntc_main(cfEngine, cfScripts, runtimes, tolerance, self.vOutputdir, self.vTestdir, 'now', data['testCaseName'])

        if(result == 1):
            self.rResult['result'] = 'p'
        elif(result == 0):
            self.rResult['result'] = 'f'
        else:
            self.rResult['result'] = 'b'

        self.rResult['notes'] = notes
        self.rResult['scheduled'] = 'now'
        t = datetime.now()
        self.rResult['timestampISO'] = t.strftime("%Y-%m-%d %H:%M:%S")

        log.msg('-----------------------------------------------------')
        log.msg('returning ', "{'result':" + self.rResult['result']+ ", 'notes':" +self.rResult['notes']+", 'scheduled':'now', 'timestampISO':"+self.rResult['timestampISO']+"}")
        log.msg('-----------------------------------------------------')
        return {'result':self.rResult['result'],'notes':self.rResult['notes'], 'scheduled':'now', 'timestampISO':self.rResult['timestampISO']}

    def xmlrpc_executeTestCase(self, data):
        return threads.deferToThread(self.executeTestCase, data)
        #value = self.executeTestCase(data)
        #log.msg(value)
        #return  {'result':'p', 'notes':'Message', 'scheduled':'now', 'timestampISO':'2012-09-26 11:33:08'}


if __name__ == '__main__':
    from twisted.internet import reactor
    import sys
    log.startLogging(sys.stdout)
    r = fntcService()
    reactor.listenTCP(8000, server.Site(r))
    reactor.run()    

else: # run the worker as a twistd service application: twistd -y xmlrpc_server.py --no_save
    from twisted.application import service, internet        
    application = service.Application('fntcservice')
    r = fntcService()
    website = internet.TCPServer(8000, server.Site(r))
    website.setServiceParent(application)
