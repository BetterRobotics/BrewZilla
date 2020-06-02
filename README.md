BrewZilla 3.0+
===============
The ultimate controller for your BrewZilla 3.0+ it takes a recipe exported from your favorite beer brewing program and automatically sets the steps up with a prompt to guide you along the way. Just export you favorite recipe in XML, run the  program using from the directory with the program, ```python brewzilla.py``` remember to upload and connect the arduino using the udev rule specified below. 


<b># NOTE:</b> This code has only been tested in a simulated environment!!! Please only use this if you are experienced in electronics/coding, also this code is only running on python2.7 at this stage.

I will be releasing a full version ready to run with all components needed after my testing is completed. 

Dependancies are required:

```bash
sudo apt-get install python-tk

sudo apt-get install python-numpy
```
Also need to write a udev rule to name the Arduino device:

```bash
sudo nano /etc/udev/rules.d/99-arduino.rules
```
Add 
```bash 
SUBSYSTEMS=="usb", DRIVERS=="ch341", MODE=="0666", GROUP=="dialout", SYMLINK+="ARDUINO"

```
