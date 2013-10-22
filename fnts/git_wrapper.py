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

import sys
import os
import subprocess
from twisted.python import log

class gitwrapper:

    def __init__(self):
        #might use this spot for something...
        self.SSH_KEY="/var/lib/fnts/.ssh/fnts"
        log.msg("initialized gitwrapper")

    def gitrun(self, testdir, repository, tag):
        
        #check if the repository has been cloned already. if not, then clone it, otherwise pull
        reposplit = repository.split(":")
        repo = reposplit[len(reposplit) - 1].split("/")
        reponame = repo[len(repo) - 1]
        try:
            host = reposplit[0].split("@", 1)[1]
        except Exception, e:
            host = reposplit[0]
        
        # check if the testing directory exists
        if not os.path.isdir(testdir):
            os.makedirs(testdir)

        dir = testdir + reponame
        inGit = self.checkGit(dir)

        if inGit[0] == "true\n":
            gitresult =  self.pull(dir, repository, tag)
        else:
            gitresult =  self.clone(testdir, repository, reponame, host, tag)
            
        return gitresult, reponame


    def pull(self, testdir, repository, tag):
        try:
            # let's try to pull the repository
            #fntsDir = os.path.dirname(os.path.realpath(__file__))
            command = "/usr/share/pyshared/fnts/gitpull.sh " + self.SSH_KEY
            cmd = command.split()

            log.msg("testdir:", testdir)
            log.msg("pulling repository", str(repository))
            gitpull = subprocess.Popen(cmd,cwd=testdir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            log.msg("Git process output:", str(gitpull))

            switchtag = "null"
            if tag and tag != "null":
                tagcommand = "git checkout tags/" + tag
                tagcmd = tagcommand.split()

                log.msg("switching to tag", tag)
                switchtag = subprocess.Popen(tagcmd,cwd=testdir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            # check and raise an exception if errors occur
            if str(gitpull[0]).find == ' ' or str(switchtag[0]).find == ' ':
                raise Exception(str(gitpull[1]) + "\n" + str(switchtag[1]))
            else:
                return "ok"
        except Exception as e:
            # if something weird happens, a message will be returned and old tests are run
            log.msg('GIT process exception:', str(e))
            return str(e)


    def clone(self, testdir, repository, reponame, host, tag):
        try:
            #let's try cloning the repository
            command = "/usr/share/pyshared/fnts/gitclone.sh " + self.SSH_KEY + " " + repository + " " + host
            cmd = command.split()

            log.msg("cloning repository", str(repository))
            gitclone = subprocess.Popen(cmd,cwd=testdir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            log.msg("Git process output:", str(gitclone))

            # check if the repo exists. if not, cloning failed
            inGit = self.checkGit(testdir + reponame + "/")
            if inGit[0] == "true\n":
                #repo exists, check for tags
                switchtag = ""
                if tag and tag != "null":
                    tagcommand = "git checkout tags/" + tag
                    tagcmd = tagcommand.split()

                    log.msg("switching to tag", tag)
                    dir = testdir + reponame
                    switchtag = subprocess.Popen(tagcmd,cwd=dir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()

                if str(gitclone[0]).find == ' ':
                    try:
                        if str(switchtag[0]).find == ' ':
                            raise Exception(str(switchtag[1]))
                    except IndexError, e:
                        #no tags, so just ignore this
                        pass
                    except Exception, e:
                        #something is wrong with tags
                        return str(e)
                    #something went wrong while cloning
                    raise Exception(str(gitclone[1]))
                else:
                    #it's good!
                    return "ok"
            else:
                return "Failed to clone the repository: " + gitresult

        except Exception as e:
            # if something weird happens, a message will be returned
            log.msg('GIT process exception:', str(e))
            return str(e)

    def checkGit(self, dir):
        inGit = ["false\n"]
        log.msg("testdir:", dir)
        try:
            inGit = subprocess.Popen("git rev-parse --is-inside-work-tree".split(),cwd=dir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            log.msg(str(inGit))
        except Exception as e:
            inGit = ["false\n"]

        return inGit
