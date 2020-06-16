#!/usr/bin/env python

'''
    This program is auto run on the pi in the following location:

       "sudo nano /home/pi/.config/lxsession/LXDE-pi/autostart"
'''


import datetime, time, ast, sys, os
import serial, struct

from threading import Thread
from subprocess import call, check_output
import numpy as np

# operate on py2/3 and computer or pi
try:
    import tkinter as tk                # python 3
    from tkinter import font  as tkfont # python 3
    from tkinter import ttk
    from tkinter import filedialog
except:
    import ttk
    import Tkinter as tk     # python 2
    import tkFont as tkfont  # python 2
    import tkFileDialog as filedialog

try:
    import Adafruit_DHT
    import RPi.GPIO as GPIO
except ImportError:
    pass

# this class will hold all infortmaiton based on the frame,
# it has been setup to allow more than one frame to be added
# with slight modifications.
class BrewZilla(tk.Tk):
    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)
        self.title("BrewZilla v1.0")
        self.attributes('-fullscreen', True)
        self.geometry("800x480")
        self.resizable(width=False, height=False)
        self.config(bg="white")
        self.lift()

        self.title_font = tkfont.Font(size=22, weight="bold")
        self.list_font = tkfont.Font(size=12, weight="bold")
        self.large_font = tkfont.Font(size=36, weight="bold")
        self.msg_font = tkfont.Font(size=14)

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        frame = Monitor(parent=container, controller=self)
        frame.grid(row=0, column=0, sticky="nsew")



