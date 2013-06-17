#!/bin/sh

if [ $# = 0 ]; then
    echo no parameters, exiting
    exit 1
fi

CURDIR=$PWD

cd $1

ssh-agent bash -c 'ssh-add /root/.ssh/root; git pull'

if [ -n "$2" ]; then
	git checkout tags/$2
else
	git checkout master
fi

cd $CURDIR
