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

import sys, os, time
from datetime import datetime
from xml.etree import ElementTree as ET
import re

import yaml
from twisted.python import log

from engine import Engine
from git_puller import gitpuller
from svn_puller import svnpuller
from TestLinkPoller import TestLinkPoller
import string

class fnts:

    def __init__(self):
        self.engine = None
        self.conf = {}
        self.data = None
        self.api = None

    def run(self, data):
        
        self.data = data

        try:
            #Load configurations from configuratiosn file
            self.loadConfigurations()

            #Get custom fields from TestLinkAPI
            self.setVariables()

            #Update repo
            self.updateVersion()

            #Load correct engine
            self.loadEngine()

            #Run tests and return values
            return self.runTests()

        except Exception, e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return (-1, str(e), timestamp)

    def loadConfigurations(self):
        file = open('/etc/fnts.conf')
        self.conf = yaml.load(file)
        file.close()
        os.environ['DISPLAY'] = self.conf['general']['display']

    def setVariables(self):
        if self.conf['general']['test_management'] == 'Testlink':
            self.api = TestLinkPoller(self.conf)
            variables = self.api.getCustomFields(self.data)
            self.completeVariables(variables)
        else:            
            self.completeVariables(self.data)

    def completeVariables(self, variables):

        # Check if default config file is given
        if 'confFile' in variables:
            file = open(variables['confFile'])
            fileVariables = yaml.load(file)
            file.close()
        else:
            fileVariables = {}

        self.conf['variables']['tag'] = self._helperCheckSteps([variables, fileVariables], 'tag') or 'null'
        self.conf['variables']['engine'] =  self._helperCheckSteps([variables, fileVariables], 'engine') or self.conf['variables']['default_engine']
        self.conf['variables']['runtimes'] =  self._helperCheckSteps([variables, fileVariables], 'runtimes') or self.conf['variables']['default_runtimes']
        self.conf['variables']['tolerance'] =  self._helperCheckSteps([variables, fileVariables], 'tolerance') or self.conf['variables']['default_tolerance']
        self.conf['variables']['scripts'] =  self._helperCheckSteps([variables, fileVariables], 'scripts') or variables['testCaseName'] + ".txt"

        testdir = self._helperCheckSteps([variables, fileVariables], 'testingdirectory')
        if testdir:
            self.conf['general']['testingdirectory'] = testdir
            
        outputdir = self._helperCheckSteps([variables, fileVariables], 'outputdirectory')
        if outputdir:
            self.conf['general']['outputdirectory'] = outputdir

        sutUrl = self._helperCheckSteps([variables, fileVariables], 'sutUrl')
        if sutUrl:
            for idx, item in enumerate(self.conf['variables']['dyn_args']):
                if 'IP' in item:
                    item = ['IP', sutUrl]
                    self.conf['variables']['dyn_args'][idx] = item
            

    # This method checks if any of the dicts provided contains variable var 
    # If some of the dicts contain var it returns it else it returns False.
    def _helperCheckSteps(self, steps, var):
        for step in steps:
            if var in step and step[var] != "":
                ret = step[var]
                break
        else:
            ret = False
        return ret


    def loadEngine(self):

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
            if e.__name__ == self.conf['variables']['engine']:
                self.engine = e(self.conf, "now")
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
        scriptlist = self.conf['variables']['scripts'].split()

        engine_state = self.engine.init_environment()

        if engine_state == 1:
            # if everything is ok, run the tests
            log.msg('Starting Engine')

            engineresult = self.engine.run_tests(self.sanitizeFilename(self.data['testCaseName']), scriptlist, self.conf['variables']['runtimes'])
            if engineresult != "ok":
                t = datetime.now()
                timestamp = t.strftime("%Y-%m-%d %H:%M:%S")
                log.msg('Engine error: ', engineresult)
                raise Exception('Engine error: ' + engineresult)
                engine_state = 0

        if engine_state == 1:
            # Trying to get the results from engine
            log.msg('Trying to get test results')
            results = self.engine.get_test_results(self.sanitizeFilename(self.data['testCaseName']), self.conf['variables']['runtimes'], self.conf['variables']['tolerance'])
            if self.conf['testlink']['uploadResults'] == True:
                self.engine.upload_results(self.data['testCaseID'], self.data['testCaseName'], self.conf['variables']['runtimes'])


        engine_state = self.engine.teardown_environment()

        if engine_state != 1:
            log.msg('Something went wrong while running engine')
            raise Exception('Engine error: ' + engineresult)
        else:
            return results



    def updateVersion(self):
        # checking the version control software and choosing the correct driver
        #TODO: this part could be more flexible
        #GIT
        if self.conf['general']['versioncontrol'] == "GIT":
            puller = gitpuller()
            gitresult = puller.pull(self.conf['general']['testingdirectory'], self.conf['variables']['tag'])
            if gitresult != "ok":
                log.msg('Git error, running old tests. ERROR:', gitresult)
            testdir = self.conf['general']['testingdirectory']
        #SVN
        elif self.conf['general']['versioncontrol'] == "SVN":
            puller = svnpuller()
            svnresult = puller.pull(self.vTestdir)
            if svnresult != "ok":
                log.msg('SVN error, running old tests. ERROR:', svnresult)
            #setting the testdir to point to the tests instead of the repository
            #if a tag is given and not found, the trunk is used as a test resource
            if self.conf['variables']['tag'] == "null":
                testdir = self.conf['general']['testingdirectory'] + "trunk/tests/"
            else:
                if os.path.exists(self.conf['general']['testingdirectory'] + self.customFields['tag'] + "/tests/") != true:
                    log.msg("Tagged tests were not found from the repository, running tests from trunk")
                    testdir = self.conf['general']['testingdirectory'] + "/trunk/tests/"
                else:
                    testdir = self.conf['general']['testingdirectory'] + self.customFields['tag'] + "/tests/"
        #something else, not officially supported
        else:
            msg = "Version control driver for " + self.conf['general']['versioncontrol'] + " was not found, tests cannot be updated"
            log.msg(msg)

    def sanitizeFilename(self, filename):
        filename = re.sub('\s', '_', filename)
        return filename



if __name__ == "__main__":

    pass
