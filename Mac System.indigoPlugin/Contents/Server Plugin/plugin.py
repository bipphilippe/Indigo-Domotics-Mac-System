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
                Introduces special state icons to reflect some special states:
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
    Rev 1.2.1 : Library error correction - 26 april 2005
                Some bugs corrections, including:
                 - library error when closing some application
    Rev 1.2.2 : Volume device with special characters - 29 april 2005
                Some bugs corrections, including:
                 - Error on volume with special characters as '
    Rev 2.0.0 : Complex application and deamon version - 27 mai 2015
                Enhancements:
                 - new devices: Helpers and Daemons
                 - new action: close application windows
                 - new turn-on property: auto-close application windows
                 - auto-add of missing device parameters and states when upgrading
                 - better respect of properties and states data types
                Some bugs corrections, including:
                 - Applescript library error filter
                 - error message after install

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
import pipes


# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.

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
        core.logger(traceLog = u'startup called')
        interface.init()
        corethread.init()
        core.dumppluginproperties()

        core.logger(traceLog = u'end of startup')

    def shutdown(self):
        core.logger(traceLog = u'shutdown called')
        core.dumppluginproperties()
        # do some cleanup here
        core.logger(traceLog = u'end of shutdown')


    ######################
    def deviceStartComm(self, dev):
        core.logger(traceLog = u'"%s" deviceStartComm called (%d - %s)' % (dev.name, dev.id, dev.deviceTypeId))
        core.dumpdeviceproperties(dev)
        core.dumpdevicestates(dev)
                
        # upgrade version if needed
        if dev.deviceTypeId == u'bip.ms.application':
            core.upgradeDeviceProperties(dev,
                        {u'closeWindows':False,
                        u'processSpecial':False,
                        u'ApplicationProcessName':dev.pluginProps[u'ApplicationID'],
                        u'windowcloseSpecial':False,
                        u'directoryPath':(dev.pluginProps[u'ApplicationPathName'])[:-5-len(dev.pluginProps[u'ApplicationID'])],
                        u'windowcloseScript':u'Tell application "' + dev.pluginProps[u'ApplicationID'] + u'" to close every window',
                        u'ApplicationStopPathName':u'tell application "'+ dev.pluginProps[u'ApplicationID'] + u'" to quit',
                        u'ApplicationStartPathName':u'open ' + pipes.quote(dev.pluginProps[u'ApplicationPathName'])})

        core.logger(traceLog = (u'end of "%s" deviceStartComm'  % (dev.name)))

    def deviceStopComm(self, dev):
        core.logger(traceLog = u'deviceStopComm called: %s (%d - %s)' % (dev.name, dev.id, dev.deviceTypeId))
        core.dumpdeviceproperties(dev)
        core.dumpdevicestates(dev)
        core.logger(traceLog = u'end of "%s" deviceStopComm'  % (dev.name))


    ########################################
    # Update thread
    ########################################
    def runConcurrentThread(self):
        core.logger(traceLog = u'runConcurrentThread initiated')

        # init spinner timer
        try:
            psvalue= int(self.pluginPrefs[u'disksleepTime'])
        except:
            psvalue=0
        
        if psvalue>0:
            psvalue = (psvalue-1)*60
        else:
            psvalue=600
        nextDiskSpin = corethread.dialogTimer(u'Next disk spin',psvalue)

        # init full data read timer for volumes
        readVolumeData = corethread.dialogTimer(u'Read volume data',60)

        # init full data read timer for applications
        readApplicationData = corethread.dialogTimer(u'Read application data',60,30)

        # loop
        try:
            while True:
                corethread.sleepWake()

                # Test if time to spin
                timeToSpin = nextDiskSpin.isTime()
                if timeToSpin:
                    # get disk sleep value
                    psvalue = shellscript.run(u"pmset -g | grep disksleep | sed -e s/[a-z]//g | sed -e 's/ //g'")
                    try:
                        psvalue = int(psvalue)
                    except:
                        psvalue=0
                    # set property and timer if needed
                    theupdatesDict = core.updatepluginprops({u'disksleepTime':psvalue})
                    if (len(theupdatesDict)>0):
                        if psvalue>0:
                            nextDiskSpin.changeInterval((psvalue-1)*60)
                        else:
                            nextDiskSpin.changeInterval(600)

                # test if time to read full data
                timeToReadVolumeData = readVolumeData.isTime()
                timeToReadApplicationData = readApplicationData.isTime()

                for thedevice in indigo.devices.iter(u'self'):
                    thevaluesDict = {}

                    ##########
                    # Application device
                    ########################
                    if (thedevice.deviceTypeId in (u'bip.ms.application',u'bip.ms.helper',u'bip.ms.daemon')) and thedevice.configured and thedevice.enabled:
                        # states
                        (success,thevaluesDict) = interface.getProcessStatus(thedevice, thevaluesDict)
                        # update
                        theupdatesDict = core.updatestates(thedevice, thevaluesDict)
                        # special images
                        core.specialimage(thedevice, u'PStatus', theupdatesDict, {u'idle':indigo.kStateImageSel.AvPaused,u'waiting':indigo.kStateImageSel.AvPaused,u'stopped':indigo.kStateImageSel.AvStopped,u'zombie':indigo.kStateImageSel.SensorTripped})

                        # do we need to read full data ?
                        if (u'onOffState' in theupdatesDict):
                            # update to get more correct data
                            corethread.setUpdateRequest(thedevice)
                            # close windows if required
                            if (thedevice.pluginProps[u'closeWindows']==True) and (theupdatesDict[u'onOffState']==True):
                                self.closeWindowAction(thedevice)

                        if timeToReadApplicationData or corethread.isUpdateRequested(thedevice):
                            (success,thevaluesDict) = interface.getProcessData(thedevice, thevaluesDict)
                            core.updatestates(thedevice, thevaluesDict)

                    ##########
                    # Volume device
                    ########################
                    elif (thedevice.deviceTypeId ==u'bip.ms.volume') and thedevice.configured and thedevice.enabled:
                         # states
                        (success,thevaluesDict) = interface.getVolumeStatus(thedevice, thevaluesDict)
                        # spin if needed
                        if timeToSpin:
                            (success,thevaluesDict) = interface.spinVolume(thedevice, thevaluesDict)
                        # update
                        theupdatesDict = core.updatestates(thedevice, thevaluesDict)
                        # special images
                        core.specialimage(thedevice, u'VStatus', theupdatesDict, {u'notmounted':indigo.kStateImageSel.AvStopped})

                        # do we need to read full data ?
                        if (u'onOffState' in theupdatesDict):
                            corethread.setUpdateRequest(thedevice,3)

                        if timeToReadVolumeData or corethread.isUpdateRequested(thedevice):
                            (success,thevaluesDict) = interface.getVolumeData(thedevice, thevaluesDict)
                            core.updatestates(thedevice, thevaluesDict)

                # wait
                corethread.sleepNext(10) # in seconds
        except self.StopThread:
            # do any cleanup here
            core.logger(traceLog = u'end of runConcurrentThread')

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
        if (dev.deviceTypeId in (u'bip.ms.application',u'bip.ms.helper',u'bip.ms.daemon')):
            if (theactionid == indigo.kDimmerRelayAction.TurnOn):
                shellscript.run(dev.pluginProps[u'ApplicationStartPathName'])
                # status update will be done by runConcurrentThread

            elif (theactionid == indigo.kDimmerRelayAction.TurnOff):
                if dev.pluginProps[u'forceQuit']:
                    shellscript.run(u"kill %s" % (dev.states[u'ProcessID']))
                    # status update will be done by runConcurrentThread
                else:
                    osascript.run(u'''(* Tell to quit *)
                        %s''' % (dev.pluginProps[u'ApplicationStopPathName']))
                    # status update will be done by runConcurrentThread

        ##########
        # Volume device
        ########################
        elif (dev.deviceTypeId ==u'bip.ms.volume'):
            if (theactionid == indigo.kDimmerRelayAction.TurnOn) and (dev.states[u'VStatus']==u'notmounted'):
                shellscript.run(u"/usr/sbin/diskutil mount %s" % (dev.states[u'VolumeDevice']))
            # status update will be done by runConcurrentThread

            elif (theactionid == indigo.kDimmerRelayAction.TurnOff):
                if dev.pluginProps[u'forceQuit']:
                    shellscript.run(u"/usr/sbin/diskutil umount force %s" % (dev.states[u'VolumeDevice']))
                    # status update will be done by runConcurrentThread
                else:
                    shellscript.run(u"/usr/sbin/diskutil umount %s" % (dev.states[u'VolumeDevice']))
                    # status update will be done by runConcurrentThread


    ########################################
    # other callbacks
    ######################
    def closewindowsCBM(self,theaction):
        self.closeWindowAction(indigo.devices[theaction.deviceId])


    def closeWindowAction(self, thedevice):
        core.logger(traceLog = u'requesting device "%s" action %s' % (thedevice.name,u'closewindows'))
        osascript.run(u'''(* Tell to close window *)
            %s''' % (thedevice.pluginProps[u'windowcloseScript']))

    ########################################
    # Prefs UI methods (works with PluginConfig.xml):
    ######################

    # Validate the pluginConfig window after user hits OK
    # Returns False on failure, True on success
    #
    def validatePrefsConfigUi(self, valuesDict):
        core.logger(traceLog = u'validating Prefs called')

        errorMsgDict = indigo.Dict()
        err = False

        # manage debug flag
        valuesDict = core.debugFlags(valuesDict)

        core.logger(traceLog = u'end of validating Prefs')
        return (True, valuesDict)


    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        core.logger(traceLog = (u'validating Device Config called for: (%d - %s)') % (devId, typeId))
        core.dumpdict(valuesDict,u'input value dict %s is %s', level=core.MSG_STATES_DEBUG)
 
        # applications and helpers
        if typeId in (u'bip.ms.application',u'bip.ms.helper'):
            if (valuesDict[u'ApplicationID'])[-4:] == u'.app':
                valuesDict[u'ApplicationID'] = (valuesDict[u'ApplicationID'])[:-4]

            if not valuesDict[u'nameSpecial']:
                valuesDict[u'directoryPath'] = u'/Applications'

            if (valuesDict[u'directoryPath'])[-1:] == u'/':
                valuesDict[u'directoryPath'] = (valuesDict[u'directoryPath'])[:-1]
            
            valuesDict[u'ApplicationPathName'] = valuesDict[u'directoryPath'] + u'/' + valuesDict[u'ApplicationID'] + u'.app'
            valuesDict[u'ApplicationStartPathName'] = u'open %s' % (pipes.quote(valuesDict[u'ApplicationPathName']))

            if typeId in (u'bip.ms.application'):
                valuesDict[u'ApplicationStopPathName'] = u'tell application "'+ valuesDict[u'ApplicationID'] + u'" to quit'
                if not valuesDict[u'processSpecial']:
                    valuesDict[u'ApplicationProcessName'] = valuesDict[u'ApplicationID']
                if not valuesDict[u'windowcloseSpecial']:
                    valuesDict[u'windowcloseScript'] = u'tell application "' + valuesDict[u'ApplicationID'] + u'" to close every window'

            if typeId in (u'bip.ms.helper',u'bip.ms.daemon'):
                valuesDict[u'ApplicationProcessName'] = valuesDict[u'ApplicationID'] + u'(?: -.+)?'

        # daemons
        if typeId in (u'bip.ms.daemon'):
            valuesDict[u'ApplicationProcessName'] = valuesDict[u'ApplicationID'] + u'(?: -.+)?'
            valuesDict[u'ApplicationStartPathName'] = pipes.quote(valuesDict[u'ApplicationPathName']) + u' ' + valuesDict[u'ApplicationStartArgument']

            if len(valuesDict[u'ApplicationStopPathName'])==0:
                valuesDict[u'forceQuit'] = True
            else:
                valuesDict[u'forceQuit'] = False
                valuesDict[u'ApplicationStopPathName'] = pipes.quote(valuesDict[u'ApplicationPathName']) + u' ' + valuesDict[u'ApplicationStopArgument']

        core.dumpdict(valuesDict,u'output value dict %s is %s', level=core.MSG_STATES_DEBUG)
        core.logger(traceLog = u'end of validating Device Config')
        return (True, valuesDict)

