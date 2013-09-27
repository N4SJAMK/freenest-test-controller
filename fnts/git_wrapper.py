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
        self.SSH_KEY="/var/lib/fnts/.ssh/id_rsa"
        log.msg("initialized gitwrapper")

    def gitrun(self, testdir, repository, tag):
        #check if the repository has been cloned already. if not, then clone it, otherwise pull
        reposplit = repository.split(":")
        repo = reposplit[len(reposplit) - 1].split("/")
        reponame = repo[len(repo) - 1]

        #agentstr = "eval `ssh-agent -s`"
        #agentcmd = agentstr.split()
        #agent = subprocess.Popen(agentstr,shell=True,cwd=testdir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
        #print agent

        inGit = ["false"]
        dir = testdir + reponame
        log.msg("testdir:", testdir)
        try: 
            inGit = subprocess.Popen("git rev-parse --is-inside-work-tree".split(),cwd=dir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            log.msg(str(inGit))
        except Exception as e:
            inGit[0] = "false"
        if inGit[0] == "true\n":
            return self.pull(dir, repository, tag)
        else:
            return self.clone(testdir, repository, reponame, tag)


    def pull(self, testdir, repository, tag):
        try:
            # let's try to pull the repository
            #fntsDir = os.path.dirname(os.path.realpath(__file__))
            command = "/usr/share/pyshared/fnts/gitpull.sh /var/lib/fnts/.ssh/id_rsa"
            cmd = command.split()

            log.msg("testdir:", testdir)
            log.msg("pulling repository", str(repository))
            gitpull = subprocess.Popen(cmd,cwd=testdir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            log.msg("Git process output:", str(gitpull))

            switchtag = "null"
            if tag != "null":
                tagcommand = "git checkout tags/" + tag
                tagcmd = tagcommand.split()

                log.msg("switching to tag", tag)
                switchtag = subprocess.Popen(tagcmd,cwd=testdir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            # check and raise an exception if errors occur
            if str(gitpull[0]).find == ' ' or str(switchtag[0]).find == ' ':
                raise Exception(str(gitpull[1]) + str(switchtag[1]))
            else:
                return "ok"
        except Exception as e:
            # if something weird happens, a message will be returned and old tests are run
            log.msg('GIT process exception:', str(e))
            return str(e)


    def clone(self, testdir, repository, reponame, tag):
        try:
            #let's try cloning the repository
            command = "/usr/share/pyshared/fnts/gitclone.sh /var/lib/fnts/.ssh/id_rsa " + repository
            cmd = command.split()

            log.msg("cloning repository", str(repository))
            gitclone = subprocess.Popen(cmd,cwd=testdir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            log.msg("Git process output:", str(gitclone))

            switchtag = "null"
            if tag != "null":
                tagcommand = "git checkout tags/" + tag
                tagcmd = tagcommand.split()

                log.msg("switching to tag", tag)
                dir = testdir + reponame
                switchtag = subprocess.Popen(tagcmd,cwd=dir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            if str(gitclone[0]).find == ' ' or str(switchtag[0]).find == ' ':
                raise Exception(str(gitclone[1]) + str(switchtag[1]))
            else:
                return "ok"
        except Exception as e:
            # if something weird happens, a message will be returned
            log.msg('GIT process exception:', str(e))
            return str(e)
