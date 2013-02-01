from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from daemon import Daemon
import time, sys, os
import datetime
import socket
import SocketServer

sleeptime = 10

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2','/')


# Threaded mix-in
class AsyncXMLRPCServer(SocketServer.ThreadingMixIn,SimpleXMLRPCServer): 
    pass
# Forked version
'''class AsyncXMLRPCServer( SocketServer.ForkingMixIn,SimpleXMLRPCServer): 
   pass'''


# Register a function under a different name
def executeTestCase(x):
    print x
    return {'result':'p', 'notes':'Message', 'scheduled':'now', 'timestampISO':'2012-09-26 11:33:08'}



class TestlinkDaemon(Daemon):
    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80))
        ip = s.getsockname()[0]
        print ip
        s.close()

        server = AsyncXMLRPCServer((ip, 8000), requestHandler=RequestHandler)
        server.register_introspection_functions()

        server.register_function(executeTestCase, 'executeTestCase')

        # Run the server's main loop
        server.serve_forever()
        while True:
            time.sleep(sleeptime)            
            '''newstatus = repo.iter_commits('master', max_count=1)
                if newstatus != status:
                    logging.debug('repo status changed, tests should be re-run!')
                    status = newstatus'''



if __name__ == "__main__":
    daemon = TestlinkDaemon('/tmp/testlinkdaemon.pid')
    if len(sys.argv) == 2:
            if 'start' == sys.argv[1]:
                    daemon.start()
            elif 'stop' == sys.argv[1]:
                    daemon.stop()
            elif 'restart' == sys.argv[1]:
                    daemon.restart()
            else:
                    print "Unknown command"
                    sys.exit(2)
            sys.exit(0)
    else:
            print "usage: %s start|stop|restart" % sys.argv[0]
            sys.exit(2)