#!/bin/bash

eval `ssh-agent -s`; ssh-add $1; git pull

exit
