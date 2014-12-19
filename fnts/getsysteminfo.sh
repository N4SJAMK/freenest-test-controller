#!/bin/bash

lshw -xml > /tmp/systeminfo.xml
lsb_release -a > /tmp/release
uname -i > /tmp/architecture 
