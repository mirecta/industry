#!/usr/bin/python

import time
import BaseHTTPServer
import urlparse
import socket
from datetime import timedelta, datetime
from multiprocessing import Process, Value, Queue, Lock
import sys
import signal

from daemonize import Daemonize


SENSORS=2

DOC_ROOT = '/home/pi/thermometer/www/'
INTERVAL = '/home/pi/thermometer/interval'
PID = '/tmp/thermometer.pid'
PIN1=4 # pin of DHT sensor
PIN2=17 
SADDRESS = 0x20 # address of mcp sensor
HOST_NAME = '' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 8080 # Maybe set this to 9000.
SENSOR='DHT'  # or DHT

if SENSOR == 'MCP':
    import Adafruit_MCP9808.MCP9808 as MCP9808
elif SENSOR == 'DHT':
    import Adafruit_DHT
#endif


mimeTypes = {'png':"image/png", 
            'jpg':"image/jpeg", 
            'jpeg':"image/jpeg", 
            'htm':"text/html",
            'html':"text/html",
            'js':"application/javascript",
            'css':"text/css",
            'txt':"text/plain",
            'xml':"text/xml",
            'php':"text/html"}



def getOneInt(p,name,default):
    """
    """
    value = p.get(name)
    if value == None:
        return default
    else:
        return int(value[0])
    #endif
#enddef

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        """Respond to a GET request."""
        
        url = urlparse.urlparse(self.path)
        params = urlparse.parse_qs(url.query)

        parts = url.path.lower().split('.')
        if (len(parts) > 1 and mimeTypes.get(parts[-1])) or url.path == '/':
            self.handleStatic(url,params)
            
        elif url.path == "/set":
            self.handleSet(url,params)
        elif url.path == "/now":
            self.handleNow(url,params)
        elif url.path == "/get":
            self.handleGet(url,params)

        else:

            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write("<html><head><title>Title goes here.</title></head>")
            self.wfile.write("<body><p>%s Not found </p></body></html>" % (url.path))

        #endif
    #enddef
  
    def handleGet(self,url,params):
        sensor = getOneInt(params,"sensor",1)
        
        
        self.send_response(200)
        self.send_header("Content-type","text/plain") 
        self.end_headers()
        while not queues[sensor - 1].empty():
            self.wfile.write('|'.join(queues[sensor - 1].get()))
            self.wfile.write("\n")
        #endwhile
    #enddef

    def handleNow(self,url,params):
        """
        """
        data = readSensors()
        sensor = getOneInt(params,"sensor",1)

        self.send_response(200)
        self.send_header("Content-type","text/plain") 
        self.end_headers()
        self.wfile.write('|'.join(data[sensor - 1]))
        self.wfile.write("\n")

    #enddef
    
    def handleSet(self,url,params):
        """
        """
        global process
        try:
            interval = params['interval'][0]
            fl = open(INTERVAL, "wt")
            fl.write(interval)
            fl.close()
            process.terminate()
            while process.is_alive():
                time.sleep(0.2)
            #endwhile
            process = Process(target=readProcess)
            process.start()
        except :
            raise
        #endtry
        
        self.send_response(200)
        self.end_headers()
    #enddef




    def handleStatic(self,url,params):
        """
        """
        try:
            filename = url.path
            if filename == '/':
                filename = "/index.html"
            #endif
            fl = open(DOC_ROOT + filename, 'r')
            
            mime = mimeTypes.get(filename.split('.')[-1],"text/html")

            self.send_response(200)
            self.send_header("Content-type", mime)
            self.end_headers()
            self.wfile.write(fl.read())

        except:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write("<html><head><title>Title goes here.</title></head>")
            self.wfile.write("<body><p>%s Not found</p></body></html>" % filename)
            
        #endtry
    #enddef
#endclass

def readSensors():
    """
    """
    data = [[datetime.now().strftime("%Y-%m-%d %H:%M:%S"),],[datetime.now().strftime("%Y-%m-%d %H:%M:%S"),]]
    lock.acquire()
    #sensor MCP9808
    if SENSOR == 'MCP':
        temp = sensor.readTempC()    
    #sensor DHT22
    elif SENSOR == 'DHT':
        hum, temp = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, PIN1)
        data[0].append("H%0.1f" % hum)
    #endif
    data[0].append("T%0.1f" % temp)
    #sensor MCP9808
    if SENSOR == 'MCP':
        temp = sensor.readTempC()    
    #sensor DHT22
    elif SENSOR == 'DHT':
        hum, temp = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, PIN2)
        data[1].append("H%0.1f" % hum)
    #endif
    data[1].append("T%0.1f" % temp)
    lock.release()
    return data
  
    #enddef

def readProcess():
    """
    """
    #read interval
    sys.stdout.flush() 
    fl = open(INTERVAL,'rt')
    interval = int(fl.read())
    fl.close()
    while True:
        data = readSensors()
        i = 0
        for queue in queues:
            queue.put(data[i])
            i+=1
            #print data[i]
        time.sleep(interval)
    #endwhile
#enddef
   


def main():
    """
    """
    global process 
  
    global lock
    global queues
    queues = []
    for i in range(0,SENSORS):
        queues.append(Queue())
    #endfor

    lock = Lock()
    
    #sensor MCP9808
    if SENSOR == "MCP":
        global sensors
        sensors = []
        for i in range(0,SENSORS):
            sensors.append(MCP9808.MCP9808())
            #sensor = MCP9808.MCP9808()
            sensors[-1].begin()
    #endif
    #make process
    process = Process(target=readProcess)
    process.start()
    signal.signal(signal.SIGTERM, handler)
    

    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)

    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    #print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
    
    process.terminate()
#enddef

def handler(signum, frame):
    if signum in [15,9]:
        process.terminate()
        time.sleep(3)
        sys.exit(0)


if __name__ == '__main__':
        
    daemon = Daemonize(app="thermometer", pid=PID, action=main, keep_fds=[])
    daemon.start() 
    #main()
