# HARP-151-Final-Project
 Team Members: Beatrice Antoinette, Ricky Quach, Nicholas DeMatteo, Fayaz Qadeer 

To run the program, just install the required libraries and then run the main.py file.

Welcome to Sky Atlas – Your Interactive Star Chart Generator!
Before you get started, here are a few things to keep in mind:
If you are curious about what the sky looks like in famous stargazing locations across the world, try out some of the location presets.
Projected visibility accounts for light pollution but does not factor in weather conditions or moon brightness.
Generating a chart with projected visibility may take 8–18 seconds or more, depending on your CPU. If the program seems unresponsive, don’t worry—just give it some time.
Star sizes on the chart reflect their brightness. Brighter stars appear larger, while dimmer stars are smaller.
You can hover over stars to view more details, and double-click a star to open its Wikipedia page (if one exists).

Imports Used

Standard Library:
datetime – from datetime import date, datetime, timezone
json
tkinter – import tkinter as tk
webbrowser

Third-Party Libraries:
requests
pandas – import pandas as pd
matplotlib – import matplotlib as mpl, import matplotlib.pyplot as plt,
from matplotlib.backend_tools import ToolBase, ToolToggleBase,
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
mplcursors
seaborn – import seaborn as sns
customtkinter – import customtkinter as ctk
ctkmessagebox

Local Modules:
functions.py – from functions import *
mpl_event_funcs.py – from mpl_event_funcs import *
light_pollution_locator.py – from light_pollution_locator import *

pip install:
matplotlib
pandas
requests
mplcursors
seaborn
tk
customtkinter
CTkMessagebox
astropy
CTkSpinBox