import customtkinter as ctk 
from settings import *
from panels import Battery, Reset, Label

class UpFrame(ctk.CTkFrame):
    def __init__(self, parent, reset, progress):
        super().__init__(master = parent, fg_color = 'transparent')
        self.battery = Battery(self, progress)
        self.reset = Reset(self, reset)
        self.label_altitude = Label(self)
        self.grid(row = 0, column = 1, sticky = 'nwe')