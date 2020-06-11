#!/bin/bash

echo "BrewZilla Installing now......"


echo "


UPDATING SYSTEM"
sudo apt-get update && sudo apt-get upgrade -y

echo "


Installing needed packages"
sudo apt-get install python-tk python-numpy arduino-core arduino-mk -y
pip install pyserial


echo "


Setting up devices"
sudo bash -c 'echo "SUBSYSTEMS=="usb", DRIVERS=="ch341", MODE=="0666", GROUP=="dialout", SYMLINK+="ARDUINO"" > /etc/udev/rules.d/99-arduino.rules'

echo "


Setting up autorun..."
echo '@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash

@python /home/pi/BrewZilla/brewzilla.py' > /home/pi/.config/lxsession/LXDE-pi/autostart

echo "


Flashing ARDUINO..."
cd ~/BrewZilla && make clean upload

echo "


Done!. auto reboot will kick in if not reboot now."


sudo reboot



