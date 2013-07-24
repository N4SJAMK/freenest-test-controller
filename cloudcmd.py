import fnts, json, yaml, shlex, sys
from fnts import Cloud

class Commander:
    
    def __init__(self):
        self.cmd("help")
        
        self.done = False
        
        file = open('/etc/fnts.conf')
        self.conf = yaml.load(file)
        file.close()
        
        self.cloud = Cloud.Cloud(self.conf)
        
        while not self.done:
            input = raw_input('> ')
            self.cmd(input)
               
    def cmd(self, input):
        
        s = ["","","",""]
        
        try:
            sh = shlex.split(input)
            for str in sh:
                s[sh.index(str)] = str
        except Exception():
            return
        
        if s[0] == "quit":
            self.done = True
            
        elif s[0] == "help":
            print("Commands:")
            print("quit, list, launch, terminate")
            
        elif s[0] == "list":
            if s[1] == "instances":
                self.cloud.InstanceManager.listInstances()
                
            elif s[1] == "flavors":
                r = self.cloud.apiRequest("/flavors", None)
                flavors = json.loads(r)
                for flavor in flavors['flavors']:
                    print flavor['name']
                    
            elif s[1] == "images":
                r = self.cloud.apiRequest("/images", None)
                images = json.loads(r)
                for image in images['images']:
                    print image['name']
                
            else:
                print("list [instances, flavors, images]")
        
        elif s[0] == "launch":
            if s[3] == "":
                print "launch <name> <image> <flavor>"
                return
            imageId = ""
            flavorId = ""
            r = self.cloud.apiRequest("/images", None)
            images = json.loads(r)
            
            for image in images['images']:
                if image['name'] == s[2]:
                    imageId = image['id']
                    break
            if imageId == "":
                print('No image matching ' + s[2])
                return
            
            r = self.cloud.apiRequest("/flavors", None)
            flavors = json.loads(r)
            
            for flavor in flavors['flavors']:
                if flavor['name'] == s[3]:
                    flavorId = flavor['id']
                    break
            if flavorId == "":
                print('No flavor matching ' + s[3])
                return
                        
            postData = '{"server":{"imageRef":"' + imageId + '","flavorRef":"'+ flavorId +'","name":"' + s[1] + '"}}'
            r = self.cloud.apiRequest('/servers', postData)
            response = json.loads(r)
            print response
        
        elif s[0] == "terminate":
            iid = ""
            if s[1] == "":
                print "terminate <instance>"
                return
            else:
                r = self.cloud.apiRequest("/servers", None)
                jsondata = json.loads(r)
                for server in jsondata['servers']:
                    if server['name'] == s[1]:
                        iid = server['id']
                
                if iid == "":
                    print "Did not find instance with name " + s[1]
                    return
                else:
                    r = self.cloud.apiRequestWithMethod("/servers/" + iid, "DELETE")
        
c = Commander()