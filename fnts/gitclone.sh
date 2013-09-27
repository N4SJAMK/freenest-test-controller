#!/bin/bash

eval `/usr/bin/ssh-agent -s`; ssh-add $1; git clone "$2"

exit
