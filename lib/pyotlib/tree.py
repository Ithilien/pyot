#
# PyoT Tree
#
# Michael Rosen
# mrrosen
# 12-10-2015
#

import importlib

import pyotlib.printlib as pr

class Tree(object):
  
  def __init__(self, params):
    # Create platform
    module = importlib.import_module("pyotlib.peripherals." + params['class']);
    newParams = dict(params);
    newParams['path'] = "/";
    newParams['parent'] = None;
    newParams['platform'] = self;
    self._head = module.create(newParams);
    
  # Function for running the phases
  def build(self):
    self._head._build();
    return;
  
  def connect(self):
    self._head._connect();
    return;
    
  def init(self):
    self._head._init();
    return;
    
  # Return the node described by path
  def find(self, path, obj=None):
    if ((obj != None) and (path[0] != "/")):
      pr.Dbg("Trying to find '%s' from '%s'" % (path, obj.fullname()));
      return self._head._find(obj.path() + path);
    elif (path[0] == "/"):
      pr.Dbg("Trying to find '%s' (absolute)" % path);
      return self._head._find(path);
    return None;
  
class Endpoints(object):

  def __init__(self, parent, path, platform, params):
    self._parent = parent;
    self._path = path;
    self._platform = platform;
    self._params = params;
    
    self._endpoints = dict();
    
  def add(self, name, t):
    if (name in self._endpoints):
      return None;
      
    if (name in self._params):
      params = self._params[name];
    else:
      params = {'build': {}, 'connect': {}, 'init': {}};
      
    self._endpoints[name] = t(self._parent, self._path, name, self._platform, params);
    
    return self._endpoints[name];
    
  def find(self, name):
    if (name in self._endpoints):
      pr.Dbg("Found: %s" % name);
      return self._endpoints[name];
     
    return None;
   
  def enumerate(self):
    pr.Msg("Endpoints for this peripheral are:");
    for ep in self._endpoints:
      # Generate path list
      cl = type(self._endpoints[ep]);
      t = cl.__name__;
      while (not(t in ["Sensor", "Port", "Actuator", "GroupSensor", "Comm", "Endpoint"])):
        cl = cl.__bases__[0];
        t = cl.__name__;
      pr.Msg("%s (%s)" % (self._endpoints[ep].name(), t));
      
    return;
    
  # Phases
  def build(self):
    for ep in self._endpoints:
      self._endpoints[ep].build(self._endpoints[ep]._params['build']);
    return;
    
  def connect(self):
    for ep in self._endpoints:
      self._endpoints[ep].connect(self._endpoints[ep]._params['connect']);
    return;
    
  def init(self):
    for ep in self._endpoints:
      self._endpoints[ep].init(self._endpoints[ep]._params['init']);
    return;
