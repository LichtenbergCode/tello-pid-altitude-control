import customtkinter as ctk
from settings import *
from panels import *

class Menu(ctk.CTkTabview):
    def __init__(self, parent, height, control, vcmd, reset_pid, tkof, land, table):
        super().__init__(master = parent, fg_color = PANELCOLOR)
        
        self.add('Height')
        self.add('Control')
        HeightFrame(self.tab('Height'), height, vcmd, reset_pid, tkof, land)
        ControlFrame(self.tab('Control'), control, vcmd, table, tkof, land)
        self.grid(row = 0, column = 0, sticky = 'nswe', rowspan = 3)

class HeightFrame(ctk.CTkFrame):
    def __init__(self, parent, height, vcmd, reset_pid, tkof, land):
        super().__init__(master = parent, fg_color = 'transparent')
        Switch(self, height['start'])
        
        SliderPanel(
            self, 
            'Height', 
            height['height'], 
            vcmd, 
            MIN_SLIDER_VALUE_HEIGHT, 
            MAX_SLIDER_VALUE_HEIGHT) # 0m - 5m
        
        SliderPanel(
            self, 
            'Proportional', 
            height['proportional'], 
            vcmd, 
            MIN_SLIDER_VALUE_PROPORTIONAL, 
            MAX_SLIDER_VALUE_PROPORTIONAL)
        
        SliderPanel(
            self, 
            'Integral', 
            height['integral'], 
            vcmd, 
            MIN_SLIDER_VALUE_INTEGRAL, 
            MAX_SLIDER_VALUE_INTEGRAL)
        
        SliderPanel(
            self, 
            'Derivative', 
            height['derivative'], 
            vcmd, 
            MIN_SLIDER_VALUE_DERIVATIVE, 
            MAX_SLIDER_VALUE_DERIVATIVE)
        
        Button(self, reset_pid, 'Reset "PID"')
        Buttons(self, tkof, land, 'Take Of', 'Land')

        self.pack(expand = True, fill = 'both')
    
class ControlFrame(ctk.CTkFrame):
    def __init__(self, parent, control, vcmd, table, tkof, land):
        super().__init__(master = parent, fg_color = 'transparent')
        SliderPanel(self,
                    'Speed',
                    control['speed'],
                    vcmd,
                    MIN_SLIDER_VALUE_SPEED,
                    MAX_SLIDER_VALUE_SPEED) 
        
        SegmentedPanel(self, 'Graph 1', control['graph1'], OPTIONS_DRONE_GRAPH1)
        SegmentedPanel(self, 'Graph 2', control['graph2'], OPTIONS_DRONE_GRAPH2)
        SegmentedPanel(self, 'Graph State', control['graph_state'], OPTIONS_DRONE_GRAPH_STATE)
        Button(self, table, 'Table')
        Buttons(self, tkof, land, 'Take Of', 'Land')

        self.pack(expand = True, fill = 'both')

