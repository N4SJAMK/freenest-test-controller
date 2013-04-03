from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm
from datetime import datetime
import os
import yaml

def mark_log(testCaseName):
	f = open(os.path.dirname(os.path.realpath(__file__)) + '/testlink_client.conf')
	conf = yaml.load(f)
	f.close

	env.password = conf['general']['slave_pass']
	logs = conf['log_collecting']['logs']

	# mark the point in the log where the test started running
	t = datetime.now()
	time = t.strftime("%Y-%m-%d %H:%M:%S")
	msg = '------------ Test Case \"' + testCaseName + '\" was started ' + time + ' ------------'
	for log in logs:
		sudo('echo ' + msg + ' >> ' + log)


def mark_log_end(testCaseName):
	f = open(os.path.dirname(os.path.realpath(__file__)) + '/testlink_client.conf')
	conf = yaml.load(f)
	f.close

	env.password = conf['general']['slave_pass']
	logs = conf['log_collecting']['logs']

        # mark the point in the log where the test ended
        t = datetime.now()
        time = t.strftime("%Y-%m-%d %H:%M:%S")
        msg = '------------ Test Case \"' + testCaseName + '\" ended ' + time + ' ------------'
        for log in logs:
		sudo('echo ' + msg + ' >> ' + log)


def collect_log(logdir):
	f = open(os.path.dirname(os.path.realpath(__file__)) + '/testlink_client.conf')
	conf = yaml.load(f)
	f.close

	env.password = conf['general']['slave_pass']
	user = conf['general']['slave_user']
	logs = conf['log_collecting']['logs']

	run('mkdir ~/logs')	

	# extract log files
	for log in logs:
		sudo('cp -r ' + log + ' ~/logs/')
	sudo('chown -R ' + user + ':' + user + ' ~/logs/')
	packname = "logs_" + env.host.rsplit('.',1)[1] + ".tar"
	run('cd ~ | tar -cvf ' + packname + ' logs/')
	get(('~/' + packname), (logdir + '/'))
