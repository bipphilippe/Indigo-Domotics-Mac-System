#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
"""
    Mac OS Sytem plug-in
    By Bernard Philippe (bip.philippe) (C) 2015

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.#


    History
    =======
    Rev 1.0.0 : Initial version
    Rev 1.0.1 : Correct the grep used for finding processes for more accurate match
    Rev 1.0.2 : Packaging for initial release - 20 march 2015
                 - replace "open" command by "run" in osascript
                 - add decode('utf-8') for output of error messages
    Rev 1.0.3 : Correction of two bugs - 22 march 2015
                 - decrease CPU overhead by incrementing pace time
                 - correct thetime variable non-assigned but used when no volume is declared (thanks to kw123)
    Rev 1.1.0 : Enhanced version with more states - 20 april 2015
                Manages new states for devices :
                 - enhanced use of ps command to collect more information
                 - use of df command to collect % used
                Introduces special state icons to reflect some special states :
                 - volume connected but not mounted
                 - application frozen or waiting
                Optimization :
                 - updates detailed volume an application data in a slower pace than the onOff state
                Some bugs corrections, including :
                 - library error when launching some application
                 - keep alive timing too close to sleep to prevent some kind of disks to sleep
                First version based on the Bip Framework
    Rev 1.1.1 : Bug correction - 22 april 2015
                Corrects the following bugs:
                 - update requests are now processed
                 - ps dump process is now more permissive on data positions
                 - avoid sending Turn On when device already On
                 - avoid sending Turn Off when device already Off
    Rev 1.2.0 : Enhancements - 25 april 2005
                 - add a "about" menu
                 - new log management, less verbose
                 - manages the "Enable Indigo Communication" flag
               Some bugs corrections, including:
                 - library error when closing some application
"""
####################################################################################

import sys
from bipIndigoFramework import core
from bipIndigoFramework import corethread
from bipIndigoFramework import shellscript
from bipIndigoFramework import osascript
from bipIndigoFramework import relaydimmer
import interface
import re


# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.


_repCloseAppError = re.compile(r"(Error loading .Library)")


