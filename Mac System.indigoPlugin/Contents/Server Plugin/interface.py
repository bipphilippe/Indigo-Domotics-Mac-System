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
pStatusDict ={'I':u"idle",'R':u"running", 'S':u"running", 'T':u"stopped", 'U':u"waiting", 'Z':u"zombie" }

def getProcessStatus(thedevice, thevaluesDict):
    """ Searches for the task in system tasklist and returns onOff states

        Args:
            thedevice: current device
            thevaluesDict: dictionary of the status values so far
        Returns:
            success: True if success, False if not
            thevaluesDict updated with new data if success, equals to the input if not
    """
    pslist = shellscript.run(u"ps -awxc -opid,state,comm | grep %s" % (pipes.quote(u' ' + thedevice.pluginProps['ApplicationID']+u'$')),_repProcessStatus,['ProcessID','PStatus'])

    if pslist['ProcessID']=='':
        thevaluesDict["onOffState"]=False
        thevaluesDict["ProcessID"]=0
        thevaluesDict["PStatus"]="off"
    else:
        thevaluesDict["onOffState"]=True
        thevaluesDict.update(pslist)
        # special update for process status
        thevaluesDict["PStatus"]= pStatusDict[thevaluesDict["PStatus"]]

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
    pslist = shellscript.run(u"ps -wxc -olstart,pcpu,pmem,etime -p%s | sed 1d" % (thevaluesDict["ProcessID"]),_repProcessData,['LStart','PCpu','PMem','ETime'])

    if pslist['LStart']=='':
        thevaluesDict["onOffState"]=False
        thevaluesDict["ProcessID"]=0
        thevaluesDict["PStatus"]="off"
        thevaluesDict["LStart"]=""
        thevaluesDict["ETime"]=0
        thevaluesDict["PCpu"]=0
        thevaluesDict["PMem"]=0
    else:
        thevaluesDict.update(pslist)
        # special update for ellapsed time : convert to seconds
        try:
            (longday,longtime)=thevaluesDict["ETime"].split('-')
        except:
            longtime=thevaluesDict["ETime"]
            longday=0
        try:
        	(longh,longm,longs)=longtime.split(':')
        except:
        	(longm,longs)=longtime.split(':')
        	longh=0
		thevaluesDict["ETime"]= ((int(longday)*24 + int(longh))*60 + int(longm))*60 + int(longs)

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
    if shellscript.run(u"ls -1 /Volumes | grep %s" %(pipes.quote(u'^'+thedevice.pluginProps['VolumeID']+u'$')))>'':
        thevaluesDict["onOffState"]=True
        thevaluesDict["VStatus"]="on"
    else:
        thevaluesDict["onOffState"]=False

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
    pslist = shellscript.run(u"/usr/sbin/diskutil list | grep %s" % (pipes.quote(u' '+thedevice.pluginProps['VolumeID']+u'  ')),[(6,32),(57,67),(68,-1)],['VolumeType','VolumeSize','VolumeDevice'])

    if pslist['VolumeDevice']=='':
        thevaluesDict["onOffState"]=False
        thevaluesDict["VStatus"]="off"
    else:
        thevaluesDict.update(pslist)
        # find free space
        pslist = shellscript.run(u"/bin/df | grep '%s'" % (thevaluesDict['VolumeDevice']),_repVolumeData2,['Used','Available'])
        if pslist['Used'] !='':
            thevaluesDict['pcUsed']= (int(pslist['Used'])*100)/(int(pslist['Used']) + int(pslist['Available']))
            thevaluesDict["onOffState"]=True
            thevaluesDict["VStatus"]="on"
        else:
            thevaluesDict["onOffState"]=False
            thevaluesDict["VStatus"]="notmounted"

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

    if (thedevice.states["VStatus"]=="on") and (thedevice.pluginProps["keepAwaken"]):
        psvalue = shellscript.run(u"touch %s" % (pipes.quote(u'/Volumes/'+thedevice.pluginProps['VolumeID']+u'/.spinner')))
        if psvalue is None:
            return (False, thevaluesDict)
        else:
            thevaluesDict['LastPing']=time.strftime('%c',time.localtime())
    return (True, thevaluesDict)