# this frame is the GUI and will be seen when the program runs
class Monitor(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.file_address = ''
        self.count = self.complete_flag = self.set_timer=self.btn_press_timer=self.toggle=0
        self.start_timer = self.set_temp = self.pause_timer =self.bzr = self.step_count = 0
        self.recipe = {}
        self.lock = False
        self.auto_flag = 1
        self.temp = 0

        self.notes_label_text = tk.StringVar()
        self.timer_label_text = tk.StringVar()
        self.temp_label_text = tk.StringVar()
        self.notes_msg_text = tk.StringVar()
	self.a_temp_label_text = tk.StringVar()
	self.a_temp_label_text.set("0c")
        self.notes_label_text.set("Welcome")
        self.timer_label_text.set("0:00:00")
        self.temp_label_text.set("0c")
        self.notes_msg_text.set("The brew steps will appear here, after a recipe is loaded please, be sure to upload an xml file")


        # decode XML keys
        self.match_internal = ['<NAME>','<BOIL_TIME>','<OG>','<AMOUNT>','<USE>','<TIME>','<TYPE>','<PRODUCT_ID>',\
                               '<SPARGE_TEMP>','<STEP_TIME>','<STEP_TEMP>','<INFUSE_AMOUNT>','<INFUSE_TEMP>',\
                               '<BOIL_SIZE>', '<BATCH_SIZE>' , '<DESCRIPTION>', '<DISPLAY_TIME>']

        self.match_external = ['<RECIPE>','<HOP>','<FERMENTABLE>','<MASH>','<MISC>','<YEAST>','<MASH_STEP>']

        self.match_string   = ['<NAME>','<TYPE>','<USE>','<DESCRIPTION>']

        #  GUI layout setup
        #  labels
        self.timer_label = tk.Label(self, textvariable=self.timer_label_text, font=controller.title_font)
        self.timer_label.place(x=60,y=80)
        self.temp_label = tk.Label(self, textvariable=self.temp_label_text, font=controller.title_font)
        self.temp_label.place(x=100,y=150)
	self.atemp_label = tk.Label(self, textvariable=self.a_temp_label_text, font=controller.title_font)
        self.atemp_label.place(x=100,y=190)
        self.notes_label = tk.Label(self, textvariable=self.notes_label_text, font=controller.large_font)
        self.notes_label.place(x=400, y=50, width=800, height=50, anchor='center')
        self.notes_msg = tk.Label(self, textvariable=self.notes_msg_text, font=controller.msg_font, wrap=370, anchor='e', justify='left')
        self.notes_msg.place(x=240,y=120)

        time_btn_label = tk.Label(self, text="Temp", font=controller.msg_font)
        time_btn_label.place(x=95,y=255)
        temp_btn_label = tk.Label(self, text="Time", font=controller.msg_font)
        temp_btn_label.place(x=95,y=325)

        self.comms_label = tk.Label(self,text="COM OK" ,fg='red' ,font=controller.msg_font)
        self.comms_label.place(x=80,y=440)

        #  Buttons
        quit_btn = ttk.Button(self, text="     Quit     ",command=lambda: self.quit())
        quit_btn.place(x=650, y=400)
        self.browse_btn = ttk.Button(self, text="Load Recipe",command=lambda: self.get_file_address())
        self.browse_btn.place(x=650, y=350)
        self.complete_btn = ttk.Button(self, text="Step Complete", state='disabled',command=lambda: self.complete())
        self.complete_btn.place(x=650, y=300)
        temp_p_btn = ttk.Button(self, text="    +    " , command=lambda: self.pos_temp())
        temp_p_btn.place(x=30, y=280)
        temp_n_btn = ttk.Button(self, text="    -    " ,command=lambda: self.neg_temp())
        temp_n_btn.place(x=130, y=280)
        time_p_btn = ttk.Button(self, text="    +    " ,command=lambda: self.pos_timer())
        time_p_btn.place(x=30, y=350)
        time_n_btn = ttk.Button(self, text="    -    " ,command=lambda: self.neg_timer())
        time_n_btn.place(x=130, y=350)
        self.auto_man_btn = ttk.Button(self, text="Manuel", width=8, command=lambda: self.auto_man())
        self.auto_man_btn.place(x=80, y=400)

        # start loops
        self.update_timer()
        self.init_serial()
        self.read_data()


    def get_file_address(self):
        rep = filedialog.askopenfilenames(parent=self.controller,
            initialdir='/home/pi/BrewZilla/Recipes',
            filetypes=[("XML", "*.xml")])
        self.file_address = rep
        time.sleep(0.1)
        self.xml_to_dict()

    def quit(self):
    	self.controller.destroy()

    def complete(self):
        self.complete_flag = 1

    def init_serial(self):
        try:
            self.ser = serial.Serial("/dev/ARDUINO", 9600)
            self.ser.reset_input_buffer()
            self.heartbeat()

        except serial.SerialException:
            print("Unexpected error:", sys.exc_info())

    def send_data(self, temp=0, bzr=0):
        string = []
        string.append('x')
        inputVals = [int(temp),int(bzr)]
        for num in inputVals:
            string.append(struct.pack('>B', num))
        string.append('y')

        try:
            for packet in string:
                self.ser.write(packet)
		#print(string)
        except:
            self.ser.close()
            self.init_serial()

    def read_data(self):
        
        try:
	    self.ser.flushInput()
            data = self.ser.readline()
            data = data.split("\r\n")[0].split(",")
            if(data[0] == 'z'):
                self.temp = int(data[1])
		a_temp = int(data[2])

            if(self.button_active()):
                self.temp_label_text.set(str(self.set_temp)+'c')
            else:
                self.temp_label_text.set(str(self.temp)+'c')
	    
	    self.a_temp_label_text.set(str(a_temp)+'c')
		
            
        except:
            print "Error readding coms", sys.exc_info()

        self.after(250, self.read_data)


    def button_active(self):
        if(time.time() > self.btn_press_timer + 3):
            return False
        else:
            return True

    def heartbeat(self):
        try:
            string = ['x','h','b','t','y']
            for packet in string:
                self.ser.write(packet)

            self.comms_label.config(fg="green")
        except:
            self.comms_label.config(fg="red")
            self.ser.close()
            self.init_serial()

        self.after(2000, self.heartbeat)

    def get_sparge_volume(self):
        count = 0
        total_grains = 0
        while 1:
            try:
                if self.recipe['<FERMENTABLE>'+str(count),'<TYPE>'] == "Grain":
                    total_grains += self.recipe['<FERMENTABLE>'+str(count),"<AMOUNT>"]
                count += 1
            except:
                break

        return round(self.recipe['<RECIPE>0', '<BOIL_SIZE>'] - (self.recipe['<MASH_STEP>0', '<INFUSE_AMOUNT>']  - total_grains),2)

    def update_timer(self):

        if self.start_timer >0:
            if not self.pause_timer:
                self.timer = round(time.time() - self.start_timer)
                self.timer_lab = datetime.timedelta(seconds=self.timer)
                self.timer_label_text.set(str(self.timer_lab))
        elif self.auto_flag:
            self.timer_label_text.set("0:00:00")
            self.timer = 0
        else:
            if not self.toggle:
                self.timer_lab = datetime.timedelta(seconds=self.set_timer)
                self.timer_label_text.set(str(self.timer_lab))
            else:
                self.timer_label_text.set("0:00:00")
                self.timer = 0

        self.after(250, self.update_timer)

    def pos_temp(self):
        self.set_temp+= 10
        self.btn_press_timer = time.time()

    def neg_temp(self):
        self.set_temp-= 10
        self.btn_press_timer = time.time()

    def pos_timer(self):
        self.set_timer+= 1
        self.btn_press_timer = time.time()

    def neg_timer(self):
        self.set_timer-= 1
        self.btn_press_timer = time.time()

    def auto_man(self):
        self.auto_flag = ~self.auto_flag&1
        self.start_timer = 0
        if(not self.auto_flag):
            self.complete_btn.config(text="Play")
            self.complete_btn.config(state='normal')
            self.auto_man_btn.config(text="Auto")
            self.notes_label_text.set("Manual Mode")
            self.notes_msg_text.set('Set timer and temp, the timer will start once temp is reached')
            self.set_temp = 0
            self.set_timer = 0
            self.manual()
        else:
            self.complete_btn.config(text="Step Complete")
            self.auto_man_btn.config(text="Manual")
            self.complete_btn.config(state='disabled')
            self.count=0;

    def wait_for_temp(self, temp=0):
        if (self.temp == temp):
            return True
        return False

    def get_boil_additions(self):
        string = ''
        while 1:
            try:
                a = self.recipe['<HOP>'+str(self.step_count),'<NAME>']
                a_size = len(a)
                b =str(self.recipe['<HOP>'+str(self.step_count),'<AMOUNT>']*1000.0)
                c = 'g'+u'\u2000'+str(round(self.recipe['<HOP>'+str(self.step_count),'<TIME>']))+'mins'
                x =''
                rng = 20 - a_size
                for i in range(rng):
                    x +=u'\u2000'
                string += a+x+b+c+"\n"
                self.step_count += 1

            except KeyError:
                self.step_count = 0
                break

        while 1:
            try:
                if self.recipe['<FERMENTABLE>'+str(self.step_count),'<TYPE>'] == "Sugar":
                    a = self.recipe['<FERMENTABLE>'+str(self.step_count),'<NAME>']
                    a_size = len(a)
                    b = str(int(round(self.recipe['<FERMENTABLE>'+str(self.step_count),'<AMOUNT>'],3)*1000))
                    c = 'g'+u'\u2000'+'10.0mins'
                    x =''
                    rng = 20 - a_size
                    for i in range(rng):
                        x +=u'\u2000'

                    string += a+x+b+c+"\n"
                self.step_count += 1
            except KeyError:
                self.step_count = 0
                break

        while 1:
            try:
                a = self.recipe['<MISC>'+str(self.step_count),'<NAME>']
                a_size = len(a)
                b = str(round(self.recipe['<MISC>'+str(self.step_count),'<AMOUNT>'],3)*1000)
                c = 'g'+u'\u2000'+str(self.recipe['<MISC>'+str(self.step_count),'<TIME>'])+'mins'
                x =''
                rng = 20 - a_size
                for i in range(rng):
                    x +=u'\u2000'

                string += a+x+b+c+"\n"
                self.step_count += 1
            except KeyError:
                self.step_count = 0
                break

        return string

    def manual(self):
        # Manual Mode
        if(not self.auto_flag):

            if (self.complete_flag):
                self.complete_flag = False
                self.toggle = ~self.toggle&1

                if (self.toggle):
                    self.complete_btn.config(text="Pause")
                    self.notes_msg_text.set('Heating to '+str(self.set_temp)+'c please wait...')
                    self.send_data(self.set_temp, 6)
                    if self.pause_timer > 0:
                        self.start_timer += (time.time() - self.pause_timer)
                        self.pause_timer = 0
                else:
                    self.complete_btn.config(text="Play")
                    self.notes_msg_text.set('Paused')
                    self.send_data(0, 6)
                    if self.start_timer > 0:
                        self.pause_timer = time.time()

            if self.toggle:
                if self.wait_for_temp(self.set_temp):
                    self.send_data(self.set_temp, 5)
                    self.notes_msg_text.set('Temp reached timer has started...')
                    if (not self.lock):
                        self.lock = True
                        self.start_timer = time.time()

            if (self.timer == self.set_timer*60):
                if (self.lock):
                    self.lock = False
                    self.send_data(0, 5)
                    self.start_timer = self.timer=0
                    self.complete_btn.config(text="Play")
                    self.notes_msg_text.set('Finsihed...')
                    self.toggle = ~self.toggle&1
        else:
            return


        self.after(250, self.manual)

    def state_machine(self):
        #try:

        # add water and heat
        if (self.count == 0):

            self.notes_label_text.set("Water")
            self.notes_msg_text.set('Add '+str(self.recipe['<MASH_STEP>0','<INFUSE_AMOUNT>'])+'L of water, once added turn on the elements and press, Step Compelete')
            if(self.complete_flag):
                self.complete_btn.config(state='disabled')
                self.lock = False
                self.complete_flag = False
                self.recipe['<MASH_STEP>0','<INFUSE_TEMP>'] = round(float(self.recipe['<MASH_STEP>0','<INFUSE_TEMP>'][0].split(' ')[0]))
                self.notes_msg_text.set("The water will begin heating, wait for it to reach, infustion temp - "+str(self.recipe['<MASH_STEP>0','<INFUSE_TEMP>']))
                self.send_data(round(self.recipe['<MASH_STEP>0','<INFUSE_TEMP>']), 6)
                self.count = 1

        # Wait for water to heat
        elif(self.count == 1):
            if(self.wait_for_temp(round(self.recipe['<MASH_STEP>0','<INFUSE_TEMP>']))):
                self.send_data(self.recipe['<MASH_STEP>0','<STEP_TEMP>'],4)
                self.count = 2
                self.complete_btn.config(state='normal')

        # add grains
        elif(self.count == 2):
            self.notes_label_text.set("Add Grain")
            self.notes_msg_text.set("Please add the grain, once it's mixed press, Step Complete")
            if(self.complete_flag):
                self.complete_btn.config(state='disabled')
                self.browse_btn.config(state='disabled')
                self.complete_flag = False
                self.start_timer = time.time()
                self.count = 3

        # mash
        elif(self.count == 3):
            self.notes_label_text.set("Mash In")
            try:
                self.notes_msg_text.set('Mash duration is '+str(self.recipe['<MASH_STEP>'+str(self.step_count), '<STEP_TIME>']))
                if( self.recipe['<MASH_STEP>'+str(self.step_count), '<STEP_TIME>'] * 60 <= self.timer):
                    self.start_timer = 0
                    self.send_data(self.recipe['<MASH_STEP>'+str(self.step_count), '<STEP_TEMP>'],4)
                    self.step_count += 1
                    # test the count level
                    self.recipe['<MASH_STEP>'+str(self.step_count),'<STEP_TIME>']
                    self.start_timer = time.time()
            except KeyError:
                self.count = 4
                self.step_count = 0
                self.start_timer = 0
                self.complete_btn.config(state='enabled')

        # sparge
        elif(self.count == 4):
            self.notes_label_text.set('Sparge')
            self.notes_msg_text.set('Add '+str(self.get_sparge_volume())+'L press, Step Complete when the sparge is finished')
            if(self.complete_flag):
                self.notes_msg_text.set('Waiting to boil, make sure you put the lid on, remember to turn off the recir pump before boil')
                self.complete_btn.config(state='disabled')
                self.complete_flag = False
                self.send_data(temp=110, bzr=5)
                self.count = 5
                self.lock = True

        # boil
        elif (self.count == 5):
            self.notes_label_text.set('Boil')
            if(self.wait_for_temp(100)):
                self.notes_msg_text.set(self.get_boil_additions())
                if(self.lock):
                    self.lock = False
                    self.start_timer = time.time()

            if(self.recipe['<RECIPE>0', '<BOIL_TIME>'] * 60 <= self.timer):
                self.notes_label_text.set('Boil Finished')
                self.start_timer = 0
                self.count = 6
    		self.send_data(0,4)
        self.after(250, self.state_machine)

    def xml_to_dict(self):
        '''
        Recipe
            Name
        Mash
            Mash Volume
            Mash temp/s
            Mash time/s
            post mash SG
        Sparge
            Volume
            Temp
        Boil
            boil time
            boil temp
            post boil SG
            boil volume
        Hops
            hop name/s
            boil time/s
            amount
        chill
            OG
            fermentation temp
            FG
        '''

        # define variables
        hop_count = mash_step = match = ext_count = 0
        recipe = {}
        str1 = str2 = last_str1 = ''

        # open file from browser
        try:
            file = open(self.file_address[0])
        except:
            pass
        try:
            # loop over each line
            for line in file.readlines():

                # Check for an external match:
                for ext_name in self.match_external:

                    # if found load name into memory
                    if ext_name in line:
                        last_str1 = str1
                        str1 = ext_name
                        if str1 == last_str1:
                            match = True
                        else:
                            match = False
                            ext_count = 0
                        break

                # Check for an internal match:
                for int_name in self.match_internal:

                    # if found load name into memory
                    if int_name in line:
                        str2 = int_name
                        if (int_name == self.match_internal[0]) and match:
                            ext_count =  ext_count + 1
                        break


                # if both strings have data do something (print).
                if str1 and str2:

                    #print("OUT: ",str1+str(ext_count), str2)
                    # get string data
                    data = line.split(">")
                    data = data[1].split("<")

                    if str2 not in self.match_string:
                        # print(str1)
                        try:
                            data = float(data[0])
                        except ValueError:
                            pass
                    else:
                        data = data[0]

                    # Save to dictonary
                    recipe[str1+str(ext_count),str2] = data

                    # reset the seoond string as this is the 2nd loop
                    # ie a higher freq of changes.
                    str2 = ''

            self.recipe = recipe
            self.complete_btn.config(state='normal')
            self.state_machine()

        except UnboundLocalError:
            pass



    def clock_tick(self):
        if self.clock.cget("text") != time.strftime('%H:%M:%S'):
            self.clock.config(text=time.strftime('%H:%M:%S'))

        self.after(200, self.clock_tick)


if __name__ == "__main__":

    app = BrewZilla()
    app.mainloop()
