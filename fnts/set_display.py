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

from twisted.python import log
import os, fnmatch
import subprocess

class setDisplay:

    def __init__(self, conf):
        #class for checking and setting virtual displays
        self.vncDir = conf['vnc']['vncdir']
        self.hostname = self.get_hostname()
        self.reserved = []

        log.msg('Started the display finder...')


    def check_password(self):
        # The password is crypted, but if the file exists, 
        # we can assume the password is set
        if os.path.isfile(self.vncDir + 'passwd'):
            return True
        else:
            return False


    def check_displays(self):
        # check if there are virtual displays running
        displays = []
        pattern = '*.pid'

        # find the pid files of the displays and check if the processes exist
        for root, dirs, files in os.walk(self.vncDir):
            for name in files:
                if fnmatch.fnmatch(name, pattern):
                    display = os.path.join(root, name)
                    log.msg(display)
                    with open(display, 'r') as f:
                        if self.check_pid(int(f.readline())):
                            disNumber = display.split(':')[1].split('.')[0]
                            log.msg(str(disNumber))
                            displays.append(disNumber)

        log.msg('found displays: ' + str(displays))

        if len(displays) == 0:
            log.msg('no active displays found, creating a new one...')
            self.create_display(None)

        return displays


    def set_display(self, displays, iDisplay):
        #set a display for the next process, iDisplay is the preferred display
        finaldisplay = None
        while not finaldisplay:
            if iDisplay:
                if iDisplay not in self.reserved:
                    finaldisplay = iDisplay
            else:
                for display in displays:
                    if display not in self.reserved:
                        finaldisplay = display
        return finaldisplay


    def create_display(self, iDisplay):
        #create a new display
        cmd = ['vnc4server']

        if iDisplay: # if display number is given, add it to the command
            cmd.append(':' + iDisplay)
            
        retDisplay = subprocess.Popen(cmd,cwd=self.vncDir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()

        log.msg(str(retDisplay))
        return display
    

    def get_hostname(self):
        #find out the server's hostname
        with open('/etc/hostname', 'r') as f:
            hostname = f.readline()
        return hostname


    def check_pid(self, pid):
        #check if the process exists
        #log.msg('pid: ' + str(pid))
        if os.path.lexists('/proc/%s' % pid):
            log.msg('process ' + str(pid) + ' found')
            return True
        else:
            log.msg('process ' + str(pid) + ' not found')
            return False
