#! /usr/bin/python


"""
    Copyright (C) 2000-2014, JAMK University of Applied Sciences

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

import os, re, subprocess

from twisted.python import log


class get_system_info:

    def __init__(self):
        log.msg("Getting system info...")


    def getInfo(self):
         info = subprocess.Popen(['sh','getsysteminfo.sh'],cwd='/usr/share/pyshared/fnts/',stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            

if __name__ == "__main__":

    pass
