###################################
####### PID DRONE INTERFACE #######
###################################
#https://colorate.azurewebsites.net/es/Color/303030

import os
import time 
import sqlite3
import threading
import numpy as np 
import pandas as pd  
import tkinter as tk
from panels import *
from menu import Menu
import customtkinter as ctk
from djitellopy import tello
from pandastable import Table
from aditional import UpFrame
from tkinter import messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from settings import *

class Window(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode('dark')
        self.geometry('1000x600')
        self.title('PID Drone Control')
        self.iconbitmap('.\\Resources\\drone-thin.ico')
        self.minsize(900, 560)
        self.maxsize(1000, 600)
        self.resizable(True, True)
        print(DEFAULT_SPEED)
        
        #Status battery
        self.battery_yellow = True
        self.battery_red = True

        #
        self.drone_variable = 'NONE'
        self.control_signal = 0

        #
        self.altitude = ALTITUDE
        self.integral = 0
        self.previous_error = 0
        self.data_time_variable = 0
        self.error = 0
        self.items = []
        self.wished_height = 10
        self.restart_graph = False
        self.control_signal = 0
        self.output = 0
        self.time = 0

        #   layout 
        self.rowconfigure(0, weight = 1, uniform = 'a')
        self.rowconfigure(1, weight = 7, uniform = 'a')
        self.rowconfigure(2, weight = 1, uniform = 'a')
        self.columnconfigure(0, weight = 2, uniform = 'a')
        self.columnconfigure(1, weight = 6, uniform = 'a')
        self.connect_button = DroneConnection(self, self.drone_connect)
        self.mainloop()

    def init_parameters(self):
        self.height_drone = {
            'proportional': ctk.DoubleVar(value = DEFAULT_PROPORTIONAL_VALUE_HEIGHT),
            'derivative': ctk.DoubleVar(value = DEFAULT_DERIVATIVE_VALUE_HEIGHT),
            'integral': ctk.DoubleVar(value = DEFAULT_INTEGRAL_VALUE_HEIGHT),
            'height': ctk.IntVar(value = DEFAULT_HEIGHT),
            'start': ctk.BooleanVar(value = False)
            }
        
        self.control_drone = {  
            'speed' :ctk.IntVar(value = DEFAULT_SPEED),
            'graph1': ctk.StringVar(value = OPTIONS_DRONE_GRAPH1[3]),
            'graph2':ctk.StringVar(value = OPTIONS_DRONE_GRAPH2[2]),
            'graph_state':ctk.StringVar(value = OPTIONS_DRONE_GRAPH_STATE[1])
        }
        
        self.progress = ctk.DoubleVar(value = PROGRESSDEFAULT)
        self.vcmd = (self.register(self.validate_entry), '%P')

    def validate_entry(self, input_value):
        if input_value == "":
            return True
        try:
            float(input_value)
            return True
        except ValueError:
            return False

    def events(self):
        # Basic movements
        self.bind('<KeyPress-Up>', lambda _: self.event_func('FORWARD'))
        self.bind('<KeyPress-Down>', lambda _: self.event_func('BACKWARD'))
        self.bind('<KeyPress-Left>', lambda _: self.event_func('LEFT'))
        self.bind('<KeyPress-Right>', lambda _: self.event_func('RIGHT'))
        self.bind('<KeyRelease-Up>', lambda _: self.event_func('NONE'))
        self.bind('<KeyRelease-Down>', lambda _: self.event_func('NONE'))
        self.bind('<KeyRelease-Left>', lambda _: self.event_func('NONE'))
        self.bind('<KeyRelease-Right>', lambda _: self.event_func('NONE'))
        self.bind('<KeyPress-a>', lambda _: self.event_func('TURNL'))
        self.bind('<KeyPress-d>', lambda _: self.event_func('TURNR'))
        self.bind('<KeyPress-w>', lambda _: self.event_func('UP'))
        self.bind('<KeyPress-s>', lambda _: self.event_func('DOWN'))
        self.bind('<KeyRelease-a>', lambda _: self.event_func('NONE'))
        self.bind('<KeyRelease-d>', lambda _: self.event_func('NONE'))
        self.bind('<KeyRelease-w>', lambda _: self.event_func('NONE'))
        self.bind('<KeyRelease-s>', lambda _: self.event_func('NONE'))

        # TakeOf/Land
        self.bind('<KeyPress-i>', lambda _: self.event_func('TKOF'))
        self.bind('<KeyRelease-i>', lambda _: self.event_func('NONE'))
        self.bind('<KeyPress-q>', lambda _: self.event_func('LAND'))
        self.bind('<KeyRelease-q>', lambda _: self.event_func('NONE'))

    def event_func(self, variable): 
        self.drone_variable = variable

    def drone_connect(self):
        
        ########## Tello ##########
        try: 
            self.drone = tello.Tello()
            self.drone.connect()
            self.connect_button.place_forget()

            self.init_parameters()
            self.menu = Menu(self, 
                    self.height_drone, 
                    self.control_drone, 
                    self.vcmd, 
                    self.reset_pid, 
                    self.take_of, 
                    self.land,
                    self.create_table
                                        )
        
            self.up = UpFrame(self, self.reset, self.progress)
            self.events()

        ########## Threading ##########
            thread1 = threading.Thread(target = self.sequence, daemon = True) # Change for open_loop--> sequence
            thread2 = threading.Thread(target = self.update_indicators, daemon = True)
            thread3 = threading.Thread(target = self.send_drone, daemon = True)
            thread4 = threading.Thread(target = self.send_database, daemon = True)
            thread5 = threading.Thread(target = self.update_parameters_graph, daemon = True)
            thread1.start()
            thread2.start()
            thread3.start()
            self.graph()
            thread4.start()
            thread5.start()
        except: 
            messagebox.showwarning("Warning", "⚠️ Drone in not connected. \n ¡Check your WiFi connection!")

    def send_drone(self):
        while True:
            try: speed = self.control_drone['speed'].get()
            except: speed = 0
            if speed > 100: speed = 100
            elif speed < 0: speed = 0
            lr, fb, up, yv = 0, 0, 0, 0

            if self.height_drone['start'].get():
                up = self.control_signal
                match self.drone_variable:
                    case 'FORWARD':
                        fb = speed
                    case 'BACKWARD': 
                        fb = -speed
                    case 'LEFT':
                        lr = -speed
                    case 'RIGHT':
                        lr = speed
                    case 'TURNL':
                        yv = -speed
                    case 'TURNR':
                        yv = speed
                    case 'LAND':
                        try:self.drone.land()
                        except: print('Something Wrong')
                        self.drone_variable = 'NONE'
                        lr, fb, up, yv = 0, 0, 0, 0
                    case 'TKOF':
                        try: self.drone.takeoff()
                        except: print('Something Wrong') 
                        self.drone_variable = 'NONE'
                        lr, fb, up, yv = 0, 0, 0, 0
                    case _:
                        pass
            else: 
                match self.drone_variable:
                    case 'FORWARD':
                        fb = speed
                    case 'BACKWARD': 
                        fb = -speed
                    case 'LEFT':
                        lr = -speed
                    case 'RIGHT':
                        lr = speed
                    case 'TURNL':
                        yv = -speed
                    case 'TURNR':
                        yv = speed
                    case 'UP':
                        up = speed
                    case 'DOWN':
                        up = -speed
                    case 'LAND':
                        try:self.drone.land()
                        except: print('Something Wrong')
                        self.drone_variable = 'NONE'
                        lr, fb, up, yv = 0, 0, 0, 0
                    case 'TKOF':
                        try: self.drone.takeoff()
                        except: print('Something Wrong') 
                        self.drone_variable = 'NONE'
                        lr, fb, up, yv = 0, 0, 0, 0
                    case _:
                        pass
                
            if self.drone.is_flying:
                try: 
                    self.drone.send_rc_control(lr, fb, up, yv)# Send to drone
                except: 
                    print('Rc Control Failed')               
            time.sleep(0.015)        

    def update_indicators(self): 
        while True:
            variable = self.drone.get_battery()/100
                        
            if variable<0.4 and self.battery_yellow == True and variable> 0.2:
                self.up.battery.progressbar.configure(progress_color = '#FAdA5F') 
                self.battery_yellow = False
                self.battery_red = True
            
            elif variable<0.2 and self.battery_red ==True:
                self.up.battery.progressbar.configure(progress_color = '#A01641') 
                self.battery_yellow = True
                self.battery_red = False

            self.up.battery.progress.set(variable)
            self.altitude = self.drone.get_distance_tof()
            self.up.label_altitude.label_altitude.configure(text = f'Altitude: {self.altitude}')
            time.sleep(0.1)

    def send_database(self):
        previous_time = time.time() #start time
        diferential_time = 0

        if os.path.exists('database.db'):
            os.remove('database.db')
        self.conn = sqlite3.connect('database.db')
        self.c = self.conn.cursor()
        self.c.execute("""
                        CREATE TABLE data_height(
                        Time DATATYPE real,
                        Height DATATYPE integer,
                        SetPoint DATATYPE integer,
                        Error DATATYPE real,
                        Signal DATATYPE integer,
                        Output DATATYPE real)
                        """)
        while True: 
            current_time = time.time()
            diferential_time += (current_time - previous_time)
            self.time = diferential_time
            previous_time = current_time

            error = round(self.error, 6)
            output = round(self.output, 4)
            
            self.c.execute(f"INSERT INTO data_height VALUES ({diferential_time}, {self.altitude}, {self.wished_height}, {error}, {self.control_signal}, {output})")
            self.conn.commit()
            
            if not self.drone.is_flying:
                self.c.execute("SELECT * FROM data_height")
                self.items = self.c.fetchall()

            time.sleep(0.5)

    def graph(self):
                # Create a Matplotlib figure and axes
        self.fig = Figure(figsize=(10, 8), dpi=100, facecolor = GRAPHFACECOLOR)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(SLIDER_BG)
        self.ax.spines['left'].set_color('black')
        self.ax.spines['left'].set_linewidth(2)
        self.ax.grid(
                    axis = 'both', 
                    visible = True, 
                    alpha = 0.3, 
                    linewidth = 1.3, 
                    linestyle = (0,(4, 3)), 
                    color = '0')
        self.ax.tick_params(axis='both', colors = WHITE) 
        # Initial plot setup
        self.x_data = []
        self.y_data = []
        self.setpoint_x_data = []
        self.setpoint_y_data = []
        self.error_x_data = []
        self.error_y_data = []
        self.output_x_data = []
        self.output_y_data = []
        self.line, = self.ax.plot(self.x_data, self.y_data, color = GRAPHBACKCOLOR)
        self.setpoint_line, = self.ax.plot(self.setpoint_x_data, self.setpoint_y_data, color = RED)
        self.error_line, = self.ax.plot(self.error_x_data, self.error_y_data, color = YELLOW)
        self.output_line, = self.ax.plot(self.output_x_data, self.output_y_data, color = PINK)
        # Create a canvas to display the plot in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row = 1, column = 1, sticky = 'nsew', padx = 1, pady = 5)
        
        self.toolbar = NewColorNavigationToolbar2Tk(self.canvas, self, pack_toolbar = False)
        self.toolbar.winfo_children()[-2].config(background=SLIDER_BG)
        self.toolbar.config(background=SLIDER_BG)
        self.toolbar._message_label.config(background = SLIDER_BG)
        self.toolbar.update()
        self.toolbar.grid(row = 2, column = 1) 

        # Start the plot update loop
        self.update_plot()

    def graph2(self):
        pass

    def update_parameters_graph(self):
        empty = []
        def option_1(self, graph2, state): # HEIGHT
            match graph2:
                case 'Error':
                    self.line.set_xdata(self.x_data)
                    self.line.set_ydata(self.y_data)
                    self.setpoint_line.set_xdata(empty)
                    self.setpoint_line.set_ydata(empty)
                    self.error_line.set_xdata(self.error_x_data)
                    self.error_line.set_ydata(self.error_y_data)
                    self.output_line.set_xdata(empty)
                    self.output_line.set_ydata(empty)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.error_y_data)-2), max(max(self.error_y_data),(max(40, max(self.y_data)+5))))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.error_y_data)-2), max(max(self.error_y_data), (max(40, max(self.y_data)+5))))
                case 'Signal':
                    self.line.set_xdata(self.x_data)
                    self.line.set_ydata(self.y_data)
                    self.setpoint_line.set_xdata(empty)
                    self.setpoint_line.set_ydata(empty)
                    self.error_line.set_xdata(empty)
                    self.error_line.set_ydata(empty)
                    self.output_line.set_xdata(self.output_x_data)
                    self.output_line.set_ydata(self.output_y_data)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.output_y_data)-2), max(max(self.output_y_data),(max(40, max(self.y_data)+5))))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.output_y_data)-2), max(max(self.error_y_data), (max(40, max(self.y_data)+5))))
                case 'None':
                    self.line.set_xdata(self.x_data)
                    self.line.set_ydata(self.y_data)
                    self.setpoint_line.set_xdata(empty)
                    self.setpoint_line.set_ydata(empty)
                    self.error_line.set_xdata(empty)
                    self.error_line.set_ydata(empty)
                    self.output_line.set_xdata(empty)
                    self.output_line.set_ydata(empty)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(0, (max(40, max(self.y_data)+5)))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(0, (max(40, max(self.y_data)+5)))
                
                case 'Both':
                    self.line.set_xdata(self.x_data)
                    self.line.set_ydata(self.y_data)
                    self.setpoint_line.set_xdata(empty)
                    self.setpoint_line.set_ydata(empty)
                    self.error_line.set_xdata(self.error_x_data)
                    self.error_line.set_ydata(self.error_y_data)
                    self.output_line.set_xdata(self.output_x_data)
                    self.output_line.set_ydata(self.output_y_data)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.error_y_data)-2, min(self.output_y_data)-2), 
                                        max(max(self.error_y_data),(max(40, max(self.y_data)+5)), max(self.output_y_data)))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.error_y_data)-2, min(self.output_y_data)-2), 
                                        max(max(self.error_y_data), (max(40, max(self.y_data)+5)), max(self.output_y_data)))
        def option_2(self, graph2, state): # SP
            match graph2:
                case 'Error':
                    self.line.set_xdata(empty)
                    self.line.set_ydata(empty)
                    self.setpoint_line.set_xdata(self.setpoint_x_data)
                    self.setpoint_line.set_ydata(self.setpoint_y_data)
                    self.error_line.set_xdata(self.error_x_data)
                    self.error_line.set_ydata(self.error_y_data)
                    self.output_line.set_xdata(empty)
                    self.output_line.set_ydata(empty)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.error_y_data)-2), max(max(self.error_y_data),(max(40, max(self.setpoint_y_data)+5))))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.error_y_data)-2), max(max(self.error_y_data), (max(40, max(self.setpoint_y_data)+5))))
                case 'Signal':
                    self.line.set_xdata(empty)
                    self.line.set_ydata(empty)
                    self.setpoint_line.set_xdata(self.setpoint_x_data)
                    self.setpoint_line.set_ydata(self.setpoint_y_data)
                    self.error_line.set_xdata(empty)
                    self.error_line.set_ydata(empty)
                    self.output_line.set_xdata(self.output_x_data)
                    self.output_line.set_ydata(self.output_y_data)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.output_y_data)-2), max(max(self.output_y_data),(max(40, max(self.setpoint_y_data)+5))))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.output_y_data)-2), max(max(self.output_y_data), (max(40, max(self.setpoint_y_data)+5))))
                case 'None':
                    self.line.set_xdata(empty)
                    self.line.set_ydata(empty)
                    self.setpoint_line.set_xdata(self.setpoint_x_data)
                    self.setpoint_line.set_ydata(self.setpoint_y_data)
                    self.error_line.set_xdata(empty)
                    self.error_line.set_ydata(empty)
                    self.output_line.set_xdata(empty)
                    self.output_line.set_ydata(empty)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.setpoint_x_data)+3))
                        self.ax.set_ylim(0, (max(40, max(self.setpoint_y_data)+5)))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.setpoint_x_data)+3))
                        self.ax.set_ylim(0, (max(40, max(self.setpoint_y_data)+5)))
                case 'Both':
                    self.line.set_xdata(empty)
                    self.line.set_ydata(empty)
                    self.setpoint_line.set_xdata(self.setpoint_x_data)
                    self.setpoint_line.set_ydata(self.setpoint_y_data)
                    self.error_line.set_xdata(self.error_x_data)
                    self.error_line.set_ydata(self.error_y_data)
                    self.output_line.set_xdata(self.output_x_data)
                    self.output_line.set_ydata(self.output_y_data)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.error_y_data)-2, min(self.output_y_data)-2), 
                                        max(max(self.error_y_data),(max(40, max(self.setpoint_y_data)+5)), max(self.output_y_data)))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.error_y_data)-2, min(self.output_y_data)-2), 
                                        max(max(self.error_y_data), (max(40, max(self.setpoint_y_data)+5)), max(self.output_y_data)))

        def option_3(self, graph2, state): # NONE
            match graph2:
                case 'Error':
                    self.line.set_xdata(empty)
                    self.line.set_ydata(empty)
                    self.setpoint_line.set_xdata(empty)
                    self.setpoint_line.set_ydata(empty)
                    self.error_line.set_xdata(self.error_x_data)
                    self.error_line.set_ydata(self.error_y_data)
                    self.output_line.set_xdata(empty)
                    self.output_line.set_ydata(empty)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(-10, min(self.error_y_data)-2), max(max(self.error_y_data)+2,10))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(-10, min(self.error_y_data)-2), max(max(self.error_y_data)+2, 10))
                case 'Signal':
                    self.line.set_xdata(empty)
                    self.line.set_ydata(empty)
                    self.setpoint_line.set_xdata(empty)
                    self.setpoint_line.set_ydata(empty)
                    self.error_line.set_xdata(empty)
                    self.error_line.set_ydata(empty)
                    self.output_line.set_xdata(self.output_x_data)
                    self.output_line.set_ydata(self.output_y_data)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(-10, min(self.output_y_data)-2), max(max(self.output_y_data)+2, 10))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(-10, min(self.output_y_data)-2), max(max(self.output_y_data)+2, 10))
                case 'None':
                    # Update the line data
                    self.line.set_xdata(empty)
                    self.line.set_ydata(empty)
                    self.setpoint_line.set_xdata(empty)
                    self.setpoint_line.set_ydata(empty)
                    self.error_line.set_xdata(empty)
                    self.error_line.set_ydata(empty)
                    self.output_line.set_xdata(empty)
                    self.output_line.set_ydata(empty)

                    # Adjust the axes limits
                    self.ax.set_xlim(-10, 10)
                    self.ax.set_ylim(-10, 10)

                case 'Both':
                    self.line.set_xdata(empty)
                    self.line.set_ydata(empty)
                    self.setpoint_line.set_xdata(empty)
                    self.setpoint_line.set_ydata(empty)
                    self.error_line.set_xdata(self.error_x_data)
                    self.error_line.set_ydata(self.error_y_data)
                    self.output_line.set_xdata(self.output_x_data)
                    self.output_line.set_ydata(self.output_y_data)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(-10, min(self.output_y_data)-2, min(self.error_y_data)-2), max(max(self.output_y_data)+2, 10, max(self.error_y_data)+2))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(-10, min(self.output_y_data)-2, min(self.error_y_data)-2), max(max(self.output_y_data)+2, 10, max(self.error_y_data)+2))

        def option_4(self, graph2, state): # BOTH
            match graph2:
                case 'Error':
                    # Update the line data
                    self.line.set_xdata(self.x_data)
                    self.line.set_ydata(self.y_data)
                    self.setpoint_line.set_xdata(self.setpoint_x_data)
                    self.setpoint_line.set_ydata(self.setpoint_y_data)
                    self.error_line.set_xdata(self.error_x_data)
                    self.error_line.set_ydata(self.error_y_data)
                    self.output_line.set_xdata(empty)
                    self.output_line.set_ydata(empty)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.error_y_data)-2), max(max(self.setpoint_y_data)+5, max(40, max(self.y_data)+5), max(self.error_y_data)+2))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.error_y_data)-2), max(max(self.setpoint_y_data)+5, max(40, max(self.y_data)+5), max(self.error_y_data)+2))
                case 'Signal':
                    # Update the line data
                    self.line.set_xdata(self.x_data)
                    self.line.set_ydata(self.y_data)
                    self.setpoint_line.set_xdata(self.setpoint_x_data)
                    self.setpoint_line.set_ydata(self.setpoint_y_data)
                    self.error_line.set_xdata(empty)
                    self.error_line.set_ydata(empty)
                    self.output_line.set_xdata(self.output_x_data)
                    self.output_line.set_ydata(self.output_y_data)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.output_y_data)-2), max(max(self.setpoint_y_data)+5,(max(40, max(self.y_data)+5)), max(self.output_y_data)+2))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.output_y_data)-2), max(max(self.setpoint_y_data)+5, max(40, max(self.y_data)+5), max(self.output_y_data)+2))
                case 'None':
                    # Update the line data
                    self.line.set_xdata(self.x_data)
                    self.line.set_ydata(self.y_data)
                    self.setpoint_line.set_xdata(self.setpoint_x_data)
                    self.setpoint_line.set_ydata(self.setpoint_y_data)
                    self.error_line.set_xdata(empty)
                    self.error_line.set_ydata(empty)
                    self.output_line.set_xdata(empty)
                    self.output_line.set_ydata(empty)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(0, max(max(self.setpoint_y_data)+10,(max(40, max(self.y_data)+5))))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(0, max(max(self.setpoint_y_data)+10, (max(40, max(self.y_data)+5))))
                case 'Both':
                    # Update the line data
                    self.line.set_xdata(self.x_data)
                    self.line.set_ydata(self.y_data)
                    self.setpoint_line.set_xdata(self.setpoint_x_data)
                    self.setpoint_line.set_ydata(self.setpoint_y_data)
                    self.error_line.set_xdata(self.error_x_data)
                    self.error_line.set_ydata(self.error_y_data)
                    self.output_line.set_xdata(self.output_x_data)
                    self.output_line.set_ydata(self.output_y_data)

                    # Adjust the axes limits
                    if state == 'Incremental':
                        self.ax.set_xlim(0, max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.error_y_data)-2, min(self.output_y_data)-2), 
                                        max(max(self.setpoint_y_data)+5, max(40, max(self.y_data)+5), 
                                            max(self.error_y_data)+2, max(self.output_y_data)+2))
                    else:
                        self.ax.set_xlim(max(0, max(self.x_data)-27), max(30, max(self.x_data)+3))
                        self.ax.set_ylim(min(0, min(self.error_y_data)-2, min(self.output_y_data)-2), 
                                        max(max(self.setpoint_y_data)+5, max(40, max(self.y_data)+5), 
                                            max(self.error_y_data)+2, max(self.output_y_data)+2))

        while True:
            #if self.drone.is_flying or self.restart_graph:
            
            try: 
                self.wished_height = self.height_drone['height'].get()
                if self.wished_height <= 10: self.wished_height = 10
            except: self.wished_height = 10

            error = round(self.error, 6)
            output = round(self.output, 4)

            self.x_data.append(self.data_time_variable)
            self.y_data.append(self.altitude)

            self.setpoint_x_data.append(self.data_time_variable)
            self.setpoint_y_data.append(self.wished_height)
            
            self.error_x_data.append(self.data_time_variable)
            self.error_y_data.append(error)

            self.output_x_data.append(self.data_time_variable)
            self.output_y_data.append(output)

            self.data_time_variable += 0.05
            self.restart_graph = False
            

            #for te menu
            graph1 = self.control_drone['graph1'].get()
            graph2 = self.control_drone['graph2'].get()
            state = self.control_drone['graph_state'].get()

            match graph1:
                case 'Height': option_1(self, graph2, state) 
                case 'SP': option_2(self, graph2, state)
                case 'None': option_3(self, graph2, state)
                case 'Both': option_4(self, graph2, state)

            time.sleep(0.05) # 50 ms

    def update_plot(self):
            # Redraw the canvas
        self.toolbar.update()
        self.canvas.draw()
        self.after(50, self.update_plot)  # Update every 50 ms (0.05 seconds)

    def reset(self): # Important 
        self.x_data = []
        self.y_data = []
        self.setpoint_x_data = []
        self.setpoint_y_data = []
        self.error_x_data = []
        self.error_y_data = []
        self.output_x_data = []
        self.output_y_data = []
        self.data_time_variable = 0
        self.restart_graph = True

    def take_of(self):
        self.drone_variable = 'TKOF'

    def land (self):
        self.drone_variable = 'LAND'

    def reset_pid(self):
        self.altitude = ALTITUDE
        self.integral = 0
        self.previous_error = 0
        self.data_time_variable = 0
        self.height_drone['proportional'].set(DEFAULT_PROPORTIONAL_VALUE_HEIGHT) 
        self.height_drone['derivative'].set(DEFAULT_DERIVATIVE_VALUE_HEIGHT)
        self.height_drone['integral'].set(DEFAULT_INTEGRAL_VALUE_HEIGHT)
        self.height_drone['height'].set(DEFAULT_HEIGHT)
        self.height_drone['start'].set(False)
        self.reset()

    def create_table(self):
        if not self.drone.is_flying:
            time = [round(item[0], 3) for item in self.items]
            height = [item[1] for item in self.items]
            setpoint = [item[2] for item in self.items]
            error = [item[3] for item in self.items]
            signal = [item[4] for item in self.items]
            output = [item[5] for item in self.items]
            TableWindow(time, height, setpoint, error, signal, output)
            time =[]
            height = []
            setpoint = []
            error = []
            signal = []
            output = []
        else: messagebox.showinfo("Information", "Land to show the table!")

    def get_speed(
                self, 
                current_value, 
                dt,
                wished_height,
                proportional_constant,
                integral_constant,
                derivative_constant):

        error = wished_height - current_value #error
        self.error = error
        self.integral += error * dt #integral
        derivative = (error - self.previous_error) / dt #derivative
        # PID OUTPUT
        output = proportional_constant * error + integral_constant * self.integral + derivative_constant * derivative #Output

        if output > MAX_OUTPUT:
            output = MAX_OUTPUT
            self.integral -= error*dt
        elif output < MIN_OUTPUT:
            output = MIN_OUTPUT
            self.integral -= error*dt

        # last error
        self.previous_error = error        
        return output

    def sequence(self):
        previous_time = time.time() #start time
        while True:

            try: 
                wished_height = int(self.height_drone['height'].get())
                if wished_height <= 10: wished_height = 10
            except: wished_height = 10
            try: proportional_constant = float(self.height_drone['proportional'].get())
            except: proportional_constant = 0
            try: integral_constant = float(self.height_drone['integral'].get())
            except: integral_constant = 0
            try: derivative_constant = float(self.height_drone['derivative'].get())
            except: derivative_constant = 0
            
            if self.height_drone['start'].get() and self.drone.is_flying:
                current_time = time.time()
                dt = current_time - previous_time
                previous_time = current_time
                if dt == 0:
                    dt = 0.00000001
                control_signal = self.get_speed(self.altitude, 
                                                dt, 
                                                wished_height,
                                                proportional_constant,
                                                integral_constant,
                                                derivative_constant)
                self.output = control_signal
                self.control_signal = int(np.clip(control_signal, MIN_OUTPUT, MAX_OUTPUT))

            #     try: self.drone.send_rc_control(0, 0, control_signal, 0)
            #     except: print('ERROR 1')
            # elif not self.height_drone['start'].get() and self.drone.is_flying:
            #     try: self.drone.send_rc_control(0, 0, 0, 0)
            #     except: print('ERROR 2')

            time.sleep(0.015) #0.1

    def open_loop(self): # Used to get the dynamic of the system not used in the real
        while True:
            try: 
                wished_height = int(self.height_drone['height'].get())
                if wished_height <= 10: wished_height = 10
            except: wished_height = 10
            
            if self.height_drone['start'].get() and self.drone.is_flying:
                if wished_height > self.altitude:
                    self.control_signal = 60
                else: 
                    self.control_signal = 0

