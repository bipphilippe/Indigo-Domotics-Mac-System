#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
""" Basic Framework helpers for indigo plugins

    By Bernard Philippe (bip.philippe) (C) 2015
    upgradeDevice function inspired from Rogue Amoeba framework

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

MSG_MAIN_EVENTS = 1
MSG_SECONDARY_EVENTS = 2
MSG_DEBUG = 4
MSG_RAW_DEBUG = 8
MSG_STATES_DEBUG = 16
MSG_DEBUGS = (MSG_DEBUG | MSG_RAW_DEBUG | MSG_STATES_DEBUG)

_debugStateDict = {u'logMainEvents':MSG_MAIN_EVENTS, u'logSecondaryEvents':MSG_SECONDARY_EVENTS, u'logDebug':MSG_DEBUG, u'logRawDebug':MSG_RAW_DEBUG, u'logStateDebug':MSG_STATES_DEBUG}

#ALL_DEBUGS = (MSG_DEBUG | MSG_RAW_DEBUG | MSG_STATES_DEBUG)

################################################################################
def debugFlags(valueDict):
    """ Get proporty value of standard indigo debug and an extra raw debug flag (plugin value)

        Args:
            valueDict: indigo dictionnary containing the following keys
        Keys:
            logLevel: level of messaging
    """
    try:
        thelevel = int(valueDict[u'logLevel'])
    except:
        thelevel = MSG_MAIN_EVENTS

    if thelevel == 99:
        indigo.activePlugin.logLevel = 0
        for key,value in _debugStateDict.iteritems():
            if valueDict[key]:
                indigo.activePlugin.logLevel = indigo.activePlugin.logLevel | value
    else:
        indigo.activePlugin.logLevel = thelevel
        for key,value in _debugStateDict.iteritems():
            if thelevel & value:
                valueDict[key]=True
            else:
                valueDict[key]=False

    if indigo.activePlugin.logLevel & MSG_DEBUGS:
        indigo.activePlugin.debug = True
    else:
        indigo.activePlugin.debug = False

    return valueDict


########################################
def logger(traceLog = None, traceRaw = None, msgLog = None, errLog = None, isMain=True ):
    """ Logger function extending the standard indigo log functions

        Args:
        traceLog: text to be inserted in log if plugin property logLevel contains MSG_DEBUG
        traceRaw: text to be inserted in log if plugin property loglevel contains MSG_RAW_DEBUG
        errLog: text to be inseted in log as an error (any logLevel)
        msgLog: text to be inserted in log as standard message if plugin property loglevel contains MSG_MAIN_EVENTS
        or MSG_SECONDARY_EVENTS, depending on isMain
        isMain : true is the message is a MSG_MAIN_EVENTS

        If both traceLog and traceRaw are given:
        - traceLog message only will be output if logLevel contains MSG_DEBUG and not MSG_RAW_DEBUG
        - traceRaw message only will be output if logLevel contains MSG_RAW_DEBUG
        this allows to have a short trace message and a verbose one defined by the same call

        Messages are output in this order:
        - traceLog or traceRaw as they should detail what is going to be done
        - errLog as it should describe an error that occured
        - msgLog as it should conclude a successfull process
    """

    # debug messages
    if (indigo.activePlugin.logLevel & MSG_RAW_DEBUG) and (traceRaw is not None):
        indigo.activePlugin.debugLog(traceRaw)
    elif (indigo.activePlugin.logLevel & MSG_DEBUG) and (traceLog is not None):
        indigo.activePlugin.debugLog(traceLog)

    # error message
    if errLog is not None:
        indigo.activePlugin.errorLog(errLog)

    # log message (the two levels, depending on msgSec)
    if (msgLog is not None) and ((indigo.activePlugin.logLevel & MSG_SECONDARY_EVENTS) or ((indigo.activePlugin.logLevel & MSG_MAIN_EVENTS) and isMain)):
        indigo.server.log(msgLog)


########################################
def strutf8(data):
    """ Generic utf-8 conversion function

        Args:
        data: input data (any type)
        Returns:
        unicode text
        """
    if type(data) is str:
        data = data.decode('utf-8')
    elif type(data) is unicode:
        pass
    else:
        data = str(data).decode('utf-8')
    return data

########################################
def formatdump(data):
    """ Generic replace function if data is empty and format with tyoe

        Args:
            data: input data (any type)
        Returns:
            data if not empty or ''
    """

    if data is None:
        return u'None'
    elif type(data) in (str,unicode):
        return u"'"+data+u"'"
    else:
        return data


########################################
def dumpdict(thedict, theformat=u'"%s" is %s', ifempty='', excludeKeys= (), level=MSG_MAIN_EVENTS):
    """ Dump a dictionnary,

        Args:
            thedict: dictionnary object
            theformat: formatting string
            ifempty: text displayed if empty
            level: debug level needed
    """

    if indigo.activePlugin.logLevel & level:
        if len(thedict)>0:
            for thekey,thevalue in thedict.iteritems():
                if thekey not in excludeKeys:
                    if level & MSG_DEBUGS:
                        indigo.activePlugin.debugLog(theformat % (thekey, formatdump(thevalue)))
                    else:
                        indigo.server.log(theformat % (thekey, formatdump(thevalue)))
        elif len(ifempty)>0:
            indigo.server.log(strutf8(ifempty))


########################################
def dumplist(thelist, theformat=u'"%s"', ifempty='', level=MSG_MAIN_EVENTS):
    """ Dump a list

        Args:
            thelist: list object
            theformat: formatting string
            ifempty: text displayed if empty
            level: debug level needed
        """

    if indigo.activePlugin.logLevel & level:
        if len(thelist)>0:
            for thevalue in thelist:
                if level & MSG_DEBUGS:
                    indigo.activePlugin.debugLog(theformat % (formatdump(thevalue)))
                else:
                    indigo.server.log(theformat % (formatdump(thevalue)))
        elif len(ifempty)>0:
            indigo.server.log(strutf8(ifempty))

########################################
def dumppluginproperties():
    """ Dump plugin properties
    """

    dumpdict(indigo.activePlugin.pluginPrefs,u'Plugin property %s is %s', level=MSG_DEBUG)

########################################
def dumpdevicestates(thedevice):
    """ Dump device states

        Args:
            thedevice: device object
    """

    dumpdict(thedevice.states,u'"'+thedevice.name+'" state %s is %s', level=MSG_DEBUG)

########################################
def dumpdeviceproperties(thedevice):
    """ Dump device properties

        Args:
            thedevice: device object
    """

    dumpdict(thedevice.pluginProps, u'"' + thedevice.name + '" property %s is %s', level=MSG_DEBUG)

########################################
def updatestates(thedevice, thevaluesDict):
    """ Update device states on server and log if changed

        Args:
            thedevice: device object
            thevaluesDict: python dictionnay of the states names and values
        Returns:
            Python dictionnary of the states names and values that have been changed
    """

    updateDict = {}

    for thekey,thevalue in thevaluesDict.iteritems():
        theactualvalue=thedevice.states[thekey]
        if type(theactualvalue) is str:
            theactualvalue = theactualvalue.decode('utf-8')
        if type(thevalue) is str:
            thevalue=thevalue.decode('utf-8')

        if theactualvalue != thevalue :
            logger(traceRaw = u'"%s" %s value : %s != %s' % (thedevice.name, thekey, formatdump(thedevice.states[thekey]),formatdump(thevalue)))
            thedevice.updateStateOnServer(key=thekey, value=thevalue)
            updateDict[thekey]=thevalue
        else:
            logger(traceRaw = u'"%s" %s value : %s == %s' % (thedevice.name, thekey, formatdump(thedevice.states[thekey]),formatdump(thevalue)))

    if len(updateDict)>0:
        indigo.activePlugin.sleep(0.2)
        if (thedevice.displayStateId in updateDict):
            thelevel = MSG_MAIN_EVENTS
        else:
            thelevel = MSG_SECONDARY_EVENTS
        dumpdict(updateDict,theformat=u'received "'+thedevice.name+'" status %s update to %s', level=thelevel)

    return updateDict


########################################
def specialimage(thedevice, thekey, thedict, theimagedict):
    """ Set special image according device state - or to auto if no value defined in theimagedict

        Args:
            thedevice: device object
            thekey : state key to choose the image
            thedict : dictionnary of key,value (ie : an update dictionary as returned by updatestates)
            theimagedict: python dictionnay of the states names and image (enumeration)
    """

    if thekey in thedict:
        if thedict[thekey] in theimagedict:
            logger(traceLog = u'device "%s" has special image for %s with vakue %s' % (thedevice.name, thekey, formatdump(thedict[thekey])))
            thedevice.updateStateImageOnServer(theimagedict[thedict[thekey]])
        else:
            logger(traceLog = u'device "%s" has automatic image for %s with value %s' % (thedevice.name, thekey, formatdump(thedict[thekey])))
            thedevice.updateStateImageOnServer(indigo.kStateImageSel.Auto)


########################################
def updatedeviceprops(thedevice, thevaluesDict):
    """ Update device properties on server and log if changed

        Args:
            thedevice: device object
            thevaluesDict: python dictionnay of the states names and values
        Returns:
            Python dictionnary of the states names and values that have been changed
    """

    updateDict = {}
    localprops = thedevice.pluginProps

    for thekey,thevalue in thevaluesDict.iteritems():
        theactualvalue=localprops[thekey]
        if type(theactualvalue) is str:
            theactualvalue = theactualvalue.decode('utf-8')
        if type(thevalue) is str:
            thevalue=thevalue.decode('utf-8')

        if theactualvalue != thevalue :
            logger(traceRaw = u'"%s" value : %s <> %s' % (thekey, formatdump(localprops[thekey]),formatdump(thevalue)))
            localprops.update({thekey:thevalue})
            updateDict[thekey]=thevalue
        else:
            logger(traceRaw = u'"%s" value : %s == %s' % (thekey, formatdump(localprops[thekey]),formatdump(thevalue)))

        if len(updateDict)>0:
            indigo.activePlugin.sleep(0.2)
            dumpdict(updateDict,theformat=u'"'+thedevice.name+'" property %s updated to %s', level=MSG_MAIN_EVENTS)

    return updateDict


########################################
def updatepluginprops(thevaluesDict):
    """ Update plugin properties on server and log if changed

        Args:
            theplugin: plugin object
            thevaluesDict: python dictionnay of the states names and values
        Returns:
            Python dictionnary of the states names and values that have been changed
    """

    updateDict = {}
    for thekey,thevalue in thevaluesDict.iteritems():
        theactualvalue=indigo.activePlugin.pluginPrefs[thekey]
        if type(theactualvalue) is str:
            theactualvalue = theactualvalue.decode('utf-8')
        if type(thevalue) is str:
            thevalue=thevalue.decode('utf-8')

        if theactualvalue != thevalue:
            logger(traceRaw = u'property %s value: %s != %s' % (thekey, formatdump(indigo.activePlugin.pluginPrefs[thekey],formatdump(thevalue))))
            indigo.activePlugin.pluginPrefs[thekey] = thevalue
            updateDict[thekey]=thevalue
        else:
            logger(traceRaw = u'property %s value: %s == %s' % (thekey, formatdump(indigo.activePlugin.pluginPrefs[thekey]),formatdump(thevalue)))

        if len(updateDict)>0:
            indigo.activePlugin.sleep(0.2)
            dumpdict(updateDict,theformat=u'pluging property %s updated to %s', level=MSG_MAIN_EVENTS)

    return updateDict


########################################
def upgradeDeviceProperties(thedevice, theUpgradePropertyDict):
    """ Update plugin properties on server and log if changed
        Inspired from Rogue Amoeba framework

        Args:
            thedevice: device object
            theUpgradePropertyDict: python dictionnay of the properties names and default values

            Syntax of a theUpgradePropertyDict dictionnary item (a,c)
                a: name of the property/device
                c: value

        Returns;
            dictionnary of the updates
    """

    dumplist(theUpgradePropertyDict.keys(), u'"' + thedevice.name + u'" requires property %s',level=MSG_STATES_DEBUG)

    theupdatedict={}
    pluginPropsCopy = thedevice.pluginProps
    for newPropertyDefn, newPropertyDefv in theUpgradePropertyDict.iteritems():
        if not (newPropertyDefn in pluginPropsCopy):
            logger(traceRaw=u'"%s" property update due to missing %s property with value: %s' % (thedevice.name,newPropertyDefn,formatdump(newPropertyDefv)))
            pluginPropsCopy[newPropertyDefn] = newPropertyDefv
            theupdatedict[newPropertyDefn] = newPropertyDefv
    if len(theupdatedict)>0:
        thedevice.replacePluginPropsOnServer(pluginPropsCopy)
        dumpdict(theupdatedict, u'"' + thedevice.name + u'" property %s created with value %s',level=MSG_DEBUG)
        logger(msgLog=u'"%s" new properties added' % thedevice.name)
    else:
        logger(msgLog=u'"%s" property list is up to date' % thedevice.name)

    return theupdatedict

########################################
def upgradeDeviceStates(thedevice, theUpgradeStatesList):
    """ Update plugin states on server and log if changed
        Inspired from Rogue Amoeba framework

        Args:
            thedevice: device object
            theUpgradeStatesList: python dictionnay of the states names

        Returns;
            list of the updates
    """

    dumplist(theUpgradeStatesList, u'"' + thedevice.name + u'" requires state %s',level=MSG_STATES_DEBUG)

    theupdatelist=()
    for newStateName in theUpgradeStatesList:
        if not (newStateName in self.indigoDevice.states):
            logger(traceRaw=u'"%s" state %s missing' % (thedevice.name,newStateName))
            theupdatelist = theupdatelist + newStateName
    if len(theupdatelist)>0:
        thedevice.stateListOrDisplayStateIdChanged();
        dumplist(theupdatelist, u'"%s" states added' % (thedevice.name),level=MSG_DEBUG)
        logger(msgLog=u'"%s" new states added' % thedevice.name)
    else:
        logger(msgLog=u'"%s" state list is up to date' % thedevice.name)
    return theupdatelist
