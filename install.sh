#!/bin/bash

clear

echo "

BrewZilla Installing......"

echo "


Updating System"
sudo apt-get update && sudo apt-get upgrade -y

echo "


Installing needed packages"
sudo apt-get install python-tk python-numpy arduino-core arduino-mk -y
pip install pyserial

echo "


Setting up VNC with password please enter what you would like to use when promted.
Use the Pi's IP address to connect or hostname.local"

sudo systemctl enable vncserver-x11-serviced 
sudo vncpasswd -service
sudo cp common.custom /etc/vnc/config.d/  "Authentication=VncAuth"

echo "


Setting up autorun..."

sudo cp autostart /etc/xdg/lxsession/LXDE-pi/

echo "


Setting up arduino..."
sudo cp 99-arduino.rules /etc/udev/rules.d/
sudo udevadm trigger
sleep 1

echo "


Flashing Arduino..."
cd ~/BrewZilla && make clean upload

echo "


Done! Rebooting 5 seconds"

sleep 5
sudo reboot



