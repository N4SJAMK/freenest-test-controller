#! /usr/bin/python

"""
Testlink API Sample Python Client implementation
"""
import xmlrpclib
import base64
import urllib2 

class TestlinkAPIClient:
    # substitute your server URL Here
    SERVER_URL = "https://strongbow.labranet.jamk.fi/ProjectTESTLINK/lib/api/xmlrpc.php"

    def __init__(self, devKey):
        self.server = xmlrpclib.Server(self.SERVER_URL)
        self.devKey = devKey
        print "devKey in init: %s" %devKey

    def getTestCaseIDByName(self,devKey):
        data = {"devKey":devKey, "testcasename":"Test Case 1", "testsuitename":"Test Suite 1"}
        return self.server.tl.getTestCaseIDByName(data)

    def reportTCResult(self, tcid, tpid, status):
        data = {"devKey":self.devKey, "tcid":tcid, "tpid":tpid, "status":status}
        return self.server.tl.reportTCResult(data)

    def getInfo(self):
        return self.server.tl.about()

    def sayHello (self):
        return self.server.tl.sayHello()

    def getProjects (self, devKey):
        print "DevKey: %s" %devKey
        data = {"devKey":devKey}
        return self.server.tl.getProjects(data)

if __name__ == '__main__':

    username = 'MikkOjala'
    password = 'dusty1'

    base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, 'https://stronbow.labranete.jamk.fi/ProjectTESTLINK/lib/api', username, password)

    handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(handler)
    urllib2.install_opener(opener)
    headers = {'X-Requested-With':'Demo'}
    uri = 'https://stronbow.labranete.jamk.fi/ProjectTESTLINK/lib/api'
    req = urllib2.Request(uri,None,headers)

    req.add_header("Authorization", "Basic %s" % base64string)
    result = urllib2.urlopen(req)
    print result.read()

    devKey = "26a3c5ceb98f1f79793bcb419b0891e1"
    # substitute your Dev Key Here
    client = TestlinkAPIClient (devKey)
    # get info about the server
    print client.getInfo()

    # retval = client.sayHello()

    #retval = client.getProjects(devKey)
#    retval = client.getTestCaseIDByName(devKey)

 #   print 'retval: ', retval
