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

import os, re

from twisted.python import log
import yaml

from engine import Engine
from git_wrapper import gitwrapper
from svn_puller import svnpuller
from TestLinkPoller import TestLinkPoller


class fnts:

    def __init__(self, conf, cloud, daemon):
        self.engine = None
        self.conf = conf
        self.data = None
        self.cloud = cloud
        self.daemon = daemon
        self.useReceivedTests = "false"

    def run(self, data):
        
        self.data = data

        try:
            if len(self.data['script'].strip()) != 0:
                self.writeScriptToFile()
            elif len(self.data['gitRepository'].strip()) != 0:
                #Update repo
                self.updateVersion()
            

            #Get custom fields from TestLinkAPI
            self.setVariables()

            #Load correct engine
            try:
                self.simpleLoadEngine()
            except Exception, e:
                engines = self.searchEngines()
                if engines != []:
                    self.loadEngine(engines)
                else:
                    raise Exception('No testing engines found!')

            #Run tests and return values
            return self.runTests()

        except Exception, e:
            return (-1, str(e), self.cloud)

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
            confFile = variables['confFile']
            confDir = os.path.dirname(confFile)
            # Pull the conf file directory in case it's a git repository
            puller = gitpuller()
            puller.pull(confDir, 'null')
            # Read the config file
            cFile = open(confFile)
            fileVariables = yaml.load(cFile)
            cFile.close()
        else:
            fileVariables = {}

        self.conf['variables']['tag'] = self._helperCheckSteps([variables, fileVariables], 'tag') or 'null'
        self.conf['variables']['engine'] =  self._helperCheckSteps([variables, fileVariables], 'engine') or self.conf['variables']['default_engine']
        self.conf['variables']['scripts'] =  self._helperCheckSteps([variables, fileVariables], 'scripts') or self.data['testCaseName'] + ".txt"
        try:
            self.conf['variables']['runtimes'] =  int(self._helperCheckSteps([variables, fileVariables], 'runtimes')) or self.conf['variables']['default_runtimes']
            self.conf['variables']['tolerance'] =  int(self._helperCheckSteps([variables, fileVariables], 'tolerance')) or self.conf['variables']['default_tolerance']
        except ValueError, e:
            raise Exception("Can't convert customfield to int " + str(e))

        if self.useReceivedTests != "true":
            testdir = self._helperCheckSteps([variables, fileVariables], 'gitLocation')
        else:
            testdir = self.conf['general']['writtentestdirectory']
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


    def searchEngines(self):

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
        else:
            log.msg('engines found: ', str(engines))

        return engines

    def loadEngine(self, engines):
        for e in engines:       #scroll through all found engines and find the correct one
            if e.__name__ == self.conf['variables']['engine']:
                self.engine = e(self.conf, "now")
                break
        else:
            log.msg('The correct testing engine was not found, tests cannot be run. Check the custom field value')
            raise Exception('The correct test engine was not found, check the custom field value')
        
    def simpleLoadEngine(self):
        varEngine = self.conf['variables']['engine']
        if varEngine == "gridEngine":
            module = __import__("fnts.engine_grid")
            self.engine = module.engine_grid.gridEngine(self.conf, 'now')
        elif varEngine == "robotEngine":
            module = __import__("fnts.engine_robot")
            self.engine = module.engine_robot.robotEngine(self.conf, 'now')
        elif varEngine == "cloudEngine":
            module = __import__("fnts.engine_cloud")
            self.engine = module.engine_cloud.cloudEngine(self.conf, 'now')
            self.cloud = self.engine.cloudInit(self.cloud)
        else:
            raise Exception('Unknown engine ' + varEngine)

    def runTests(self):

        if self.engine is None:
            raise Exception('No test engine loaded')
        
        # getting testing scripts
        scriptlist = self.conf['variables']['scripts'].split()

        engine_state = self.engine.init_environment()

        if engine_state == 1:
            # if everything is ok, run the tests
            log.msg('Starting Engine')

            engineresult = self.engine.run_tests(self.sanitizeFilename(self.data['testCaseName']), scriptlist, self.conf['variables']['runtimes'], self.daemon)
            if engineresult != "ok":
                engine_state = 0
                log.msg('Engine error: ', engineresult)
                raise Exception('Engine error: ' + engineresult)

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
            results.append(self.cloud)
            return results



    def updateVersion(self):
        # checking the version control software and choosing the correct driver
        #TODO: this part could be more flexible
        #GIT
        if self.conf['general']['versioncontrol'] == "GIT":
            wrapper = gitwrapper()
            gitrepository = self.data['gitrepository']
            gitresult = wrapper.gitrun(self.conf['general']['testingdirectory'], gitrepository, self.conf['variables']['tag'])
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
                if os.path.exists(self.conf['general']['testingdirectory'] + self.customFields['tag'] + "/tests/") != True:
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

    def writeScriptToFile(self):
        log.msg(self.data['script'])
        
        try:
            file = self.conf['general']['writtentestdirectory'] + self.data['scripts']
            f = open(file, 'w')
            f.write(self.data['script'])
            f.close()
            log.msg('Script written to file')
            self.useReceivedTests = "true"
        except Exception, e:
            log.msg('ERROR: Writing the script to a file failed!' + str(e))


if __name__ == "__main__":

    pass