class TableWindow(ctk.CTkToplevel):
    #csv
    def __init__(self, time, height, setpoint, error, signal, output):
        super().__init__()
        ctk.set_appearance_mode('dark')
        self.title('Data Base Table')
        self.resizable(False, False)

        df = pd.DataFrame({
            "Time" : time,
            'Set Point': setpoint,
            "Height": height,
            "Error": error,
            "Signal": signal,
            "Output": output
        })

        self.frame_table = ctk.CTkFrame(self)
        self.frame_table.pack()
        self.table = Table(
                        self.frame_table,
                        dataframe = df, 
                        showstatusbar = True, 
                        showtoolbar = True)
        self.table.show()

class NewColorNavigationToolbar2Tk(NavigationToolbar2Tk):
    def __init__(self, canvas, window, pack_toolbar):
        super().__init__(canvas, window, pack_toolbar = pack_toolbar)

    def _Button(self, text, image_file, toggle, command):
        if not toggle:
            b = tk.Button(
                master=self, text=text, command=command,
                relief="flat", overrelief="groove", borderwidth=1, background=SLIDER_BG,
            
            )
        else:
            var = tk.IntVar(master=self)
            b = tk.Checkbutton(
                master=self, text=text, command=command, indicatoron=False,
                variable=var, offrelief="flat", overrelief="groove",
                borderwidth=1, background=SLIDER_BG
            )
            b.var = var
        b._image_file = image_file
        if image_file is not None:
            # Explicit class because ToolbarTk calls _Button.
            NavigationToolbar2Tk._set_image_for_button(self, b)
        else:
            b.configure(font=self._label_font)
        b.pack(side=tk.LEFT)
        return b

    def set_message(self, s):
        pass

    def _Spacer(self):
        s = tk.Frame(master=self, height='18p', relief=tk.RIDGE, bg='black')
        s.pack(side=tk.LEFT, padx='3p')
        return s

if __name__ == '__main__':
    Window()
