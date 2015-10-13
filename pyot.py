#
# PyoT Node (Main)
#
# Michael Rosen
# mrrosen
# 09-10-2015
#

import sys
import json
import time
import Queue
import getopt
import threading

from pyotlib import *
from pyotlib.printlib import *
from pyotlib.classes import *

def prHelp():
  print(" pyot.py\n"
        "\n"
        "   Script for running PyoT nodes with a provided configuration file\n"
        "\n"
        "   Arguments:\n"
        "\n"
        "     -h, --help               Displays this text.\n"
        "     -c, --config [file]      Needed to provide the script with a configuration file that\n"
        "                              describes the setup of the node's hardware and sensors as\n"
        "                              well as the communication channels to use. This file also\n"
        "                              configures which sensors are sent to the IoT backend (and\n"
        "                              which backends to use).\n"
        "                              Note that this should be a JSON file\n"
        "     -d, --debug              Print debug messages\n");
  return;
  
# If the platform has a chronometer, it should be defined in the configuration, otherwise, system
# time will be used
def setupTimer(config):
  global platform;
  if (config['timer'] != "default"):
    timer = platform.find(config['timer']);
    if (chrometer == None):
      prWrn("Chronometer '%s' could not be found, using system time instead");
    else:
      return timer.read;
  
  return getSystemTime;
    
def getSystemTime():
  return (time.time() * 1000);

# Producer Thread, reads data from all sensors that are given in the configuration
def proTask(config, channel, timer):
  global platform;
  
  prDbg("Producer thread started!");
  
  # Get all the objects for the sensors in the config
  sensors = [];
  for sen in config['sensors']:
    sensor = platform.find(sen['path']);
    if (sensor == None):
      prWrn("Sensor '%s'('%s') was not found" % (sen['name'], sen['path']));
    else:
      sensors.append({'name': sen['name'], 'sensor': sensor});
      
  if (len(sensors) == 0):
    prErr("No sensor paths in configuration are valid!");
  sleepTime = config['sensorSampleRate'];
  
  prDbg("Starting main loop of producer thread");
  
  while (True):
    time.sleep(sleepTime);
    
    channel.lock();
    
    for s in sensors:
      prDbg("Reading from sensor '%s'" % s['sensor'].fullname());
      val = s['sensor'].read();
      ts = timer();
      
      if (val == None):
        prDbg("Failed to read from sensor");
      else:
        prDbg("Got value: %s" % str(val));
        channel.put({'name': config['name'], 'ts': ts, 'val': val, 'sent': [False] * len(config['iot'])});
    
    channel.unlock();
    
    prMsg("All sensors read, sleeping for %d seconds..." % sleepTime);

# Consumer Thread, reads data generated by the producer thread and sends it to the iot backends that
# are given in the configuration
def conTask(config, channel):
  global platform;
  
  prDbg("Consumer thread started!");
  
  # Get all the objects for the backends in the config
  iotBackends = [];
  idx = 0;
  for i in config['iot']:
    iot = platform.find(i['path']);
    if (iot == None):
      prWrn("Backend '%s'('%s') was not found" % (i['name'], i['path']));
    else:
      iotBackends.append({'comm': iot, 'idx': idx});
      idx += 1;
      
  if (len(iotBackends) == 0):
    prErr("No backend paths in configuration are valid!");
  sleepTime = config['iotSendRate'];
  
  prDbg("Starting main loop of consumer thread");
  
  while (True):
    time.sleep(sleepTime);
    
    channel.lock();
    
    if (channel.empty()):
      prDbg("No items to send!");
    
    for i in xrange(channel.size()):
      # Pull off an item to send
      item = channel.get();
      
      prDbg("Sending reading: %s" + str(item));
      
      for comm in iotBackends:
        prDbg("Sending to backend '%s'" % comm['comm'].fullname());
          
        if (item['sent'][comm['idx']]):
          prDbg("Already sent this value on this comm successfully!");
        else:
          sent = comm['comm'].send(item);
        
          if (sent):
            prDbg("Data sent!");
            item['sent'][comm['idx']] = True;
          else:
            prDbg("Failed to send!");
      
      if (not(reduce(lambda x, y: x & y, item['sent']))):
        prDbg("Item still needs to send on some comms, putting back in list...");
        channel.put(item);
      else:
        prDbg("Item sent on all comms, leaving out of list!");
            
    channel.unlock();
    
    prMsg("Data sending complete, sleeping for %d seconds..." % sleepTime);
    
# Main function
def main(argv):
  global platform;
  
  # Parse arguments
  try:
    (options, args) = getopt.getopt(argv, 'hdc:', ['config=', 'help', 'debug']);
  except:
    prErr("Bad commandline options");
    print('');
    prHelp();
    sys.exit(-1);

  configFile = '';

  if (not(options[0])):
    prErr("Bad commandline options");
    print('');
    prHelp();
    sys.exit(-1);
  
  for (o, a) in options:
    if (o in ("-h", "--help")):
      prHelp();
      sys.exit(0);
    elif (o in ("-c", "--config")):
      configFile = a;
    elif (o in ("-d", "--debug")):
      debug[0] = True;
      
  if (configFile == ''):
    prErr("Need a configuration file!");
    sys.exit(-1);
    
  # Load configuration
  with open(configFile) as configFileHandle:
    config = json.load(configFileHandle);
  
  if (not("platform" in config)):
    prErr("Need a platform in configuration!");
    sys.exit(-1);  
  if (not("sensors" in config)):
    prErr("No sensors are given in the configuration, so no data will be collected!");
  if (not("iot" in config)):
    prErr("No backend comms are given in the configuration, so no data will be sent!");
  
  # Create the hierarchy
  try:
    prDbg("Generating tree...");
    platform = tree.Tree(config['platform']);
    prDbg("Generation complete!");
  except:
    prErr("Failed to create the platform and its peripherals!");
    sys.exit(-1);
  
  # Run through the phases of generating the system
  try:
    prDbg("Build phase...");
    platform.build();
    prDbg("Build phase complete!");
  except:
    prErr("Build phase failed");
    sys.exit(-1);
  
  try:
    prDbg("Connect phase...");
    platform.connect();
    prDbg("Connect phase complete!");
  except:
    prErr("Connect phase failed");
    sys.exit(-1);
    
  try:
    prDbg("Init phase...");
    platform.init();
    prDbg("Init phase complete!");
  except:
    prErr("Init phase failed");
    sys.exit(-1);
    
  prMsg("Platform prep complete!");
  
  # Build a channel between the producer and consumer
  channel = channel.Channel();
  prDbg("Channel built!");
  
  # Get the timer, using either system time or a specific chronometer
  timer = setupTimer(config);
  
  # Create producer and consumer threads
  proThread = threading.Thread(target=proTask, args=(config, channel, timer));
  conThread = threading.Thread(target=conTask, args=(config, channel));
  
  prMsg("Starting threads...");
  
  while (True):
    if (not(proThread.isAlive())):
      prDbg("Producer thread is dead, reviving...");
      proThread.start();
    if (not(conThread.isAlive())):
      prDbg("Consumer thread is dead, reviving...");
      conThread.start();
    time.sleep(config['threadRestartRate']);
    
if (__name__ == "__main__"):
  if (len(sys.argv) == 1):
    prHelp();
    sys.exit(-1);
  main(sys.argv[1:]);