################################################################################
class Plugin(indigo.PluginBase):
    ########################################
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debug = False
        self.logLevel = 1

    def __del__(self):
        indigo.PluginBase.__del__(self)

    ########################################
    # Indigo plugin functions
    #
    #
    ########################################
    def startup(self):
        # first read debug flags - before any logging
        core.debugFlags(self.pluginPrefs)
        # startup call
        core.logger(traceLog = u"startup called")
        interface.init()
        corethread.init()
        core.logger(traceLog = u"end of startup")

    def shutdown(self):
        core.logger(traceLog = u"shutdown called")
        # do some cleanup here
        core.logger(traceLog = u"end of shutdown")


    ######################
    def deviceStartComm(self, dev):
        core.logger(traceLog = u"deviceStartComm called for: %s (%d - %s)" % (dev.name, dev.id, dev.deviceTypeId))
        core.logger(traceLog = u"end of deviceStartComm")

    def deviceStopComm(self, dev):
        core.logger(traceLog = u"deviceStopComm called: %s (%d - %s)" % (dev.name, dev.id, dev.deviceTypeId))
        core.logger(traceLog = u"end of deviceStopComm")

    ######################
    #def triggerStartProcessing(self, trigger):
    #    core.logger(traceLog = u"triggerStartProcessing called for: %s (%d)" % (trigger.name, trigger.id))
    #
    #    core.logger(traceLog = u"end of triggerStartProcessing")

    # def triggerStopProcessing(self, trigger):
    #    core.logger(traceLog = u"triggerStopProcessing called for: %s (%d)" % (trigger.name, trigger.id))
    #
    #    core.logger(traceLog = u"end of triggerStopProcessing")


    ########################################
    # Update thread
    ########################################
    def runConcurrentThread(self):
        core.logger(traceLog = u"runConcurrentThread initiated")

        # init spinner timer
        psvalue= int(self.pluginPrefs['disksleepTime'])
        if psvalue>0:
            psvalue = (psvalue-1)*60
        else:
            psvalue=600
        nextDiskSpin = corethread.dialogTimer("Next disk spin",psvalue)
        
        # init full data read timer for volumes
        readVolumeData = corethread.dialogTimer("Read volume data",60)

        # init full data read timer for applications
        readApplicationData = corethread.dialogTimer("Read application data",60,30)

        # loop
        try:
            while True:
                corethread.sleepWake()
  
                # Test if time to spin
                timeToSpin = nextDiskSpin.isTime()
                if timeToSpin:
                    # get disk sleep value
                    psvalue = shellscript.run(u"pmset -g | grep disksleep | sed -e s/[a-z]//g  | sed -e 's/ //g'")
                    try:
                        psvalue = int(psvalue)
                    except:
                        psvalue=0
                    # set property and timer if needed
                    theupdatesDict = core.updatepluginprops({'disksleepTime':psvalue})
                    if (len(theupdatesDict)>0):
                        if psvalue>0:
                            nextDiskSpin.changeInterval((psvalue-1)*60)
                        else:
                            nextDiskSpin.changeInterval(600)
        
                # test if time to read full data
                timeToReadVolumeData = readVolumeData.isTime()
                timeToReadApplicationData = readApplicationData.isTime()
                
                for thedevice in indigo.devices.iter("self"):
                    thevaluesDict = {}

                    ##########
                    # Application device
                    ########################
                    if (thedevice.deviceTypeId =="bip.ms.application") and thedevice.configured:
                        # states
                        (success,thevaluesDict) = interface.getProcessStatus(thedevice, thevaluesDict)
                        # update
                        theupdatesDict = core.updatestates(thedevice, thevaluesDict)
                        # special images
                        core.specialimage(thedevice, "PStatus", theupdatesDict, {"idle":indigo.kStateImageSel.AvPaused,"waiting":indigo.kStateImageSel.AvPaused,"stopped":indigo.kStateImageSel.AvStopped,"zombie":indigo.kStateImageSel.SensorTripped})
                        
                        # do we need to read full data ?
                        if ('onOffState' in theupdatesDict):
                            corethread.setUpdateRequest(thedevice)

                        if timeToReadApplicationData or corethread.isUpdateRequested(thedevice):
                            (success,thevaluesDict) = interface.getProcessData(thedevice, thevaluesDict)
                            core.updatestates(thedevice, thevaluesDict)

                    ##########
                    # Volume device
                    ########################
                    elif (thedevice.deviceTypeId =="bip.ms.volume") and thedevice.configured:
                         # states
                        (success,thevaluesDict) = interface.getVolumeStatus(thedevice, thevaluesDict)
                        # spin if needed
                        if timeToSpin:
                            (success,thevaluesDict) = interface.spinVolume(thedevice, thevaluesDict)
                        # update
                        theupdatesDict = core.updatestates(thedevice, thevaluesDict)
                        # special images
                        core.specialimage(thedevice, "VStatus", theupdatesDict, {"notmounted":indigo.kStateImageSel.AvStopped})

                        # do we need to read full data ?
                        if ('onOffState' in theupdatesDict):
                            corethread.setUpdateRequest(thedevice,3)
                        
                        if timeToReadVolumeData or corethread.isUpdateRequested(thedevice):
                            (success,thevaluesDict) = interface.getVolumeData(thedevice, thevaluesDict)
                            core.updatestates(thedevice, thevaluesDict)
        
                # wait
                corethread.sleepNext(10) # in seconds
        except self.StopThread:
            # do any cleanup here
            core.logger(traceLog = u"end of runConcurrentThread")

    ########################################
    # Relay / Dimmer Action callback
    ######################
    def actionControlDimmerRelay(self, action, dev):
        # some generic controls and logs
        theactionid = relaydimmer.startAction(dev, action)

        if theactionid is None:
            # no action to do
            return
        
        if theactionid == indigo.kDeviceGeneralAction.RequestStatus:
            corethread.setUpdateRequest(dev)
            return

        ##########
        # Application device
        ########################
        if (dev.deviceTypeId =="bip.ms.application"):
            if (theactionid == indigo.kDimmerRelayAction.TurnOn):
                shellscript.run(u"open '%s'" % (dev.pluginProps['ApplicationPathName']))
                # status update will be done by runConcurrentThread

            elif (theactionid == indigo.kDimmerRelayAction.TurnOff):
                if dev.pluginProps['forceQuit']:
                    shellscript.run(u"kill %s" % (dev.states['ProcessID']))
                    # status update will be done by runConcurrentThread
                else:
                    osascript.run(u'''(* Tell to quit *)
                        tell application "%s" to quit''' % (dev.pluginProps['ApplicationID']), )
                    # status update will be done by runConcurrentThread

        ##########
        # Volume device
        ########################
        elif (dev.deviceTypeId =="bip.ms.volume"):
            if (theactionid == indigo.kDimmerRelayAction.TurnOn) and (dev.states['VStatus']=="notmounted"):
                shellscript.run(u"/usr/sbin/diskutil mount %s" % (dev.states['VolumeDevice']))
            # status update will be done by runConcurrentThread
            
            elif (theactionid == indigo.kDimmerRelayAction.TurnOff):
                if dev.pluginProps['forceQuit']:
                    shellscript.run(u"/usr/sbin/diskutil umount force %s" % (dev.states['VolumeDevice']))
                    # status update will be done by runConcurrentThread
                else:
                    shellscript.run(u"/usr/sbin/diskutil umount %s" % (dev.states['VolumeDevice']))
                    # status update will be done by runConcurrentThread


    ########################################
    # Prefs UI methods (works with PluginConfig.xml):
    ######################

    # Validate the pluginConfig window after user hits OK
    # Returns False on failure, True on success
    #
    def validatePrefsConfigUi(self, valuesDict):
        core.logger(traceLog = u"validating Prefs called")

        errorMsgDict = indigo.Dict()
        err = False

        # manage debug flag
        core.debugFlags(valuesDict)

        core.logger(traceLog = u"end of validating Prefs")
        return (True, valuesDict)


    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        core.logger(traceLog = (u"validating Device Config called for:    (%d - %s)") % ( devId, typeId))

        if typeId == "bip.ms.application":
            if not valuesDict['nameSpecial']:
                valuesDict['ApplicationPathName'] = '/Applications/' +valuesDict['ApplicationID']+'.app'

        core.logger(traceLog = u"end of validating Device Config")
        return (True, valuesDict)

