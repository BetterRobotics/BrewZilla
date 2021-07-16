BrewZilla Control
==================
The ultimate controller for your BrewZilla 3.0; 3.1; 3.1.1; 

It takes a recipe exported from your favorite beer brewing program and automatically, sets up the steps using a prompt to guide you along the way. Just export you favorite recipe in XML to a USB plug it into the device and hit "Load Recipe" and open the xml file. You can remove the USB or leave it once this is done. 

If you want to send the recipe wirelessly I suggest placingit in ~/BrewZilla/Recipe to as this is the defaut browse location. The wireless option is 

```scp 'file location' pi@"ip address":~/BrewZilla/```





The program's main features
----------------------------
- Manual mode timer: which activates after the set temperature is reached
- Auto mode: reads the XML recipe file and prompts for needed interactions no programming needed
- Buzzer to alert the brewer attention is required
- Auto/Manual functionality to allow you to take control for any reason
- PID temperature control
- Communication loss detection
- Uses all existing hardware that comes with the brewzilla 3 with the addition of PI and Arduino

<b># NOTE:</b> This code is only running on python2.7 at this stage, it will be ported to python 3 when necessary.





Installation Steps
----------------------------

first install git.
```
sudo apt-get install git -y 
```

Get the Repo
```
cd ~/
```

```
git clone https://github.com/BetterRobotics/BrewZilla.git
```

Go to the BrewZilla directory.
```
cd BrewZilla
```
Set application actions
```
chmod +x install.sh
```
Setup environment
```
./install.sh
```

Auto reboot will kick in and you should have your program running after the loading screen. 
Arduino pics for wiring will come shortly or check the brewzilla.ino file for info input / output pins.







65L Setup
----------------------------

If your using a 65L model you will need to change the type setting in the brewzilla.ino file to:

"#define MODEL 0" 

then run 

`cd ~/BrewZilla && make clean upload`







Trouble shooting
----------------------------

After installation has finished check you can access the arduino via USB:

```ls -l /dev/ARDUINO```  

This will show something like ```lrwxrwxrwx 1 root root 7 Jun  9 18:48 /dev/ARDUINO -> ttyUSB0``` if the install was sucessful. If not you will need to make a udev rule as you may have an genuine nano and I don't think they use the "ch341" chip for USB comms so the rule will need to be modified to suit see "/etc/udev/rules.d/99-arduino.rules" for more info.

Next you will need to check the upload of the .ino script to the arudino nano328, this can be done by typing.

```cd ~/BrewZilla && make clean upload```

Once done and wiring is correct you will have an automatic Brewzilla with wireless connectivity.


