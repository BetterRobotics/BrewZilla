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
    from tkinter import messagebox
    from tkinter import filedialog
except:
    import ttk
    import Tkinter as tk     # python 2
    import tkFont as tkfont  # python 2
    import tkMessageBox
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

        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        self.list_font = tkfont.Font(family='Helvetica', size=12, weight="bold", slant="italic")
        self.large_font = tkfont.Font(family='Helvetica', size=36, weight="bold", slant="italic")
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
        self.lock = 0

        #for now this is a pretend setup for pi 
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(17, GPIO.OUT)
            GPIO.setup(27, GPIO.OUT)
        except:
            pass
        

        #  GUI layout setup
        #  labels 
        monitor_label = tk.Label(self, text="BrewZilla", font=controller.title_font)
        monitor_label.place(x=350, y=20)
        self.timer_label = tk.Label(self, text="00:00:00", font=controller.large_font)
        self.timer_label.place(x=40,y=80)
        self.temp_label = tk.Label(self, text="??"+u"\u2103", font=controller.title_font)
        self.temp_label.place(x=85,y=150)
        self.time_btn_label = tk.Label(self, text="Time", font=controller.title_font)
        self.time_btn_label.place(x=95,y=255)
        self.temp_btn_label = tk.Label(self, text="Temp", font=controller.title_font)
        self.temp_btn_label.place(x=95,y=325)
        self.notes_label = tk.Label(self, text="The brew steps will appear here\nonce a recipe is loaded please be\nsure to upload a '*.xml' file",font=controller.title_font)
        self.notes_label.place(x=250,y=80)

        #  Buttons
        quit_btn = ttk.Button(self, text="   Quit   ",command=lambda: quit())
        quit_btn.place(x=650, y=400)
        browse_btn = ttk.Button(self, text="Browse",command=lambda: self.get_file_address())
        browse_btn.place(x=650, y=350)
        temp_p_btn = ttk.Button(self, text="    +    " , command=lambda: self.quit())
        temp_p_btn.place(x=30, y=280)
        temp_n_btn = ttk.Button(self, text="    -    " ,command=lambda: self.quit())
        temp_n_btn.place(x=130, y=280)
        time_p_btn = ttk.Button(self, text="    +    " ,command=lambda: self.quit())
        time_p_btn.place(x=30, y=350)
        time_n_btn = ttk.Button(self, text="    -    " ,command=lambda: self.quit())
        time_n_btn.place(x=130, y=350)
        auto_man_btn = ttk.Button(self, text="Auto/Man" ,command=lambda: self.quit())
        auto_man_btn.place(x=80, y=400)

    def get_file_address(self):
        rep = filedialog.askopenfilenames(
            parent=self.controller,
            initialdir='/',
            initialfile='tmp',
            filetypes=[
                ("XML", "*.xml")])
        self.file_address = rep
        time.sleep(0.1)
        self.decode_xml()

    def quit(self):
    	self.controller.destroy()

    def decode_xml(self):
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

        # setup matchs 
        match_internal = ['<NAME>','<BOIL_TIME>','<OG>','<AMOUNT>','<USE>','<TIME>','<TYPE>','<PRODUCT_ID>',\
                          '<SPARGE_TEMP>','<STEP_TIME>','<STEP_TEMP>','<INFUSE_AMOUNT>','<INFUSE_TEMP>',\
                          '<BOIL_SIZE>', '<BATCH_SIZE>', '<TRUB_CHILLER_LOSS>', '<COOLING_LOSS_PCT>' ]

        match_external = ['<RECIPE>','<HOP>','<MASH>','<MISC>','<YEAST>','<MASH_STEP>','<EQUIPMENT>']

        # define variables
        hop_count = mash_step = match = 0
        recipe = {}
        str1 = str2 = ''

        # open file from browser
        file = open(self.file_address[0])

        # loop over each line
        for line in file.readlines():

            # Check for an external match:
            for ext_name in match_external:

                # if found load name into memory
                if ext_name in line:
                    str1 = ext_name  

            # Check for an internal match:
            for int_name in match_internal:

                # if found load name into memory
                if int_name in line:
                    str2 = int_name 

            # if both strings have data do something (print). 
            if str1 and str2:
                print("OUT: ",str1, str2)

                # reset the seoond string as this is the 2nd loop 
                # ie a higher freq of changes.  
                str2 = ''

            # get string data
            line = line.split(">")
            line = line[0].split("<")

            # TODO - convert sting to data type needed
            #

            # Save to dictonary
            recipe[str1,str2] = line
        

    def clock(self):
        if self.clock.cget("text") != time.strftime('%H:%M:%S'):
            self.clock.config(text=time.strftime('%H:%M:%S'))

        self.after(200, self.clock_tick)




if __name__ == "__main__":

    app = BrewZilla()
    app.mainloop()


