#!/bin/sh

ssh-agent bash -c 'ssh-add /root/.ssh/root; git pull'

if [ -n "$1" ]; then
	git checkout tags/$1
else
	git checkout master
fi
