#! /usr/bin/env python
# -*- coding: utf-8 -*-
###################################################################################
# Mac OS System plug-in
# By Bernard Philippe (bip.philippe) (C) 2015
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.#
#
#
# History
# Rev 1.0.2 : 	replace "open" command by "run" in osascript
#				add decode('utf-8') for output of error messages
# Rev 1.0.1 : 	correct the grep used for finding processes for more accurate match
# Rev 1.0.0 :   initial version
#
####################################################################################

import sys
import subprocess
import time

# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.

################################################################################
class Plugin(indigo.PluginBase):
    ########################################
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debug = False
        self.debugraw = False
        self.nextDiskPing = 0
        self.paceDiskPing = 0

    def __del__(self):
        indigo.PluginBase.__del__(self)

    ########################################
    # Private functions
    ########################################
    def _debugFlags(self,valueDict):
        # manage debug flag
        try:
            if valueDict[u'showDebugInfo'] == True:
                self.debug = True
            else:
                self.debug = False
            if valueDict[u'showShellLog'] == True:
                self.debugraw = True
            else:
                self.debugraw = False
        except:
            pass


    ########################################
    def startup(self):
        self.debugLog(u"startup called")
        # list of device : Volumes and applications
        self._debugFlags(self.pluginPrefs)
        self.volumeList = {}
        self.wakePace = 0
        self.applicationList = {}

        self.debugLog(u"end of startup")

    def shutdown(self):
        self.debugLog(u"shutdown called")
        # do some cleanup here
        self.debugLog(u"end of shutdown")


    ######################
    def deviceStartComm(self, dev):
        self.debugLog(u"deviceStartComm called for: %s (%d - %s)" % (dev.name, dev.id, dev.deviceTypeId))
        if dev.deviceTypeId == "bip.ms.volume":
            self.volumeList[dev.id] = {'ref':dev,'name':dev.name,'VolumeID':dev.pluginProps['VolumeID'],'ping':dev.pluginProps['keepAwaken'],'status':None}
            self.debugLog(u"device %s added as a volume" % (dev.name))
        else:
            if ((dev.pluginProps['ApplicationID'])[-4]=='.app'):
                self.applicationList[dev.id] = {'ref':dev,'name':dev.name,'ApplicationID':dev.pluginProps['ApplicationID'],'status':None}
            else:
                self.applicationList[dev.id] = {'ref':dev,'name':dev.name,'ApplicationID':dev.pluginProps['ApplicationID']+'.app','status':None}
            self.debugLog(u"application %s added" % (dev.name))

        self.debugLog(u"end of deviceStartComm")

    def deviceStopComm(self, dev):
        self.debugLog(u"deviceStopComm called: %s (%d - %s)" % (dev.name, dev.id, dev.deviceTypeId))
        if dev.deviceTypeId == "bip.ms.volume":
            del self.volumeList[dev.id]
            self.debugLog(u"device %s removed" % (dev.name))
        else:
            del self.applicationList[dev.id]
            self.debugLog(u"application %s added" % (dev.name))
        self.debugLog(u"end of deviceStopComm")

    ######################
    #def triggerStartProcessing(self, trigger):
    #    self.debugLog(u"triggerStartProcessing called for: %s (%d)" % (trigger.name, trigger.id))
    #
    #    self.debugLog(u"end of triggerStartProcessing")

    # def triggerStopProcessing(self, trigger):
    #    self.debugLog(u"triggerStopProcessing called for: %s (%d)" % (trigger.name, trigger.id))
    #
    #    self.debugLog(u"end of triggerStopProcessing")

    ########################################
    # Update thread
    ########################################
    def runConcurrentThread(self):
        self.debugLog(u"runConcurrentThread called")
        try:
            while True:
                # Applications
                if len(self.applicationList) > 0:
                    for theapplication in self.applicationList:
                        p = subprocess.Popen("ps -awx | grep '" + self.applicationList[theapplication]['ApplicationID'] + "/Contents/MacOS/" + self.applicationList[theapplication]['ApplicationID'][:-4]+ "$'", shell=True,stdout=subprocess.PIPE, close_fds=True)
                        p.wait()
                        pslist = p.stdout.readlines()
                        if self.debugraw == True:
                            self.debugLog(u"ps Log: %s" % pslist)
                        isOn = False
                        if len(pslist)>0:
                            isOn =True
                            if self.applicationList[theapplication]['status']!=True:
                                self.applicationList[theapplication]['ref'].updateStateOnServer(key="ProcessID", value=pslist[0][:6].strip())
                                self.applicationList[theapplication]['status']=True
                                self.debugLog(u"device %s information updated from ps" % (self.applicationList[theapplication]['ApplicationID']))

                        if self.applicationList[theapplication]['ref'].displayStateValRaw != isOn:
                            self.debugLog(u"device %s state is now %s" % (self.applicationList[theapplication]['ApplicationID'],isOn))
                            self.applicationList[theapplication]['ref'].updateStateOnServer(key="onOffState", value=isOn)

                # Volumes
                if len(self.volumeList) > 0:
                    # store the time stamp as a reference
                    thetime = time.time()

                    p = subprocess.Popen("/usr/sbin/diskutil list", shell=True,stdout=subprocess.PIPE, close_fds=True)
                    p.wait()
                    diskutil = p.stdout.read()
                    p = subprocess.Popen("ls /Volumes -1", shell=True,stdout=subprocess.PIPE, close_fds=True)
                    p.wait()
                    diskls = p.stdout.read()
                    if self.debugraw == True:
                        self.debugLog(u"diskutil Log: %s" % diskutil)
                        self.debugLog(u"ls /Volumes Log: %s" % diskls)
                    diskutil = diskutil.split("\n")
                    diskls = diskls.split("\n")

                    for thevolume in self.volumeList:
                        isThere = False
                        for disk in diskutil:
                            thename = disk[33:55].strip()
                            if (len(thename)>0) and (thename<>"NAME"):
                                if thename == self.volumeList[thevolume]['VolumeID']:
                                    isThere = True

                                    if self.volumeList[thevolume]['status']!=True:
                                        self.volumeList[thevolume]['ref'].updateStateOnServer(key="VolumeType", value=disk[6:33].strip())
                                        self.volumeList[thevolume]['ref'].updateStateOnServer(key="VolumeSize", value=disk[57:68].strip())
                                        self.volumeList[thevolume]['ref'].updateStateOnServer(key="VolumeDevice", value=disk[68:].strip())
                                        self.volumeList[thevolume]['ref'].updateStateOnServer(key="VolumeDeviceReady", value=True)
                                        self.volumeList[thevolume]['status']=True
                                        self.debugLog(u"device %s information updated from diskutil" % (self.volumeList[thevolume]['VolumeID']))


                                    isOn = False
                                    for vname in diskls:
                                        if thename == vname:
                                            isOn = True
                                            break

                                    # update state if needed
                                    if self.volumeList[thevolume]['ref'].displayStateValRaw != isOn:
                                        self.debugLog(u"device %s state is now %s" % (self.volumeList[thevolume]['VolumeID'],isOn))
                                        self.volumeList[thevolume]['ref'].updateStateOnServer(key="onOffState", value=isOn)

                                    # keep spinning if required
                                    if (thetime > self.nextDiskPing) and (self.paceDiskPing>0) and (self.volumeList[thevolume]['ping']==True):
                                        self.debugLog(u"going to ping device %s" % (self.volumeList[thevolume]['VolumeID']))
                                        thefile = "/Volumes/"+self.volumeList[thevolume]['VolumeID']+"/.spinner"
                                        p = subprocess.Popen("touch '"+thefile+"'", shell=True,stderr=subprocess.PIPE, close_fds=True)
                                        p.wait()
                                        perror = p.stderr.read()
                                        if len(perror)>0:
                                            self.errorLog(u"spinning %s failed because %s" % (dev.name, perror.decode('utf-8')))
                                        else:
                                            self.volumeList[thevolume]['ref'].updateStateOnServer(key="LastPing", value=time.time())


                                    # nothing more to do
                                    break

                        if (isThere == False) and (self.volumeList[thevolume]['status']!=False):
                            self.volumeList[thevolume]['ref'].updateStateOnServer(key="onOffState", value=False)
                            self.volumeList[thevolume]['ref'].updateStateOnServer(key="VolumeDeviceReady", value=False)
                            self.volumeList[thevolume]['status']=False
                            self.debugLog(u"device %s information updated as no more in diskutil" % (self.volumeList[thevolume]['VolumeID']))

                # update ping time if needed
                if thetime > self.nextDiskPing:
                    # test the disk pace
                    p = subprocess.Popen("pmset -g | grep disksleep | sed -e s/[a-z]//g  | sed -e 's/ //g'", shell=True,stdout=subprocess.PIPE, close_fds=True)
                    p.wait()
                    try:
                        self.paceDiskPing = int(p.stdout.read()) * 60
                    except:
                        self.paceDiskPing = 0

                    if self.paceDiskPing == 0:
                        self.nextDiskPing = thetime + 60
                    else:
                        self.nextDiskPing = thetime + self.paceDiskPing - 30

                    # calculate the next one
                    self.debugLog(u"next ping time %s (pace is %s)" % (self.nextDiskPing,self.paceDiskPing))


                # wait
                self.sleep(2) # in seconds
        except self.StopThread:
            # do any cleanup here
            pass
        self.debugLog(u"end of runConcurrentThread")

    ########################################
    # Relay / Dimmer Action callback
    ######################
    def actionControlDimmerRelay(self, action, dev):
        self.debugLog(u"actionControlDimmerRelay called for: %s (%d - %s)" % (dev.name, dev.id, dev.deviceTypeId))
        theaction = action.deviceAction
        if theaction == indigo.kDimmerRelayAction.Toggle:
            if dev.displayStateValRaw == False:
                theaction = indigo.kDimmerRelayAction.TurnOn
            else:
                theaction = indigo.kDimmerRelayAction.TurnOff

        ###### TURN ON ######
        if theaction == indigo.kDimmerRelayAction.TurnOn:
            if dev.displayStateValRaw == True:
                self.debugLog(u"device %s is already on" % (dev.name))
            else:
                if dev.deviceTypeId == "bip.ms.volume":
                    if (dev.states['VolumeDeviceReady']==True):
                        self.debugLog(u"mouting volume %s device %s" % (dev.name,dev.states['VolumeDevice']))
                        p = subprocess.Popen("/usr/sbin/diskutil mount " + dev.states['VolumeDevice'], shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, close_fds=True)
                        p.wait()
                        perror = p.stderr.read()
                        if len(perror) > 0:
                            self.errorLog(u"mounting %s failed because %s" % (dev.name, perror.decode('utf-8')))
                        # state will be update by the updating thread
                    else:
                        self.errorLog(u"send %s %s failed because device not available" % (dev.name, "on"))
                else:
                    self.debugLog(u"launch of application %s with id %s" % (dev.name,self.applicationList[dev.id]['ApplicationID']))
                    osa = subprocess.Popen(['osascript', '-e', 'tell application "' + self.applicationList[dev.id]['ApplicationID'] + '" to run'],stderr=subprocess.PIPE,close_fds=True)
                    osa.wait()
                    perror = osa.stderr.read()
                    if len(perror) > 0:
                        self.errorLog(u"launching %s failed because %s" % (dev.name, perror.decode('utf-8')))

        ###### TURN OFF ######
        elif theaction == indigo.kDimmerRelayAction.TurnOff:
            if dev.displayStateValRaw == False:
                self.debugLog(u"device %s is already off" % (dev.name))
            else:
                if dev.deviceTypeId == "bip.ms.volume":
                    if dev.pluginProps['forceQuit']==True:
                        flag="force "
                    else:
                        flag=""
                    self.debugLog(u"unmouting " + flag + "volume %s device %s" % (dev.name,dev.states['VolumeDevice']))
                    p = subprocess.Popen("/usr/sbin/diskutil umount " + flag + dev.states['VolumeDevice'], shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE, close_fds=True)
                    p.wait()
                    perror = p.stderr.read()
                    if len(perror) > 0:
                        self.errorLog(u"umounting %s failed because %s" % (dev.name, perror.decode('utf-8')))
                    # state will be update by the updating thread
                else:
                    if dev.pluginProps['forceQuit']==False:
                        self.debugLog(u"quit of application %s with id %s" % (dev.name,self.applicationList[dev.id]['ApplicationID']))
                        p = subprocess.Popen(['osascript','-e','tell application "' + self.applicationList[dev.id]['ApplicationID'] + '" to quit'],stderr=subprocess.PIPE,close_fds=True)
                        p.wait()
                        perror = p.stderr.read()
                        if len(perror) > 0:
                            self.errorLog(u"quit %s failed because %s" % (dev.name, perror.decode('utf-8')))
                    else:
                        self.debugLog(u"forced quit of application %s with id %s" % (dev.name,self.applicationList[dev.id]['ApplicationID']))
                        p = subprocess.Popen(['osascript','-e','do shell script "killall ' + self.applicationList[dev.id]['ApplicationID'][:-4] +'"'],stderr=subprocess.PIPE,close_fds=True)
                        p.wait()
                        perror = p.stderr.read()
                        if len(perror) > 0:
                            self.errorLog(u"forced quit %s failed because %s" % (dev.name, perror.decode('utf-8')))


        self.debugLog(u"end of actionControlDimmerRelay")


    ########################################
    # Prefs UI methods (works with PluginConfig.xml):
    ######################

    # Validate the pluginConfig window after user hits OK
    # Returns False on failure, True on success
    #
    def validatePrefsConfigUi(self, valuesDict):
        self.debugLog(u"validating Prefs called")

        errorMsgDict = indigo.Dict()
        err = False

        # manage debug flag
        self._debugFlags(valuesDict)

        self.debugLog(u"end of validating Prefs")
        return (True, valuesDict)


    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        self.debugLog((u"validating Device Config called for:    (%d - %s)") % ( devId, typeId))

        self.debugLog(u"end of validating Device Config")
        return (True, valuesDict)
