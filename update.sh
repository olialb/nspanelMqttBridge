#!/bin/bash
#
# This file is part of the nspanelMqttBridge distribution (https://github.com/olialb/nspanelMqttBridge).
# Copyright (c) 2026 Oliver Albold.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
abort()
{
   echo "
###########################
Abort!!
###########################
An error occured Exiting..." >&2
   exit 1
}
trap 'abort' 0
#exit on error
set -e

echo "#########################################"
echo "Update nspanelMqttBridge"
echo "#########################################"
#stop systemd service
sudo systemctl stop nsPanelMqttBridge
#backup config in ini file
cp nspanelMqttBridge.ini nspanelMqttBridge.ini.backup
#get latest code from release branch
git fetch origin release
git reset --hard origin/release
#move configuration back
mv -f nspanelMqttBridge.ini.backup nspanelMqttBridge.ini
#start systemd service
sudo systemctl start nsPanelMqttBridge

echo "################################################"
echo "Done"
echo "################################################"
trap - 0
