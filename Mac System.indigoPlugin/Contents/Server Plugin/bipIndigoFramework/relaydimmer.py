#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
""" Basic Relay and dimmer helpers for indigo plugins
    
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
import core

_kDimmerRelayActionDict = {indigo.kDimmerRelayAction.AllLightsOff:'AllLightsOff',
indigo.kDimmerRelayAction.AllLightsOn:'AllLightsOn',
indigo.kDimmerRelayAction.AllOff:'AllOff',
indigo.kDimmerRelayAction.BrightenBy:'BrightenBy',
indigo.kDimmerRelayAction.DimBy:'DimBy',
indigo.kDimmerRelayAction.SetBrightness:'SetBrightness',
indigo.kDimmerRelayAction.Toggle:'Toggle',
indigo.kDimmerRelayAction.TurnOff:'TurnOff',
indigo.kDimmerRelayAction.TurnOn:'TurnOn'}

################################################################################
def startAction(thedevice, theaction):
    """ Check if the device is already in the required state - transform toggle in on or off
        
        Args:
            thedevice: current device
            theaction: indigo action
        Returns:
            None or action to provide
    """

    theactionid = theaction.deviceAction
    core.logger(traceLog = u"requesting device \"%s\" action %s " % (thedevice.name,_kDimmerRelayActionDict[theactionid]))
    # work on toggling
    if theactionid == indigo.kDimmerRelayAction.Toggle:
        if thedevice.states['onOffState']:
            theactionid = indigo.kDimmerRelayAction.TurnOff
        else:
            theactionid = indigo.kDimmerRelayAction.TurnOn

    # test if needed
    if (theaction == indigo.kDimmerRelayAction.TurnOn) and (thedevice.states['onOffState']):
        core.logger(msgLog= u"device %s is already on" % (thedevice.name))
        return None

    if (theaction == indigo.kDimmerRelayAction.TurnOff) and not(thedevice.states['onOffState']):
        core.logger(msgLog = u"device %s is already off" % (thedevice.name))
        return None

    # go for the action
    core.logger(msgLog = u"sent device \"%s\" action %s " % (thedevice.name,_kDimmerRelayActionDict[theactionid]))
    return theactionid
