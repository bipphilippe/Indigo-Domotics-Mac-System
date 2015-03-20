###################################################################################
# Mac OS System plug-in
# By Bernard Philippe (bip.philippe) (C) 2015
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.#
#
####################################################################################

Indigo Automation Plug-in for managing disk volumes and applications running

This plug-in allows to declare as devices : disk volumes and applications.

For disk volumes :
- allows to mount/unmount volumes,
- has an option to force unmount,
- prevent sleeping (option) of volumes,

For Application :
- launch/quit application.
- as an option to force quit application

Typical use of this plugin is managing an iTunes instance as a media server, on the same mac than the Indigo server. 
The kind of scenarios I use are :
- Turn on the media service :
   - When the house wakes up, a trigger turns on the raid disk (using a reay device)
   - When the disk volume is mounted (i.e. disk volume device becomes on), a trigger launches iTunes by setting the Application device to On
   - Then you can use iTunes Plug-in or Airfoil plugin as usual
- Turn off the media service :
   - When the house goes to sleep, a trigger sets the application device to off to stop iTunes,
   - When iTunes device is off, a trigger unmount the disk volume (i.e. sets disk volume device to off),
   - When the disk volume is off, then the raid drive relay device is set off.
   
More on the indigo Forum : http://forums.indigodomo.com/viewtopic.php?f=162&t=13678
