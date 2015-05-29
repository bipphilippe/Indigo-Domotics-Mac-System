__author__ = 'bip-philippe'
__version__ = '1.3.0'

#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################################################################################
""" Framework helpers for indigo plugins
    
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
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
    
    History
    =======
    Rev 1.0.0 : Initial version
    Rev 1.0.2 : Packaging for initial release
                Enhancements:
                 - add decode('utf-8') for output of error messages
    Rev 1.0.3 : Wait time version
                Enhancements:
                 - decrease CPU overhead by adding wait time
    Rev 1.1.0 : Enhanced version with more states
                Enhancements:
                 - Manages special states icons for devices :
                 - enhanced use of ps command to collect more information
                 - first version of the relaydimmer library
                 - new log management, less verbose
    Rev 1.2.0 : Special characters management
                Enhancements:
                 - shellscript logging
                Some bugs corrections, including:
                 - Error with special characters in shell command
    Rev 1.3.0 : Apple Scripting enhancements
                Enhancements:
                 - applescript library error filter
                 - matching between True/False states between applescript and python
                 - uniform way of encoding strings
                 - logging
    Rev 1.4.0 : Auto-add of missing device parameters
                Enhancements:
                 - Auto-add of missing device parameters and states when upgrading
                 - better respect of properties and states when starting/stopping devices
                 - new log of properties and states mechanism
                Some bugs corrections, including:
                 - applescript library error filter
"""
####################################################################################
