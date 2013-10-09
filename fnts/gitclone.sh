#!/bin/bash

echo "scanning for host key..."
ssh-keyscan -t rsa,dsa $3 2>&1 | sort -u - ~/.ssh/known_hosts > ~/.ssh/tmp_hosts
cat ~/.ssh/tmp_hosts >> ~/.ssh/known_hosts
#rm ~/.ssh/tmp_hosts

echo "adding identity and cloning..."
eval `/usr/bin/ssh-agent -s`; ssh-add $1; git clone "$2"

exit
