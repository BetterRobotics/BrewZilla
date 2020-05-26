#!/usr/bin/env python

import datetime, time, ast, sys, os

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
        # self.attributes('-fullscreen', True)
        self.geometry("800x480")
        self.resizable(width=False, height=False)
        self.config(bg="white")
        self.lift()

        self.title_font = tkfont.Font(family='Helvetica', size=22, weight="bold", slant="italic")
        self.list_font = tkfont.Font(family='Helvetica', size=12, weight="bold", slant="italic")
        self.large_font = tkfont.Font(family='Helvetica', size=36, weight="bold", slant="italic")
        self.msg_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)


        frame = Monitor(parent=container, controller=self)
        frame.grid(row=0, column=0, sticky="nsew")


    def second(self):
        return int(time.time())

    def hour(self):
        return int(datetime.datetime.now().strftime("%H"))

# this frame is the GUI and will be seen when the program runs
class Monitor(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.file_address = ''
        self.count = self.step_temp = self.complete_flag = self.start_timer = self.temp = self.step_count = 0
        self.recipe = {}

        #for now this is a pretend setup for pi 
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(17, GPIO.OUT)
            GPIO.setup(27, GPIO.OUT)
        except:
            pass

        self.notes_label_text = "Welcome"
        self.timer_label_text = "00:00:00"
        self.temp_label_text =  "??"
        self.notes_msg_text  =  "The brew steps will appear here, after a recipe is loaded please, be sure to upload an xml file"

        self.match_internal = ['<NAME>','<BOIL_TIME>','<OG>','<AMOUNT>','<USE>','<TIME>','<TYPE>','<PRODUCT_ID>',\
                               '<SPARGE_TEMP>','<STEP_TIME>','<STEP_TEMP>','<INFUSE_AMOUNT>','<INFUSE_TEMP>',\
                               '<BOIL_SIZE>', '<BATCH_SIZE>' , '<DESCRIPTION>', '<DISPLAY_TIME>']

        self.match_external = ['<RECIPE>','<HOP>','<FERMENTABLE>','<MASH>','<MISC>','<YEAST>','<MASH_STEP>']

        self.match_string   = ['<NAME>','<TYPE>','<USE>','<DESCRIPTION>']

        #  GUI layout setup
        #  labels
        # monitor_label = tk.Label(self, text="BrewZilla", font=controller.large_font)
        # monitor_label.place(x=80, y=20)
        time_btn_label = tk.Label(self, text="Temp", font=controller.msg_font)
        time_btn_label.place(x=95,y=255)
        temp_btn_label = tk.Label(self, text="Time", font=controller.msg_font)
        temp_btn_label.place(x=95,y=325)

        self.timer_label = tk.Label(self, text=self.timer_label_text, font=controller.large_font, width=8)
        self.timer_label.place(x=40,y=80)
        self.temp_label = tk.Label(self, text=self.temp_label_text+u"\u2103", font=controller.large_font)
        self.temp_label.place(x=85,y=150)
        self.notes_label = tk.Label(self, text=self.notes_label_text, font=controller.large_font, anchor='c')
        self.notes_label.place(x=320,y=40)
        self.notes_msg = tk.Message(self, text=self.notes_msg_text,font=controller.msg_font, width=370)
        self.notes_msg.place(x=240,y=120)

        #  Buttons
        quit_btn = ttk.Button(self, text="     Quit     ",command=lambda: self.quit())
        quit_btn.place(x=650, y=400)
        browse_btn = ttk.Button(self, text="Load Recipe",command=lambda: self.get_file_address())
        browse_btn.place(x=650, y=350)
        self.complete_btn = ttk.Button(self, text="Step Complete", state='disabled',command=lambda: self.complete())
        self.complete_btn.place(x=650, y=300)
        temp_p_btn = ttk.Button(self, text="    +    " , command=lambda: self.pos_temp())
        temp_p_btn.place(x=30, y=280)
        temp_n_btn = ttk.Button(self, text="    -    " ,command=lambda: self.neg_temp())
        temp_n_btn.place(x=130, y=280)
        time_p_btn = ttk.Button(self, text="    +    " ,command=lambda: self.quit())
        time_p_btn.place(x=30, y=350)
        time_n_btn = ttk.Button(self, text="    -    " ,command=lambda: self.quit())
        time_n_btn.place(x=130, y=350)
        auto_man_btn = ttk.Button(self, text="Auto/Man" ,command=lambda: self.quit())
        auto_man_btn.place(x=80, y=400)

        self.update_labels()

    def get_file_address(self):
        rep = filedialog.askopenfilenames(
            parent=self.controller,
            initialdir='',
            filetypes=[("XML", "*.xml")])
        self.file_address = rep
        time.sleep(0.1)
        self.xml_to_dict()

    def quit(self):
    	self.controller.destroy()

    def complete(self):
        self.complete_flag = 1

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

        # print("Need to add", np.round(self.sparge_volume,2), "L for sparge")

    def update_labels(self):
        
        if self.start_timer is not 0:
             self.timer = round(time.time() - self.start_timer)
             self.timer_label_text = str(self.timer)
        else:
            self.timer_label_text = 0
            self.timer = 0
        
        self.timer_label.config(text=self.timer_label_text)

        self.temp_label.config(text=self.temp_label_text+u"\u2103")

        self.notes_label.config(text=self.notes_label_text)

        self.notes_msg.config(text=self.notes_msg_text)

        self.after(200, self.update_labels)

    def pos_temp(self):
        self.temp+= 1

    def neg_temp(self):
        self.temp-= 1

    def read_temp(self):
        return self.temp

    def turn_on_heaters(self, temp=0):
        return 0

    def wait_for_temp(self, set_temp=0): 
        temp = self.read_temp() 
        self.temp_label_text = str(temp)
        if (temp == set_temp):
            return True
        self.after(1000, self.wait_for_temp)

    def get_boil_additions(self):
        string = ''
        while 1:
            try:
                string += self.recipe['<HOP>'+str(self.step_count),'<NAME>']+'\tAmount: '+str(self.recipe['<HOP>'+str(self.step_count),'<AMOUNT>'])+'\tTime: '+str(self.recipe['<HOP>'+str(self.step_count),'<TIME>'])+'\n'
                self.step_count += 1
            except KeyError:
                self.step_count = 0
                break

        while 1:
            try:
                if self.recipe['<FERMENTABLE>'+str(self.step_count),'<TYPE>'] == "Sugar":
                    string += self.recipe['<FERMENTABLE>'+str(self.step_count),'<NAME>']+'\tAmount: '+str(self.recipe['<FERMENTABLE>'+str(self.step_count),'<AMOUNT>'])+'\tTime: 10\n'
                self.step_count += 1
            except KeyError:
                self.step_count = 0
                break

        while 1:
            try:
                string += self.recipe['<MISC>'+str(self.step_count),'<NAME>']+'\tAmount: '+str(self.recipe['<MISC>'+str(self.step_count),'<AMOUNT>'])+'\tTime: '+str(self.recipe['<MISC>'+str(self.step_count),'<TIME>'])+'\n'
                self.step_count += 1
            except KeyError:
                self.step_count = 0
                break

        return string

    def state_machine(self):
        # self.count = 0
        # add water and heat
        if (self.count == 0):
            self.notes_label_text = "Water"
            self.notes_msg_text = 'Add '+str(self.recipe['<MASH_STEP>0','<INFUSE_AMOUNT>'])+'L of water, once added turn on the elements and press, Step Compelete'
            if(self.complete_flag):
                self.complete_flag = False
                self.notes_msg_text = "The water is heating, wait for it to reach, the required infustion temp"
                self.turn_on_heaters(5) # self.recipe['<MASH_STEP>0','<INFUSE_TEMP>']
                self.count = 1
        
        # Wait for water to heat
        elif(self.count == 1):  
                if(self.wait_for_temp(5)): # self.recipe['<MASH_STEP>0','<INFUSE_TEMP>']
                    self.turn_on_heaters(4) # self.recipe['<MASH_STEP>0','<STEP_TEMP>']
                    self.count = 2 
        # add grains
        elif(self.count == 2):
            self.notes_label_text = "Add Grain"
            self.notes_msg_text = "Please add the grain, once it's mixed press, Step Complete"
            if(self.complete_flag):
                self.complete_flag = False
                self.start_timer = time.time()
                self.count = 3

        # mash 
        elif(self.count == 3):
            self.notes_label_text = 'Mash In'
            try:
                self.notes_msg_text = 'Mash Finished in '+str(self.recipe['<MASH_STEP>'+str(self.step_count), '<STEP_TIME>'])
                if( 10 <= self.timer ): # self.recipe['<MASH_STEP>'+str(self.step_count), '<STEP_TIME>']
                    self.start_timer = 0
                    self.turn_on_heaters(3) # self.recipe['<MASH_STEP>'+str(self.step_count), '<STEP_TEMP>']
                    self.step_count += 1
                    # test the count level
                    self.recipe['<MASH_STEP>'+str(self.step_count),'<STEP_TIME>']
                    self.start_timer = time.time()
            except KeyError:
                self.count = 4
                self.step_count = 0
                self.start_timer = 0

        # sparge
        elif(self.count == 4):
            self.notes_label_text = 'Sparge'
            self.notes_msg_text = 'Add '+str(self.get_sparge_volume())+'L press, Step Complete when the sparge is finished'
            if(self.complete_flag):
                self.notes_msg_text = 'Waiting to boil, make sure you put the lid on, remember to turn off the recir pump before boil'
                # self.complete_flag = False
                self.turn_on_heaters(7)
                self.count = 5

        # boil
        elif (self.count == 5):
            self.notes_label_text = 'Boil'
            if(self.wait_for_temp(7)):
                self.notes_msg_text = self.get_boil_additions()
                if(self.complete_flag):
                    self.complete_flag = False
                    self.start_timer = time.time()
               
            if(20 <= self.timer):
                self.notes_label_text = 'Boil Finished'
                self.start_timer = 0
                self.count = 6
            
        
        self.update_labels()
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
                # print (line)

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
            for line in recipe:
                print(line)

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


