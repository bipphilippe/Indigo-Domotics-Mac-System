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


# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.

def init():
    osascript.init()
    shellscript.init()


##########
# Application device
########################
pStatusDict ={'I':u"idle",'R':u"runnable", 'S':u"running", 'T':u"stopped", 'U':u"waiting", 'Z':u"zombie" }

def getProcessStatus(thedevice, thevaluesDict):
    """ Searches for the task in system tasklist and returns onOff states
        
        Args:
            thedevice: current device
            thevaluesDict: dictionary of the status values so far
        Returns:
            success: True if success, False if not
            thevaluesDict updated with new data if success, equals to the input if not
    """
    pslist = shellscript.run(u"ps -awxc -opid,state,comm | grep '" + thedevice.pluginProps['ApplicationID'] + "$'",[(0,6),(6,7)],['ProcessID','PStatus'])
    
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
    pslist = shellscript.run(u"ps -awxc -opid,lstart,etime,pcpu,pmem,state,comm | grep '" + thedevice.pluginProps['ApplicationID'] + "$'",[(0,6),(6,31),(31,47),(47,53),(53,58),(58,59)],['ProcessID','LStart','ETime','PCpu','PMem','PStatus'])

    if pslist['ProcessID']=='':
        thevaluesDict["onOffState"]=False
        thevaluesDict["ProcessID"]=0
        thevaluesDict["PStatus"]="off"
        thevaluesDict["LStart"]=""
        thevaluesDict["ETime"]=0
        thevaluesDict["PCpu"]=0
        thevaluesDict["PMem"]=0
    else:
        thevaluesDict["onOffState"]=True
        thevaluesDict.update(pslist)
        # special update for process status
        thevaluesDict["PStatus"]= pStatusDict[thevaluesDict["PStatus"]]
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
    if shellscript.run(u"ls -1 /Volumes | grep '^" + thedevice.pluginProps['VolumeID'] +"$'")>'':
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
    pslist = shellscript.run(u"/usr/sbin/diskutil list | grep ' " + thedevice.pluginProps['VolumeID'] +"  '",[(6,32),(57,67),(68,-1)],['VolumeType','VolumeSize','VolumeDevice'])

    if pslist['VolumeDevice']=='':
        thevaluesDict["onOffState"]=False
        thevaluesDict["VStatus"]="off"
    else:
        thevaluesDict.update(pslist)
        # check if mounted
        if shellscript.run(u"ls -1 /Volumes | grep '^" + thedevice.pluginProps['VolumeID'] +"$'")>'':
            # find free space
            pslist = shellscript.run(u"/bin/df | grep '" + thevaluesDict['VolumeDevice'] +"'",re.compile(r".+? [0-9]+ +([0-9]+) +([0-9]+) .+"),['Used','Available'])
            thevaluesDict['pcUsed']= (int(pslist['Used'])*100)/(int(pslist['Used']) + int(pslist['Available']))
            # status on
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
        psvalue = shellscript.run(u"touch '/Volumes/" + thedevice.pluginProps['VolumeID'] + "/.spinner'")
        if psvalue is None:
            return (False, thevaluesDict)
        else:
            thevaluesDict['LastPing']=time.strftime('%c',time.localtime())
    return (True, thevaluesDict)

