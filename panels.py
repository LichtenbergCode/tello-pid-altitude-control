import customtkinter as ctk 
from tkinter import filedialog
from settings import *

class Panel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(master = parent, fg_color= DARKGRAY)
        self.pack(padx = 5, pady = 5)

class Panel2(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color= DARKGRAY)
        self.pack(fill = 'x', pady = 4, ipady = 8, padx = 5)

class SliderPanel(Panel):
    def __init__(self, parent, text, data_var, vcmd, min_value, max_value):
        super().__init__(parent = parent)

        # layout
        self.rowconfigure((0, 1, 2), weight = 1)
        self.columnconfigure((0,1), weight = 1)
        self.entry_variable = ctk.DoubleVar()
        self.data_var = data_var
        self.data_var.trace('w', self.update_text)

        self.label_slider = ctk.CTkLabel(self, text = text)
        self.label_slider.grid(column = 0, row = 0, sticky = 'W', padx = 5)

        self.num_label = ctk.CTkLabel(self, 
                                    text = self.data_var.get()
                                    )
        self.num_label.grid(column = 1, row = 0, sticky = 'E', padx = 5)

        self.slider = ctk.CTkSlider(self, 
                        fg_color = SLIDER_BG, 
                        variable = self.data_var,
                        from_ = min_value,
                        to = max_value,)
        self.slider.grid(row = 1, column = 0, columnspan = 2, sticky = 'EW', padx = 5, pady = 5)

        self.entry = ctk.CTkEntry(self, 
                    fg_color = SLIDER_BG, 
                    textvariable = self.entry_variable,
                    validate = 'key',
                    validatecommand = vcmd)
        self.entry.grid(row = 2, column = 0, columnspan = 1, sticky = 'EW', padx = 4, pady = 5)
        
        self.button =ctk.CTkButton(self, 
                    text = 'Send',
                    width=50,
                    height=15,
                    command = self.send_entry )
        self.button.grid(row = 2, column = 1, columnspan = 1, sticky = 'EW', padx = 2.5, pady = 5)

    def update_text(self, *args):
        try: self.num_label.configure(text = f'{round(self.data_var.get(),2)}')
        except: pass
    
    def send_entry(self):
        if self.entry_variable.get() == "": 
            try: self.data_var.set(0)
            except: pass
        else:
            try: self.data_var.set(self.entry_variable.get())
            except: pass

class Switch(Panel):
    def __init__(self, parent, switch_var):
        super().__init__(parent)

        ctk.CTkSwitch(
                    self, 
                    text = 'Start PID',
                    variable = switch_var ,
                    onvalue = True,
                    offvalue = False).pack()

class Button(Panel):
        def __init__(self, parent, reset_pid, text):
            super().__init__(parent)
            ctk.CTkButton(
                self, 
                text = text, 
                width=100, 
                height=15, 
                command = reset_pid).pack(padx = 5, pady = 5)

class SegmentedPanel(Panel2):
    def __init__(self, parent, text, data_var, options):
        super().__init__(parent = parent)

        ctk.CTkLabel(self, text = text).pack()
        ctk.CTkSegmentedButton(self, variable=data_var, values = options, 
                            bg_color = DARKGRAY, fg_color = DARKGRAY, unselected_color = DARKGRAY).pack(expand = True, fill = 'both', padx = 4, pady = 4)

##########################

class Battery(ctk.CTkFrame):
    def __init__(self, parent, progress):
        super().__init__(master = parent, fg_color='transparent')
        self.progress = progress
        
        # Create a progress bar with specific properties
        self.progressbar = ctk.CTkProgressBar(self, width=50, 
                                        height=25, 
                                        corner_radius = 0, 
                                        progress_color= PROGRESSCOLOR,
                                        fg_color=BACKPROGRESSCOLOR, 
                                        bg_color=BACKPROGRESSCOLOR,
                                        variable = self.progress)
        self.progressbar.pack(side = 'left', pady=20)
        frame = ctk.CTkFrame(self, width = 6, height =14, fg_color = BACKPROGRESSCOLOR, bg_color = BACKPROGRESSCOLOR)
        frame.pack(side = 'left', pady = 20)

        self.place(relx = 0.5, rely = 0.05, anchor = 'n')

class Reset(ctk.CTkButton):
    def __init__(self, parent, reset):
        super().__init__(
                        master = parent, 
                        text = 'RESET', 
                        text_color = WHITE, 
                        fg_color = 'transparent', 
                        width = 40, 
                        height = 40,
                        corner_radius = 0,
                        hover_color = RED,
                        command = reset)
        self.place(relx = 0.99, rely = 0.5, anchor = 'e')
        print(self.cget("font"))

class Buttons(ctk.CTkFrame):
    def __init__(self, parent, tkof, land, text_btn1, text_btn2):
        super().__init__(parent)
        # Layout
        self.columnconfigure((0, 1), weight = 1)
        self.rowconfigure(0, weight = 1)
        ctk.CTkButton(self, text = text_btn1, width=100, height=15, corner_radius = 100, command = tkof).grid(row = 0, column = 0, padx = 5, pady = 5)
        ctk.CTkButton(self, text = text_btn2, width=100, height=15, corner_radius = 100, command =land).grid(row = 0, column = 1, padx = 5, pady = 5)
        
        self.place(relx = 0.5, rely = 1, anchor = 's')

class Label(ctk.CTkFrame):
    def __init__(self, parent, text = 'Makako'):
        super().__init__(parent, fg_color = 'transparent')
        self.label_altitude = ctk.CTkLabel(
                                    self, 
                                    text = text, 
                                    width = 40, 
                                    height = 40, 
                                    fg_color = 'transparent',
                                    text_color = WHITE, 
                                    font = ("Segoe UI", 16))
        self.label_altitude.pack(expand = True, fill = 'both')
        
        self.place(relx = 0.01, rely = 0.5, anchor = 'w')

class DroneConnection(ctk.CTkFrame):
    def __init__(self, parent, drone_connect):
        super().__init__(master = parent, fg_color = 'transparent')
        self.place(relx = 0.5, rely = 0.5, anchor = 'center')
        ctk.CTkButton(self, text ='Connect Drone', command= drone_connect).pack(expand = True)

