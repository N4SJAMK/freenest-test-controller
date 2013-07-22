import json
import urllib2

from twisted.python import log

class Cloud():
    
    def __init__(self, conf):
        self.conf = conf
        self.token = None
        self.tokenIsValid = False
        self.InstanceManager = InstanceManager(self)
        
    def getToken(self):
        log.msg("Requesting cloud auth token")     
        url = self.conf['cloud']['OS_AUTH_URL'] + '/tokens'
        postData = '{"auth":{"passwordCredentials":{"username":"' + self.conf['cloud']['OS_USERNAME'] +'","password":"' + self.conf['cloud']['OS_PASSWORD'] + '"},"tenantId":"' + self.conf['cloud']['OS_TENANT_ID'] + '"}}'
        header = { 'Content-type' : "application/json" }
        try:
            req = urllib2.Request(url, postData, header)
            res = urllib2.urlopen(req)
            content = res.read()
            jsondata = json.loads(content)
            if jsondata['access']['token']['id'] is not None:
                log.msg("Got token")
                self.token = jsondata
                self.tokenIsValid = True
                return True
        except Exception, e:
            log.msg("Couldn't get token " + str(e))
            self.tokenIsValid = False
            return False
    
    def apiRequest(self, uri="", postData=None):  
        
        #TODO: check if token is about to expire
        
        if self.tokenIsValid is False:
            if not self.getToken():
                raise Exception("No valid token, can't do API request")
        
        apiEndpoints = self.token['access']['serviceCatalog']
        url = ""
                
        # TODO: if uri == /servers;
        # get compute url
        for endpoint in apiEndpoints:
            if endpoint['type'] == "compute":
                url = endpoint['endpoints'][0]['publicURL'] + uri
                break
        
        header = { 'X-Auth-Token' : self.token['access']['token']['id'] }
        
        if postData is not None:
            header['Content-type'] = 'application/json' 
               
        try:
            req = urllib2.Request(url, postData, header)
            res = urllib2.urlopen(req)
            content = res.read()
            return content
        except Exception, e:
            log.msg("API request failed: " + str(e))

class InstanceManager:

    def __init__(self, cloud):
        self.cloud = cloud
        self.instances = 0
        self.active = []
        self.suspended = []
        self.paused = []
        self.busy = 0
        self.IdReserve = []
        
            
    def listInstances(self):
        r = self.cloud.apiRequest("/servers/detail", None)
        jsondata = json.loads(r)
        instances = len(jsondata['servers'])
        log.msg("List of " + str(instances) +" cloud instances:")
        for server in jsondata['servers']:
            print server
        
    def getNodeInstances(self):
        self.instances = 0
        self.active[:] = []
        self.suspended[:] = []
        self.paused[:] = []
        self.IdReserve[:] = []
        r = self.cloud.apiRequest("/servers/detail", None)
        jsondata = json.loads(r)
        for server in jsondata['servers']:
            if 'FNTS' in server['metadata']:
                if server['metadata']['FNTS'] == 'node':
                    self.instances = self.instances + 1
                    self.IdReserve.append(int(server['metadata']['ID']))
                    status =  server['OS-EXT-STS:vm_state']
                    if status == 'active':
                        self.active.append(server['id'])
                    elif status == 'suspended':
                        self.suspended.append(server['id'])
                    elif status == 'paused':
                        self.paused.append(server['id'])
                    else:
                        log.msg(server['name'] + ' with bad status: ' + status )
        strActive = ""
        strSuspended = ""
        strPaused = ""
        activeCount = len(self.active)
        suspendedCount = len(self.suspended)
        pausedCount = len(self.paused)
        if activeCount > 0:
            strActive = str(activeCount) + " active"
        if suspendedCount > 0:
            strSuspended = str(suspendedCount) + " suspended"
            if strActive != "":
                strSuspended = ", " + strSuspended
        if pausedCount > 0:
            strPaused = str(pausedCount) + " paused"
            if (strActive != "" or strSuspended != ""):
                strPaused = ", " + strPaused
                
        log.msg(str(self.instances) + ' nodes in cloud: ' + strActive + strSuspended + strPaused)
    
    def launchInstance(self, pImage="FNTS-NODE", pFlavor="m1.tiny1", pName="FNTS-NODE", pFntsMeta="node"):
        imageId = ""
        flavorId = ""
        r = self.cloud.apiRequest("/images", None)
        images = json.loads(r)
        
        for image in images['images']:
            if image['name'] == pImage:
                imageId = image['id']
                break
        if imageId == "":
            raise Exception('No image matching ' + pImage)
        
        r = self.cloud.apiRequest("/flavors", None)
        flavors = json.loads(r)
        
        for flavor in flavors['flavors']:
            if flavor['name'] == pFlavor:
                flavorId = flavor['id']
                break
        if flavorId == "":
            raise Exception('No flavor matching ' + pFlavor)
        
        nodeId = self.getId()
        self.IdReserve.append(nodeId)
        pName = pName + "-" + (str(nodeId)).zfill(3)
        
        postData = '{"server":{"imageRef":"' + imageId + '","flavorRef":"'+ flavorId +'","name":"' + pName + '","metadata":{"FNTS":"' + pFntsMeta + '","ID":"'+ str(nodeId) +'"},"key_name":"fntskey"}}'
        log.msg("Launching a new instance " + pName)
        r = self.cloud.apiRequest('/servers', postData)
        response = json.loads(r)
        response['server']['nodeName'] = pName
        return response
            
    def getInstanceProgress(self, pInstanceId="a27bc588-639e-493c-a876-0cc895cffa31"):
        r = self.cloud.apiRequest("/servers/" + pInstanceId, None)
        jsondata = json.loads(r)
        if 'progress' in jsondata['server']:
            return int(jsondata['server']['progress'])
        else:
            log.msg("No such instance: " + pInstanceId)
            return 0
        
    def getInstanceDetails(self, pInstanceId="a27bc588-639e-493c-a876-0cc895cffa31", nodeName=True):
        r = self.cloud.apiRequest("/servers/" + pInstanceId, None)
        jsondata = json.loads(r)
        jsondata['server']['nodeName'] = jsondata['server']['name']
        return jsondata

    def suspendInstance(self, pInstanceId):
        return self.cloud.apiRequest("/servers/" + pInstanceId + "/action", '{"suspend":null}')
    
    def resumeInstance(self, pInstanceId):
        return self.cloud.apiRequest("/servers/" + pInstanceId + "/action", '{"resume":null}')
    
    def getId(self):
        nodeId = 1
        found = False
        while not found:
            if nodeId not in self.IdReserve:
                self.IdReserve.append(nodeId)
                return nodeId
            else:
                nodeId = nodeId + 1
            
