import datetime
import xmlrpclib

s = xmlrpclib.ServerProxy('http://192.168.42.104:8000')


print s.executeTestCase({'testPlanID': '1420', 
	'executionMode': 'now', 
	'platformID': '0', 
	'testCaseID': '1959', 
	'buildID': '5', 
	'testCaseVersionID': '1960', 
	'testCaseName': 'LoginAdminUser', 
	'testProjectID': '15'})
# Print list of available methods
print s.system.listMethods()

#print s.system.methodHelp('executeTestCase')


for t, v in [ ('boolean', True), 
              ('integer', 1),
              ('floating-point number', 2.5),
              ('string', 'some text'), 
              ('datetime', datetime.datetime.now()),
              ('array', ['a', 'list']),
              ('array', ('a', 'tuple')),
              ('structure', {'a':'dictionary', 'b':'what'}),
            ]:

             print '%-22s:' % t, v