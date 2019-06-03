#!/usr/bin/python -u
# -*- coding: utf-8 -*-

import dbus
import os
import sys
from time import time, sleep
from dbus.mainloop.glib import DBusGMainLoop
import urllib2, httplib
import ConfigParser
import pprint

# Victron packages
AppDir = os.path.dirname(os.path.realpath(__file__))               
sys.path.insert(1, os.path.join(AppDir, 'ext', 'velib_python'))
from vedbus import VeDbusItemImport

SoftwareVersion = "1.02"
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

while (dbusConn):

    EmoncmsInputs = {}
    for bus_key in DbusObjectPath.keys():

        bus_key_config = dict(config.items(bus_key))
        for key, value in bus_key_config.items():
            try:
                result = VeDbusItemImport(dbusConn, DbusObjectPath[bus_key], value)
                EmoncmsInputs[key] = 0 if result is None else result.get_value()
            except Exception, ex:
                print "Exception: %s" % ex
                EmoncmsInputs[key] = 0

    # Prepare data for POST
    data = "apikey=%s&node=%s&time=%s&data={%s}" % (
        Emoncms['apikey'], Emoncms['node'], time(),
        ','.join(['%s:%s' % kv for kv in EmoncmsInputs.items()]) )

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
        if "ok" in result:
            print "Send ok"
        else:
            print "Send failure"


    sleep(interval)

# Fin.

