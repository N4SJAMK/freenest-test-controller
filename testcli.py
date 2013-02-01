import xmlrpclib

s = xmlrpclib.ServerProxy('http://localhost:8000')
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