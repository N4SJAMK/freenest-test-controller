#! /usr/bin/python


"""
    Copyright (C) 2000-2012, JAMK University of Applied Sciences

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU testlink Public License as published by
    the Free Software Foundation, version 2.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>

"""


import testlink.testlinkapi
import sys, os, time
from twisted.python import log
import yaml
from datetime import datetime
from xml.etree import ElementTree as ET
from git_puller import gitpuller
from engine import Engine
from fnts.git_puller import gitpuller
from fnts.svn_puller import svnpuller
from fnts.TestLinkPoller import TestLinkPoller

class fnts:

    def __init__(self):
        self.engine = None
        self.customFields = {}
        self.conf = {}

    def run(self, data):

        try:
            #Load configurations from configuratiosn file
            self.loadConfigurations

            #Get custom fields from TestLinkAPI
            self.getCustomFields()

            #Update repo
            self.updateVersion()

            #Load correct engine
            self.loadEngine()

            #Run tests and return values
            return self.runTests()

        except Exception, e:
            return (-1, e, timestamp)

    def loadConfigurations(self):
        file = open('/etc/fnts.conf')
        self.conf = yaml.load(file)
        file.close

    def getCustomFields(self):
        api = TestLinkPoller(self.conf['testlink']['serverURL'], self.conf['testlink']['devkey'])
        if self.conf['general']['test_management'] == 'Testlink':
            self.customFields = api.getCusomFields(data, self.conf)
        else:
            self.customFields = api.getDefaultCustomFields()


    def loadEngine():

        cls = Engine
        engines = []

        path ="/usr/share/pyshared/fnts"
        for root, dirs, files in os.walk(path):
            for name in files:
                if name.endswith(".py") and name.startswith("engine_"):
                    path = os.path.join(root, name)
                    modulename = path.rsplit('.', 1)[0].replace('/', '.')
                    modulename = modulename.rsplit('.', 1)[1]
                    fntcprefix = "fnts." + modulename
                    try:
                        log.msg("Checking module:", modulename)
                        module = __import__(fntcprefix)

                        # walk the dictionaries to get to the last one
                        d = module.__dict__
                        for m in fntcprefix.split('.')[1:]:
                            d = d[m].__dict__

                        #look through this dictionary for the correct class
                        for key, entry in d.items():
                            if key == cls.__name__:
                                continue
                            try:
                                if issubclass(entry, cls):
                                    log.msg("Found engine:", key)
                                    engines.append(entry)
                            except TypeError:
                                #this happens when a non-type is passed in to issubclass. Non-types can't be instances, so they will be ignored.
                                continue
                    except Exception, e:
                        # if something goes wrong while loading modules, loading is aborted
                        log.msg('Error while loading modules:', str(e))

        if engines == []:
            log.msg('No test engines found')

        log.msg('engines found', engines)

        for e in engines:       #scroll through all found engines and find the correct one
            if e.__name__ == cfengine:
                self.engine = e(self.conf, cfengine, cfoutputdir, cftestdir, cfscheduled)
                break
        else:
            t = datetime.now()
            timestamp = t.strftime("%Y-%m-%d %H:%M:%S")
            log.msg('The correct testing engine was not found, tests cannot be run. Check the custom field value')
            raise Exception('Test engine was not found, check custom fields')


    def runTests(self):

        if self.engine is None:
            raise Exception('No test engine loaded')
        
        # getting testing scripts
        scriptlist = self.customFields['scripts'].split()

        engine_state = self.engine.init_environment()

        if engine_state == 1:
            # if everything is ok, run the tests
            log.msg('Starting Engine')

            engineresult = self.engine.run_tests(cftestname, scriptlist, cfruntimes)
            if engineresult != "ok":
                t = datetime.now()
                timestamp = t.strftime("%Y-%m-%d %H:%M:%S")
                log.msg('Engine error: ', engineresult)
                raise Exception('Engine error: ' + engineresult)
                engine_state = 0

        if engine_state == 1:
            # Trying to get the results from engine
            log.msg('Trying to get test results')
            results = engine.get_test_results(self.customFields['testname'], self.customFields['runtimes'], self.customFields['tolerance'])


        engine_state = engine.teardown_environment()

        if engine_state != 1:
            log.msg('Something went wrong while running engine')
            raise Exception('Engine error: ' + engineresult)
        else:
            self.costomFields = api.getDefaultCustomFields()


    def updateVersion(self):
        # checking the version control software and choosing the correct driver
        #TODO: this part could be more flexible
        #GIT
        if self.versioncontrol == "GIT":
            puller = gitpuller()
            gitresult = puller.pull(self.vTestdir, tag)
            if gitresult != "ok":
                log.msg('Git error, running old tests. ERROR:', gitresult)
            testdir = self.vTestdir
        #SVN
        elif self.versioncontrol == "SVN":
            puller = svnpuller()
            svnresult = puller.pull(self.vTestdir)
            if svnresult != "ok":
                log.msg('SVN error, running old tests. ERROR:', svnresult)
            #setting the testdir to point to the tests instead of the repository
            #if a tag is given and not found, the trunk is used as a test resource
            if tag == "null":
                testdir = self.vTestdir + "trunk/tests/"
            else:
                if os.path.exists(self.vTestdir + tag + "/tests/") != true:
                    log.msg("Tagged tests were not found from the repository, running tests from trunk")
                    testdir = self.vTestdir + "/trunk/tests/"
                else:
                    testdir = self.vTestdir + tag + "/tests/"
        #something else, not officially supported
        else:
            msg = "Version control driver for " + self.versioncontrol + " was not found, tests cannot be updated"
            log.msg(msg)




if __name__ == "__main__":

    pass
