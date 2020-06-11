BrewZilla Control 
==================
The ultimate controller for your BrewZilla 3.0; 3.1; 3.1.1; it takes a recipe exported from your favorite beer brewing program and automatically, sets up the steps using a prompt to guide you along the way. Just export you favorite recipe in XML (I use beersmith 2), run the program from the directory, ```python brewzilla.py``` remember to upload and connect the arduino and setup the udev rule specified below. 

The program's main features
----------------------------
- Manual mode timer: which activates after the set temperature is reached
- Auto mode: reads the XML recipe file and prompts for needed interactions no programming needed
- Buzzer to alert the brewer attention is required
- Auto/Manual functionality to allow you to take control for any reason
- PID temperature control
- Communication loss detection
- Uses all existing hardware that comes with the brewzilla 3 with the addition of PI and Arduino



<b># NOTE:</b> This code has only been tested in a simulated environment!!! Please only use this if you are experienced in electronics/coding, also this code is only running on python2.7 at this stage.

I will be releasing a full version ready to run with all components needed after my testing is completed. 

first install git.
```
sudo apt-get install git -y 
```

Get the Repo
```
cd ~/
```

```
git clone repo
```

Go to the BrewZilla directory.
```
cd BrewZilla
```
Set applicaiton actions
```
chmod +x install.sh
```
Setup environment
```
./install.sh
```

Auto reboot will kick in and you should have your program running after the loading screen. 

arduino pics for wiring will come shortly. 


