#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
"""
    Mac OS System plug-in interface module
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
"""
####################################################################################

import indigo
import time
from bipIndigoFramework import core
from bipIndigoFramework import osascript
from bipIndigoFramework import shellscript
import re
import pipes



# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.

_repProcessStatus = re.compile(r" *([0-9]+) +(.).+$")
_repProcessData = re.compile(r"(.+?)  +([0-9.,]+) +([0-9.,]+) +(.+)$")
_repVolumeData2 = re.compile(r".+? [0-9]+ +([0-9]+) +([0-9]+) .+")

def init():
    osascript.init()
    shellscript.init()


##########
# Application device
########################
pStatusDict ={'I':u'idle','R':u'running', 'S':u'running', 'T':u'stopped', 'U':u'waiting', 'Z':u'zombie' }

def getProcessStatus(thedevice, thevaluesDict):
    """ Searches for the task in system tasklist and returns onOff states

        Args:
            thedevice: current device
            thevaluesDict: dictionary of the status values so far
        Returns:
            success: True if success, False if not
            thevaluesDict updated with new data if success, equals to the input if not
    """
    pslist = shellscript.run(u"ps -awxc -opid,state,args | egrep %s" % (pipes.quote(u' ' + thedevice.pluginProps[u'ApplicationProcessName']+u'$')),_repProcessStatus,[u'ProcessID',u'PStatus'])

    if pslist[u'ProcessID']==u'':
        thevaluesDict[u'onOffState']=False
        thevaluesDict[u'ProcessID']=0
        thevaluesDict[u'PStatus']="off"
    else:
        thevaluesDict[u'onOffState']=True
        thevaluesDict.update(pslist)
        # special update for process status
        thevaluesDict[u'PStatus']= pStatusDict[thevaluesDict[u'PStatus']]

    return (True,thevaluesDict)

def getProcessData(thedevice, thevaluesDict):
    """ Searches for the task in system tasklist and returns states data

        Args:
            thedevice: current device
            thevaluesDict: dictionary of the status values so far
        Returns:
            success: True if success, False if not
            thevaluesDict updated with new data if success, equals to the input if not
    """
    pslist = shellscript.run(u"ps -wxc -olstart,pcpu,pmem,etime -p%s | sed 1d" % (thevaluesDict[u'ProcessID']),_repProcessData,[u'LStart','PCpu','PMem','ETime'])

    if pslist[u'LStart']=='':
        thevaluesDict[u'onOffState']=False
        thevaluesDict[u'ProcessID']=0
        thevaluesDict[u'PStatus']="off"
        thevaluesDict[u'LStart']=""
        thevaluesDict[u'ETime']=0
        thevaluesDict[u'PCpu']=0
        thevaluesDict[u'PMem']=0
    else:
        thevaluesDict.update(pslist)
        # special update for ellapsed time : convert to seconds
        try:
            (longday,longtime)=thevaluesDict[u'ETime'].split('-')
        except:
            longtime=thevaluesDict[u'ETime']
            longday=0
        try:
        	(longh,longm,longs)=longtime.split(':')
        except:
        	(longm,longs)=longtime.split(':')
        	longh=0
		thevaluesDict[u'ETime']= ((int(longday)*24 + int(longh))*60 + int(longm))*60 + int(longs)

    return (True,thevaluesDict)

##########
# Volume device
########################
def getVolumeStatus(thedevice, thevaluesDict):
    """ Searches for the volume to return states OnOff only

        Args:
            thedevice: current device
            thevaluesDict: dictionary of the status values so far
        Returns:
            success: True if success, False if not
            thevaluesDict updated with new data if success, equals to the input if not
    """
    # check if mounted
    if shellscript.run(u"ls -1 /Volumes | grep %s" % (pipes.quote(u'^'+thedevice.pluginProps[u'VolumeID']+u'$')))>'':
        thevaluesDict[u'onOffState']=True
        thevaluesDict[u'VStatus']="on"
    else:
        thevaluesDict[u'onOffState']=False

    return (True,thevaluesDict)

def getVolumeData(thedevice, thevaluesDict):
    """ Searches for the volume using system diskutil and df to return states data

        Args:
            thedevice: current device
            thevaluesDict: dictionary of the status values so far
        Returns:
            success: True if success, False if not
            thevaluesDict updated with new data if success, equals to the input if not
        """
    pslist = shellscript.run(u"/usr/sbin/diskutil list | grep %s" % (pipes.quote(u' '+thedevice.pluginProps[u'VolumeID']+u'  ')),[(6,32),(57,67),(68,-1)],[u'VolumeType',u'VolumeSize',u'VolumeDevice'])

    if pslist[u'VolumeDevice']=='':
        thevaluesDict[u'onOffState']=False
        thevaluesDict[u'VStatus']=u'off'
    else:
        thevaluesDict.update(pslist)
        # find free space
        pslist = shellscript.run(u"/bin/df | grep '%s'" % (thevaluesDict[u'VolumeDevice']),_repVolumeData2,[u'Used','Available'])
        if pslist[u'Used'] !=u'':
            thevaluesDict[u'pcUsed']= (int(pslist[u'Used'])*100)/(int(pslist[u'Used']) + int(pslist[u'Available']))
            thevaluesDict[u'onOffState']=True
            thevaluesDict[u'VStatus']=u'on'
        else:
            thevaluesDict[u'onOffState']=False
            thevaluesDict[u'VStatus']=u'notmounted'

    return (True,thevaluesDict)


def spinVolume(thedevice, thevaluesDict):
    """ Touch a file to keep the disk awaken

        Args:
            thedevice: current device
            thevaluesDict: dictionary of the status values so far
        Returns:
            success: True if success, False if not
            thevaluesDict updated with new data if success, equals to the input if not
        """

    if (thedevice.states[u'VStatus']==u'on') and (thedevice.pluginProps[u'keepAwaken']):
        psvalue = shellscript.run(u"touch %s" % (pipes.quote(u'/Volumes/'+thedevice.pluginProps[u'VolumeID']+u'/.spinner')))
        if psvalue is None:
            return (False, thevaluesDict)
        else:
            thevaluesDict[u'LastPing']=time.strftime('%c',time.localtime())
    return (True, thevaluesDict)

