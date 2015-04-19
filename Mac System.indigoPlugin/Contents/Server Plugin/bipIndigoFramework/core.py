#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
""" Basic Framework helpers for indigo plugins
    
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
    Rev 1.0.0 :   initial version
"""
####################################################################################

import indigo

################################################################################
def debugFlags(valueDict):
    """ Get proporty value of standard indigo debug and an extra raw debug flag (plugin value)
        
        Args:
            valueDict: indigo dictionnary containing the following keys
        Keys:
            showDebugInfo: true for level 1 debug messages
            showShellLog: true for detailed debug messages including shell/osa info
    """
    try:
        if valueDict[u'showDebugInfo']:
            indigo.activePlugin.debug = True
        else:
            indigo.activePlugin.debug = False
        if valueDict[u'showShellLog']:
            indigo.activePlugin.debugraw = True
        else:
            indigo.activePlugin.debugraw = False
    except:
        pass


########################################
def logger(traceLog = None, traceRaw = None, msgLog = None, errLog = None ):
    """ Logger function extending the standard indigo log functions
        
        Args:
            traceLog: text to be inserted in log if plugin property showDebugInfo=True
            traceRaw: text to be inserted in log if plugin property showShellLog=True
            errLog: text to be inseted in log as an error
            msgLog: text to be inserted in log as standard message
            
            If both traceLog and traceRaw are given:
                - traceLog message only will be output if showDebugInfo=True and showShellLog=False
                - traceRaw message only will be output if showShellLog=True
            this allows to have a short trace message and a verbose one defined by the same call
            
            Messages are output in this order:
                - traceLog or traceRaw as they should detail what is going to be done
                - errLog as it should describe an error that occured
                - msgLog as it should conclude a successfull process
    """
    
    if indigo.activePlugin.debugraw and (traceRaw is not None):
        indigo.activePlugin.debugLog(traceRaw)
    elif traceLog is not None:
        indigo.activePlugin.debugLog(traceLog)
    if errLog is not None:
        indigo.activePlugin.errorLog(errLog)
    if msgLog is not None:
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
def updatestates(thedevice, thevaluesDict):
    """ Update device states on server and log if changed
        
        Args:
            thedevice: device object
            thevaluesDict: python dictionnay of the states names and values
        Returns:
            Python dictionnary of the states names and values that have been changed
        """

    updateDict = {}

    logger(traceRaw = u"Input Keys: Values   : %s" % (thevaluesDict))
    for thekey,thevalue in thevaluesDict.iteritems():
        theactualvalue=strutf8(thedevice.states[thekey])
        thevalue=strutf8(thevalue)

        if theactualvalue.lower() != thevalue.lower() :
            logger(traceRaw = u"%s value : %s <> %s" % (thekey, thedevice.states[thekey],thevalue), msgLog=u'received "%s" status %s update to %s' % (thedevice.name,thekey,thevalue))
            thedevice.updateStateOnServer(key=thekey, value=thevalue)
            updateDict[thekey]=thevalue
            logger(traceRaw = u"%s value : %s == %s" % (thekey, thedevice.states[thekey],thevalue))

    if len(updateDict)>0:
        indigo.activePlugin.sleep(0.2)

    logger(traceRaw = u"Updated Keys: Values   : %s" % (updateDict))

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
            logger(traceLog = u"device \"%s\" has special image for %s = %s" % (thedevice.name, thekey, thedict[thekey]))
            thedevice.updateStateImageOnServer(theimagedict[thedict[thekey]])
        else:
            logger(traceLog = u"device \"%s\" has automatic image for %s = %s" % (thedevice.name, thekey, thedict[thekey]))
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
    
    logger(traceRaw = u"Input Device Property Keys: Values   : %s" % (thevaluesDict))
    localprops = thedevice.pluginProps

    for thekey,thevalue in thevaluesDict.iteritems():
        theactualvalue=strutf8(localprops[thekey])
        thevalue=strutf8(thevalue)
        
        if theactualvalue.lower() != thevalue.lower() :
            logger(traceRaw = u"%s value : %s <> %s" % (thekey, localprops[thekey],thevalue), msgLog=u'received "%s" device property %s update to %s' % (thedevice.name,thekey,thevalue))
            localprops.update({thekey:thevalue})
            updateDict[thekey]=thevalue
            logger(traceRaw = u"%s value : %s == %s" % (thekey, localprops[thekey],thevalue))

    if len(updateDict)>0:
        thedevice.replacePluginPropsOnServer(localprops)
        indigo.activePlugin.sleep(0.2)
        
        logger(traceRaw = u"Updated Device Property: Values   : %s" % (updateDict))
    
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
    
    logger(traceRaw = u"Input Plugin Property Keys: Values   : %s" % (thevaluesDict))
    
    for thekey,thevalue in thevaluesDict.iteritems():
        theactualvalue=strutf8(indigo.activePlugin.pluginPrefs[thekey])
        thevalue=strutf8(thevalue)
        
        if theactualvalue.lower() != thevalue.lower() :
            logger(traceRaw = u"%s value : %s <> %s" % (thekey, indigo.activePlugin.pluginPrefs[thekey],thevalue), msgLog=u'received plugin propserty %s update to %s' % (thekey,thevalue))
            indigo.activePlugin.pluginPrefs[thekey] = thevalue
            updateDict[thekey]=thevalue
            logger(traceRaw = u"%s value : %s == %s" % (thekey, indigo.activePlugin.pluginPrefs[thekey],thevalue))

    if len(updateDict)>0:
        indigo.activePlugin.sleep(0.2)
        
        logger(traceRaw = u"Updated Plugin Property: Values   : %s" % (updateDict))
    
    return updateDict

