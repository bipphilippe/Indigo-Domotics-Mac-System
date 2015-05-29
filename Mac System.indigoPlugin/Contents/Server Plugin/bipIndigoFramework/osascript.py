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
"""
####################################################################################

import subprocess
import indigo
import core
import re

_repCloseAppErrorFilter = re.compile(r".Library.ScriptingAdditions.")
_valueConvertDict = {u'True':True, u'true':True, u'False':False, u'false':False}

########################################
def init():
    """ Initiate special applescript error handling
    """
    indigo.activePlugin._retryLog=dict()
    indigo.activePlugin._errorMsg=dict()


########################################
def run(ascript, akeys =  None, errorHandling = None):
    """ Calls applescript script and returns the result as a python dictionnary

        Args:
            ascript: applescript as text
            akeys: list of keys, ordered the same way that output data of the applescript,
                   or None
            errorHandling : a compiled regular expression matching errors to ignore
                    or number of retry (integer)
                    or None if no special management
        Returns:
            python dictionnay of the states names and values,
            or unicode string returned by the script is akeys is None,
            or None if error
    """

    osaname = ascript.splitlines()[0]
    core.logger(traceRaw = u'going to call applescript %s' % (ascript),traceLog = u'going to call applescript %s' % (osaname))

    osa = subprocess.Popen([u'osascript','-e',ascript],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           close_fds=True)
    indigo.activePlugin.sleep(0.25)
    (osavalues, osaerror) = osa.communicate()

    # error management
    if len(osaerror)>0:
        osaerror2=osaerror[:-1].decode('utf-8')
        # filter standard errors due to old mac configuration
        osaerror=u''
        filterederror=u''
        for theline in osaerror2.splitlines():
            if _repCloseAppErrorFilter.search(theline) is None:
                osaerror = osaerror + theline + u'\n'
            else:
                filterederror = filterederror + theline + u'\n'
        if filterederror>u'':
            core.logger(traceLog=u'warning: applescript %s error filtered as not significant' % (osaname), traceRaw = u'warning: applescript %s following error filtered: %s' % (osaname, filterederror[:-1]))

    # test if error
    if len(osaerror)>0:
        osaerror=osaerror[:-1]
        if errorHandling is None:
            core.logger(traceLog=u'no error handling', errLog = u'applescript %s failed because %s' % (osaname, osaerror))
            return None
        else:
            core.logger(traceLog = u'applescript %s error handling %s because %s' % (osaname, type(errorHandling), osaerror))
            if type(errorHandling) is int:
                # test if dictionnary exists
                if osaname in indigo.activePlugin._retryLog:
                    indigo.activePlugin._retryLog[osaname]=indigo.activePlugin._retryLog[osaname]+1
                    if indigo.activePlugin._retryLog[osaname] >= errorHandling:
                        core.logger(errLog = u'applescript %s failed after %s retry because %s' % (osaname, indigo.activePlugin._retryLog[osaname],osaerror))
                        return None
                else:
                    indigo.activePlugin._retryLog[osaname]=1
                indigo.activePlugin._errorMsg[osaname]= osaerror
                core.logger(traceLog = u'applescript %s failed %s time' % (osaname, indigo.activePlugin._retryLog[osaname]))
            else:
                if errorHandling.search(osaerror) is None:
                    core.logger(errLog = u'applescript %s failed because %s' % (osaname ,osaerror))
                else:
                    core.logger(msgLog = u'warning on applescript %s : %s' % (osaname, osaerror), isMain=False)

            # continue the process with a dummy value
            osavalues=u'\n'
    else:
        # a success sets the # retries to 0
        if type(errorHandling) is int:
            if osaname in indigo.activePlugin._retryLog:
                if (indigo.activePlugin._retryLog[osaname]>0) and (indigo.activePlugin._retryLog[osaname]<errorHandling):
                    core.logger(msgLog = u'warning on applescript %s : %s' % (osaname, indigo.activePlugin._errorMsg[osaname]), isMain=False)
                indigo.activePlugin._retryLog[osaname]=0
                indigo.activePlugin._errorMsg[osaname]=u''

    # return value without error
    if akeys is None:
        # return text if no keys
        osavalues = core.strutf8(osavalues[:-1])
    else:
        # return list of values
        osavalues = dict(zip(akeys,(osavalues[:-1]).split('||')))
        for thekey,thevalue in osavalues.iteritems():
            if thevalue in _valueConvertDict:
                thevalue = _valueConvertDict[thevalue]
            osavalues[thekey] = core.strutf8(thevalue)

    core.logger(traceRaw = u'returned from applescript: %s' % (osavalues),traceLog = u'returned from applescript %s' % (osaname))

    return osavalues
