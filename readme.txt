FreeNest Test Service (fnts)

Overview

Freenest Test Service is a small service coded in Python and using Twisted Framework, 
listening to port 8000 for XML-RPC calls. Once the service receives a call with correct information, it will 
try to find runnable tests based on the data, run the tests against a target and finally return the results back to the caller.

FNTS requires at least the amount of test runs, the name of the test run, a list of test script names, the preferred 
testing engine, and the tolerance in order to run the tests. After the tests have been run, it will return the result, 
test notes including possible error messages, and a time stamp.

If using Robot Framework as the test engine, the user can also pass a test scrip within the call, in which case it is saved
into a file and run against the target. 

Please notice that the service is still in development meaning that there will be bugs.

Contributors: Niko Korhonen, Mikko Ojala, Janne Alatalo, Henri Tervakoski

Requirements

lorem ipsum...


Building the package

lorem ipsum...

$dpkg-buildpackage 


Setting up Testlink on FreeNest

lorem ipsum...

Setting up test client to match Testlink on Freenest

lorem ipsum...



Running daemon

lorem ipsum...
