#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
""" Basic Framework helpers for indigo plugins concurrentThread
    
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
import core
import time
from threading import Timer


def init():
    """ Initiate
    """
    indigo.activePlugin._requestedUpdate = dict()

########################################
def setUpdateRequest(thedevice, nbTime=1):
    """ set the device states to be updated
        
    Args:
        thedevice: current device
    """

    core.logger(traceLog = u'Device "%s" has %s update requests stacked' % (thedevice.name,nbTime))
    indigo.activePlugin._requestedUpdate[thedevice.id]=nbTime


########################################
def isUpdateRequested(thedevice):
    """ Test is the device states need to be updated
        
        Args:
            thedevice: current device
        Returns:
            True is updateRequested
        """
    
    if thedevice.id in indigo.activePlugin._requestedUpdate:
        if indigo.activePlugin._requestedUpdate[thedevice.id]>0:
            indigo.activePlugin._requestedUpdate[thedevice.id] = indigo.activePlugin._requestedUpdate[thedevice.id]-1
            core.logger(traceLog = u'Device "%s" is going to process an update request' % (thedevice.name))
            return True

    return False


########################################
def sleepNext(thetime):
    """ Calculate sleep time according main dialog pace
        
        Args:
            thetime: time in seconds between two dialog calls
    """

    nextdelay = thetime - (time.time() - indigo.activePlugin.wakeup)

    nextdelay = round(nextdelay,2)
    if nextdelay < 1:
        nextdelay = 0.5

    core.logger(traceLog = u'going to sleep for %s seconds' % (nextdelay))
    indigo.activePlugin.sleep(nextdelay)


def sleepWake():
    """ Take the time before one ConcurrentThread run
    """

    indigo.activePlugin.wakeup = time.time()


########################################
class dialogTimer(object):
    """ Timer to be used in runConcurrentThread for dialogs that needs to be made less often that the runConcurrentThread pace
    """
    def __init__(self, timername, interval, initialinterval=0):
        """ Constructor

            Args:
                timername : name of the timer (for logging use)
                interval: interval in seconds
                initialinterval : first interval in seconds (ignored if 0)
            Returns:
                dialogTimer class instance
        """
        self._timer     = None
        self.timername = timername
        self.initialinterval = initialinterval
        self.interval   = interval
        self.timeEllapsed = True
        core.logger(traceLog = u'initiating dialog timer "%s" on a %s seconds pace' % (self.timername, interval))
        self._run()

    def __del__(self):
        core.logger(traceLog = u'deleting dialog timer "%s"' % (self.timername))
        self._timer.cancel()
    
    def _run(self):
        core.logger(traceLog = u'time ellapsed for dialog timer "%s"' % (self.timername))
        self.timeEllapsed = True
        if self.initialinterval>0:
            self._timer = Timer(self.initialinterval, self._run)
            self.initialinterval=0
        else:
            self._timer = Timer(self.interval, self._run)
        self._timer.start()

    def changeInterval(self, interval):
        """ Change interval value - restart the timer to take the new value in account
        
        Args:
            interval: interval in seconds
        """
        self.interval = interval
        core.logger(traceLog = u'restarting with new timing value %s for dialog timer "%s"' % (interval, self.timername))
        self._timer.cancel()
        self._run()

    def doNow(self):
        """ Stop the current timing and set isTime to true
        """
        core.logger(traceLog = u'forced time ellapsed for dialog timer "%s"' % (self.timername))
        self._timer.cancel()
        self._run()

    def isTime(self):
        """ True if the timing is ellapsed
            
            Note : returns true When the class instance is created
        """
        if self.timeEllapsed:
            self.timeEllapsed = False
            return True
        else:
            return False
