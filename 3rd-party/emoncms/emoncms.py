#!/usr/bin/python -u
# -*- coding: utf-8 -*-

from dbus.mainloop.glib import DBusGMainLoop
import dbus
import gobject
import sys
import os
from time import time, sleep
import urllib2, httplib
import ConfigParser
import pprint

# Victron packages
AppDir = os.path.dirname(os.path.realpath(__file__))               
sys.path.insert(1, os.path.join(AppDir, 'ext', 'velib_python'))
from vedbus import VeDbusItemImport

SoftwareVersion = "1.12"
ConfigFile = "%s/emoncms.conf" % AppDir
UserAgent = "CCGX-Emoncms/%s" % SoftwareVersion

print("-------- emoncms, v{} is starting up --------".format(SoftwareVersion))                          

# Read config, do not lowercase keys (optionxform).
config = ConfigParser.RawConfigParser()
config.optionxform = str
config.read(ConfigFile)
Emoncms = dict(config.items('EMONCMS'))
DbusObjectPath = dict(config.items('DBUS'))

EmoncmsURL = "%s/emoncms/input/post" % Emoncms['server']
interval = float(Emoncms['interval'])

DBusGMainLoop(set_as_default=True)
dbusConn = dbus.SystemBus()

# Create the dictionary will all the VeDbusItemImport objects.
print "Building objects dictionary"
EmoncmsObjects = {}
for bus_key in DbusObjectPath.keys():

    bus_key_config = dict(config.items(bus_key))
    for key, value in bus_key_config.items():
        EmoncmsObjects[key] = VeDbusItemImport(dbusConn, DbusObjectPath[bus_key], value)

print "Done. Object size = %d bytes." % sys.getsizeof(EmoncmsObjects)

# Loop
print "Loop start"
while (dbusConn):

    EmoncmsValues = {}
    for key, o in EmoncmsObjects.items():
            EmoncmsValues[key] = o.get_value()

    # Prepare data for POST
    data = "apikey=%s&node=%s&time=%s&data={%s}" % (
        Emoncms['apikey'], Emoncms['node'], time(),
        ','.join(['%s:%s' % kv for kv in EmoncmsValues.items()]) )

    try:
        req = urllib2.Request(EmoncmsURL, headers={ 'User-Agent': UserAgent })
        result = urllib2.urlopen(req, data=data, timeout=8).read()
    except urllib2.HTTPError as e:
        print "Couldn't send to server, HTTPError: " +  str(e.code)
    except urllib2.URLError as e:
        print "Couldn't send to server, URLError: " +  str(e.reason)
    except httplib.HTTPException:
        print "Couldn't send to server, HTTPException"
    except Exception:
        import traceback
        print "Couldn't send to server, Exception: " +  traceback.format_exc()
    else:
        print "Send %d bytes, %s" % (len(data), result)


    sleep(interval)

# Fin.

