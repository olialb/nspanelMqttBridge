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
echo "Create virtual environment"
echo "#########################################"
python3 -m venv venv
source venv/bin/activate

echo "#########################################"
echo "Install the required python packages..."
echo "#########################################"
echo ""
pip install paho-mqtt
pip install pyyaml
pip install webcolors
pip install requests
pip install watchdog
#pip install -U pytest
#pip install pylint

#echo "#########################################"
#echo "Fill templates"
#echo "#########################################"
#echo ""

echo "################################################"
echo "Install systemd serice..."
echo "service name: nsPanelMqttBridge"
eval "echo \"user        : $USER\""
echo "################################################"
echo ""
chmod +x nsPanelMqttBridge
eval "echo \"$(cat nsPanelMqttBridge.service.template)\"" >nsPanelMqttBridge.service
sudo mv nsPanelMqttBridge.service /lib/systemd/system/nsPanelMqttBridge.service
sudo chmod 644 /lib/systemd/system/nsPanelMqttBridge.service
sudo systemctl daemon-reload
#sudo systemctl enable nsPanelMqttBridge
#sudo systemctl status nsPanelMqttBridge

echo "################################################"
echo "Enable the service with:"
echo "sudo systemctl enable nsPanelMqttBridge"
echo ""
echo "Start the service with:"
echo "sudo systemctl start nsPanelMqttBridge"
echo ""
echo "Stop the service with:"
echo "sudo systemctl stop nsPanelMqttBridge"
echo ""
echo "Restart the service after any config change with:"
echo "sudo systemctl restart nsPanelMqttBridge"
echo "################################################"
trap - 0
