#
# PyoT Base Classes
#
# Michael Rosen
# mrrosen
# 09-10-2015
#

import importlib
from abc import *
from pyotlib.tree import Endpoints

# Base class for peripheral objects, includes a bunch of stuff for dealing with the tree structure
class Peripheral(object):
  
  def __init__(self, params):
    self._path = params['path'];
    self._parent = params['parent'];
    self._name = params['name'];
    
    # Parse params
    if ("." in params['params']):
      self._params = params['params']['.'];
    else:
      self._params = {'build': {}, 'connect': {}, 'init': {}};
    
    # Create endpoints
    self.endpoints = Endpoints(self, self.fullname(), params['params']);
    
    # Create all peripherals    
    self._peripherals = []
    for p in params['peripherals']:
      module = importlib.import_module("pyotlib.peripherals." + p['class']);
      newParams = dict(p);
      newParams['path'] = self.fullname();
      newParams['parent'] = self;
      self._peripherals.append(module.create(newParams));
  
  # Recursive find method  
  def _find(self, path):
    # Take off the leading /
    p = path[1:];
    
    # If there is no longer a / in the path, we are the end (maybe)
    if (not("/" in p)):
      parts = p.split(":");
      if ((parts[0] == self._name) or (parts[0] == ".")):
        if (len(parts) == 1):
          return self;
        else:
          return self.endpoints.find(parts[1]);
    else:
      # We are not the endpoint, strip off ourself (also checking if we were the proper place to go)
      parts = p.split("/");
      if ((parts[0] == self._name) or (parts[0] == ".") or (parts[0] == "..") or (parts[0] == "")):
        newPath = p[len(parts[0]):];
        if ((parts[1] == self._name) or (parts[1] == ".") or (parts[1] == "")):
          return self._find(newPath);
        elif (parts[1] == ".."):
          return self._parent._find(newPath);
        else:
          for peripheral in self._peripherals:
            if (parts[1] == peripheral._name):
              return peripheral._find(newPath);
    
    return None;
    
  def name(self):
    return self._name;
   
  def path(self):
    return self._path;
    
  def fullname(self):
    return (self._path + "/" + self._name); 
     
  #Phases
  
  def build(self, params):
    return;
    
  def _build(self):
    self.build(self._params['build']);
    self.endpoints.build();
    
    for p in self._peripherals:
      p._build();
      
    return;
    
  def connect(self, params):
    return;
    
  def _connect(self):
    self.build(self._params['connect']);
    self.endpoints.connect();
    
    for p in self._peripherals:
      p._connect();
      
    return;
    
  def init(self, params):
    return;
    
  def _init(self):
    self.build(self._params['init']);
    self.endpoints.init();
    
    for p in self._peripherals:
      p._init();
      
    return;

# Endpoint base class
class Endpoint(object):
  
  def __init__(self, parent, path, name, params):
    self._parent = parent;
    self._path = path;
    self._name = name;
    self._params = params;
    
  def name(self):
    return self._name;
    
  def path(self):
    return self._path;
    
  def fullname(self):
    return (self._path + ":" + self._name);
    
  def __find(self, path):
    return self._parent._find(path);

  def build(self, params):
    return;
    
  def connect(self, params):
    return;
    
  def init(self, params):
    return;
    
  def request(self, params):
    return True;
  
# Base class for sensor objects
class Sensor(Endpoint):
  __metaclass__ = ABCMeta;
    
  @abstractmethod
  def read(self):
    pass;
   
# Base class for actuator objects
class Actuator(Endpoint):
  __metaclass__ = ABCMeta;

  @abstractmethod
  def write(self, val):
    pass;
    
# Base class for comm objects
class Comm(Endpoint):
  __metaclass__ = ABCMeta;
    
  @abstractmethod
  def send(self, vals):
    pass;
  
  @abstractmethod
  def poll(self):
    pass;
    
# Base class for port objects
class Port(Endpoint):
  pass;
