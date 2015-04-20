#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
""" Applescript helper for Indgo Plugin

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

import subprocess
import indigo
import core

########################################
def init():
    """ Initiate special applescript error handling
    """
    indigo.activePlugin._retryLog=dict()
    indigo.activePlugin._statusCheck=dict()
    indigo.activePlugin._errorMsg=dict()


########################################
def run(ascript, akeys =  None, errorHandling = None):
    """ Calls applescript script and returns the result as a python dictionnary

        Args:
            ascript: applescript as text
            akeys: list or keys, ordered the same way that output data of the applescript,
                   or None
            errorHandling : Dictionnary of status,value to check to cancel error (checked on ConcurrentThread) (not yet implemented)
                    or number of retry (integer)
                    or None if no special management
        Returns:
            python dictionnay of the states names and values,
            or unicode string returned by the script is akeys is None,
            or None if error
    """

    osaname = ascript.splitlines()[0]
    core.logger(traceRaw = u"going to call applescript %s" % (ascript),traceLog = u"going to call applescript %s" % (osaname))

    osa = subprocess.Popen(['osascript','-e',ascript],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           close_fds=True)
    indigo.activePlugin.sleep(0.25)
    (osavalues, osaerror) = osa.communicate()

    # error management
    if len(osaerror)>0:
        osaerror=osaerror[:-1].decode('utf-8')
        # test if error
        if errorHandling is None:
            core.logger(errLog = u"applescript %s failed because %s" % (osaname, osaerror))
            return None
        else:
            core.logger(traceLog = u"applescript %s error handling %s because %s" % (osaname, type(errorHandling), osaerror))
            if type(errorHandling) is int:
                # test if dictionnary exists
                if osaname in indigo.activePlugin._retryLog:
                    indigo.activePlugin._retryLog[osaname]=indigo.activePlugin._retryLog[osaname]+1
                    if indigo.activePlugin._retryLog[osaname] >= errorHandling:
                        core.logger(errLog = u"applescript %s failed after %s retry because %s" % (osaname, indigo.activePlugin._retryLog[osaname],osaerror))
                        return None
                else:
                    indigo.activePlugin._retryLog[osaname]=1
                indigo.activePlugin._errorMsg[osaname]= osaerror
                core.logger(traceLog = u"applescript %s failed %s time" % (osaname, indigo.activePlugin._retryLog[osaname]))
            elif type(errorHandling) is dict:
                indigo.activePlugin._statusCheck[osaname]=errorHandling
                indigo.activePlugin._errorMsg[osaname]= osaerror
                core.logger(traceLog = u"applescript %s failed - waiting for %s" % (osaname,errorHandling))
            # continue the process with a dummy value
            osavalues="\n"
    else:
        # a success sets the # retries to 0
        if type(errorHandling) is int:
            if osaname in indigo.activePlugin._retryLog:
                if (indigo.activePlugin._retryLog[osaname]>0) and (indigo.activePlugin._retryLog[osaname]<errorHandling):
                    core.logger(msgLog = u"warning on applescript %s : %s" % (osaname, indigo.activePlugin._errorMsg[osaname]))
                indigo.activePlugin._retryLog[osaname]=0
                indigo.activePlugin._errorMsg[osaname]=""

    # return value without error
    if akeys is None:
        # return text if no keys
        osavalues = core.strutf8(osavalues[:-1])
    else:
        # return list of values
        osavalues = dict(zip(akeys,(osavalues[:-1]).split("||")))
        for thekey,thevalue in osavalues.iteritems():
            osavalues[thekey] = core.strutf8(thevalue)

    core.logger(traceRaw = u"returned from applescript: %s" % (osavalues),traceLog = u"returned from applescript %s" % (osaname))

    return osavalues
