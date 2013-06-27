#!/bin/sh
SSH_KEY="/var/lib/fnts/.ssh/fnts"

if [ $# = 0 ]; then
    echo no parameters, exiting
    exit 1
fi

CURDIR=$PWD

cd $1

isgitrepo=`git rev-parse --is-inside-work-tree`

if [ "$isgitrepo" = "true" ]; then
    if [ -f $SSH_KEY ]; then
        ssh-agent bash -c "ssh-add $SSH_KEY; git pull"

        if [ -n "$2" ]; then
                git checkout tags/$2
        else
            git checkout master
        fi
    else
        echo "Can't find fnts ssh key from $SSH_KEY"
        exit 1
    fi
fi

cd $CURDIR
exit 0
