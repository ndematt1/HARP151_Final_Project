from datetime import datetime, timezone
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backends._backend_tk import add_tooltip
import mplcursors

import time

import tkinter as tk
import customtkinter as ctk
import CTkMessagebox
import CTkSpinbox

from functions import *
from mpl_event_funcs import *
from light_pollution_locator import *

from PIL import Image, ImageTk
from io import BytesIO

# Color Palette
bg = "#3c4276"
fg = "#51568d"
lbg = "#454b87"
lfg = "#595e99"
mfg = "#7f81b5"
font = ("Arial Rounded MT Bold", 15)
# Setting fonts in mpl: https://matplotlib.org/stable/users/explain/text/text_props.html
mpl.rcParams['font.family'] = "Arial Rounded MT Bold"
mpl.rcParams['text.color'] = "white"

# All tools we are using that are availible in NavigationToolbar2Tk
toolitems = (
        ('Home', 'Reset original view', 'home', 'home'),
        ('Back', 'Back to previous view', 'back', 'back'),
        ('Forward', 'Forward to next view', 'forward', 'forward'),
        ('Pan',
         'Left button pans, Right button zooms\n'
         'x/y fixes axis, CTRL fixes aspect',
         'move', 'pan'),
        ('Zoom', 'Zoom to rectangle\nx/y fixes axis', 'zoom_to_rect', 'zoom'),
        ('Save', 'Download Star Chart', 'filesave', 'save_figure'),
      )


class LocStarMap:
    def __init__(self, address, dt, highlight = False, time = None):
        
        '''
        A class for a star map
        Has the attributes address, datetime, coordinates, and local siderial time.
        '''
        self.address = address
        
        try:
            self.lat, self.lon = geocode_address(address)
            self.status_code = '200'
        except:
            self.status_code = '404'
            return
        
        self.dt = dt
        self.highlight = highlight
        print(self.lat, self.lon)
        
        # Converts the timezone to UTC
        self.time = self.dt.astimezone(timezone.utc).strftime('%H:%M')
        
        # Getting the LST.
        self.lst = get_siderial_time(dt, self.time, self.lon)
    
    # Method to construct the table with x,y coordinates.
    # Used by the next method to plot our coords on a map.
    # Optionally, includes a limiting apparent magnitude, later will be adjusted by Bortle Scale
    def construct_table(self, df, am = 8):
        '''
        Method to construct the table with x,y coordinates.
        Used by the next method to plot our coords on a map.
        Optionally, includes a limiting apparent magnitude
        '''
        df = df.loc[df['apparent_magnitude'] < am].copy()

        X = []
        Y = []
        
        # Loops through right ascensions and declinations in our dataset
        for ra, dec in zip(df['right_ascension'], df['declination']):
            # Degree conversion
            degra, degdec = conv_rasc_decl(ra, dec)
            
            # Hours angle calculation
            ha = hour_angle(self.lst, degra)
            
            # Altitude and Azimuth Calculation
            alt, az = az_alt_calc(degdec, ha, self.lat)
            
            # Conversion to the cartesian plane
            try:
                x,y = cartesian_conversion(alt, az)
            
            # If we get an arccos/arcsin that is not in its domain, sets x and y to none
            except ValueError:
                x = None
                y = None
                
            X.append(x)
            Y.append(y)
        
        # Creating X and Y Columns
        df['X'] = X
        df['Y'] = Y
        
        
        # Returns the dataframe with the x,y coords
        return df
    
    def plot_stars(self, df, color = 'white', z = 1, size_mult = 1):
        '''
        Method that plots stars using Matplotlib
        '''
        # Checks where both X and Y are nonzero, meaning they can be seen
        stardf = df.loc[(df['X'] != 100) & (df['Y'] != 100)]    
        
        stardf.reset_index(inplace = True)
        
        fig, ax = plt.subplots()
        
        # STARMAP STYLING GOES HERE
        fig.set_size_inches(4,4)
        fig.patch.set_facecolor(fg)
        
        x = stardf['X']
        y = stardf['Y']
        self.title = f"Star Chart of {self.address} at {self.time} UTC on {self.dt.strftime('%B %d, %Y')}"
        ax.set_title(self.title, fontdict = {'fontsize': 22}, wrap = True, pad = 40)
        
        # Highlighting Polaris, just to check for accuracy right now
        #polaris = df.loc[df['name'] == 'Polaris']
        #if polaris.iloc[0]['X'] != 0:
            #plt.scatter(polaris['X'], polaris['Y'], color = 'yellow', s = 20, picker = True)
        
        # Making the background black
        fig.gca().set_facecolor("black")
        
        box = (-1,1)
        ax.set_ylim(box)
        ax.set_xlim(box)
        
        # Removing both x and y ticks
        fig.gca().set_xticks([])
        fig.gca().set_yticks([])
        
        # Creating a scatterplot of our stars
        scatter = ax.scatter(x, y, s = (stardf['apparent_magnitude'].abs() * 2 * size_mult),
                             color = color,marker = 'o', picker = 5)
        
        # Highlighting Important Stars
        important_df = stardf.loc[stardf['apparent_magnitude'] <= 1]
        important = ax.scatter(important_df['X'], important_df['Y'], s = (important_df['apparent_magnitude'].abs() * 80 * size_mult),
                               marker = 'o', color=color, picker = 5)
        
        # Found out how to add these here:
        # https://stackoverflow.com/questions/14762181/adding-a-y-axis-label-to-secondary-y-axis-in-matplotlib
        
        size = 20
        pad = 5
        # Bottom and left to South and west
        ax.set_xlabel("S", fontsize=size, labelpad = pad)
        ax.set_ylabel("W", fontsize = size, rotation = 0, ha = 'right')
        # Duplicating the y axis and adding North on top
        ax2 = ax.twiny()
        ax2.set_xlabel("N", fontsize = size , labelpad = pad)
        ax2.set_xticks(ax.get_xticks())
        ax2.set_xticklabels(ax.get_xticklabels())

        # Duplicating the x axis and adding East on 
        ax3 = ax.twinx()
        ax3.set_ylabel("  E", fontsize = size, rotation = 0)
        ax3.set_yticks(ax.get_yticks())
        ax3.set_yticklabels(ax.get_yticklabels())
        
        # Since these ax vars are set above the first axis,
        # we must set the z order to make the pick events work
        ax.set_zorder(z)
        ax2.set_zorder(-1)
        ax2.patch.set_visible(False)
        ax3.set_zorder(-1)
        ax3.patch.set_visible(False)
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax2.xaxis.label.set_color('white')
        ax2.yaxis.label.set_color('white')
        ax3.xaxis.label.set_color('white')
        ax3.yaxis.label.set_color('white')
        
        '''
        The following code utilizes the mplcursors library.
        More information can be found at: https://mplcursors.readthedocs.io/en/stable/
        '''
          
        # Creating a cursor object which makes the scatterplot a pickupable
        # Also setting hover to make the following function run when the mouse hovers over a datapoint
        # More info on the cursor object here: https://mplcursors.readthedocs.io/en/stable/mplcursors.html#mplcursors.cursor
        cursor = mplcursors.cursor(scatter, hover = True)
        
        # Connections within mpl events and mplcursors both take lambdas with a single arg
        # Since the functions in mpl_event_funcs.py take 2 kwargs, we need to specify them
        # This assigns the kwargs and creates lambda func with no kwargs
        onhover2 = lambda sel: onhover(sel, df = stardf)
        onclick2 = lambda event: onclick(event, plot = scatter, df = stardf)
        
        # The connect method takes paraments like Button from Tkinter.
        # A lambda function is taken for what to do when the cursor interacts
        # THe 'add' parameter makes basically turns the function on.
        cursor.connect('add', onhover2)
        
        cid_click = fig.canvas.mpl_connect('button_press_event', onclick2)
        
        self.fig = fig
        self.ax = ax
        self.cursor = cursor
        
        # Method returns self
        return self
    
    def highlight_constellation(self, df, color, size_mult, z):
        '''
        Method to highlight constellations in the current fig
        '''
        x = df['X']
        y = df['Y']
        
        self.ax.scatter(x, y, s = (df['apparent_magnitude'].abs() * 2 * size_mult),
                        color = color,marker = 'o', picker = 5, zorder = z)
        
    def find_limiting_am(self):
        '''
        Uses Selenium to get te bortle scale of the location.
        Converts it to limiting apparent magnitude
        '''
        bortle_nelm = {1: 8,
                       2: 7.5,
                       3: 7,
                       4: 6.5,
                       4.5: 6.3,
                       5: 6,
                       6: 5.5,
                       7: 5,
                       8: 4.5,
                       9: 4,}
        
        self.bortle = get_bortle(self.lat, self.lon)
        return bortle_nelm[self.bortle]
    
class GUI(ctk.CTk):
    def __init__(self, df, path, *args, **kwargs):
        '''
        GUI object with a df and path as an attribute.
        Child of the CTk root class
        '''
        super().__init__(*args, **kwargs)
        self._state_before_windows_set_titlebar_color = 'zoomed'
        self.title("Sky Atlas")
        self.path = path
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)
        self.config(bg=bg)

        self.df = df
        self.stored_map = False
        
        self.load_images()
        self.load_widgets()
        self.load_presets()
        self.place_tooltips()
        
    
    def load_widgets(self):
        '''
        Method is used to initialize widgets & tkVars
        '''
        self.logo_frame = CustomFrame(master = self, reverse_color = True, bg_color = bg, corner_radius = 0)
        self.entry_frame = CustomFrame(master = self)
        self.map_frame = CustomFrame(master = self)
        self.settings_frame = CustomFrame(master = self)
        
        self.logo_button = ctk.CTkButton(master=self.logo_frame, image=self.logo_ctk_img, text="", fg_color=bg, state="disabled")
        self.info_button = ctk.CTkButton(master = self.map_frame, image=self.info_ctk_img, text = "", fg_color = fg, width = 60, hover_color=fg, command = lambda: self.open_help(800))
        self.instructions = H1Label(master = self.entry_frame, text="First, enter a...")
        
        self.location_label = H2Label(master = self.entry_frame, text="Location")
        self.location_info = H3Label(master = self.entry_frame,
                           text="Enter a full address or general location (e.g. '4400 Vestal Parkway East'\nor 'Cape Town, South Africa') or select a preset location.")
        self.address_entry = EntryBox(master = self.entry_frame)
        
        self.date_label = H2Label(master = self.entry_frame, text="Date")
        self.date_info = H3Label(master = self.entry_frame, text="Enter in the format MM/DD/YYYY.     ")
        self.date_entry_box = EntryBox(master = self.entry_frame, state = 'normal')
        
        self.time_label = H2Label(master = self.entry_frame, text="Time")
        self.time_info = H3Label(master = self.entry_frame, text="Enter in the format HH:MMam/pm.   ")
        self.time_entry_box = EntryBox(master = self.entry_frame, state = 'normal')
        
        self.datevar = tk.IntVar(value = 0)
        self.timevar = tk.IntVar(value = 0)
        self.current_date_checkbox = CheckBox(self.entry_frame, text="Use current date", fg_color = bg, border_color = 'white', hover_color = lbg,
                                              variable = self.datevar, text_color="white", command = lambda: self.disable_entry(self.date_entry_box, self.datevar))
        self.current_time_checkbox = CheckBox(self.entry_frame, text="Use current time", fg_color = bg, border_color = 'white', hover_color = lbg,
                                              variable = self.timevar, text_color="white", command = lambda: self.disable_entry(self.time_entry_box, self.timevar))
        
        self.bortle_check = tk.IntVar()
        self.pollution_checkbox = CheckBox(self.entry_frame, text="Use projected visibility", text_color="white", variable = self.bortle_check, fg_color = bg, border_color = 'white', hover_color = lbg,)
        
        self.selected_constellation = tk.StringVar(self.map_frame, value = 'None')
        self.limiting_am = tk.IntVar(value = 3)
        self.generate_button = ctk.CTkButton(self.entry_frame, text="Generate!", fg_color="#3c4276", hover_color=lbg,
                                             font=("Arial Rounded MT Bold", 25), text_color="white", command = self.press_generate)
        self.settings_button = ctk.CTkButton(self.entry_frame, text = "", image = self.settings_gray_ctk_img, fg_color = fg, hover_color = lfg,
                                             width=65, height=78,
                                             command = self.open_settings, state = 'disabled')
        
        self.clear = tk.Button(self.map_frame, text = 'Clear', command = self.clear_button)
        
        # Quit button and window closing protocol handled
        # https://stackoverflow.com/questions/111155/how-do-i-handle-the-window-close-event-in-tkinter
        self.exit_button = tk.Button(self.entry_frame, text = 'Quit', command=self.quit_button)
        self.protocol("WM_DELETE_WINDOW", self.quit_button)
        self.comparison_frame = CustomFrame(master = self)
        
        
        self.no_canvaslbl = H2Label(master = self.map_frame,
                                    text = 'To view a chart, enter a valid location, date, and time.', text_color=mfg, font=("Arial Rounded MT Bold", 20))
            
    def load_images(self):
        img_path = self.path + '/images/'
        undo_img = Image.open(img_path + "undo_arrow.png")
        self.undo_ctk_img = ctk.CTkImage(light_image=undo_img, size=(50, 50))

        redo_img = Image.open(img_path + "redo_arrow.png")
        self.redo_ctk_img = ctk.CTkImage(light_image=redo_img, size=(50, 50))

        search_img = Image.open(img_path + "search_icon.png")
        self.search_ctk_img = ctk.CTkImage(light_image=search_img, size=(65, 65))
        
        settings_img = Image.open(img_path + "settings_icon.png")
        self.settings_ctk_img = ctk.CTkImage(light_image=settings_img, size=(65, 65))

        settings_gray_img = Image.open(img_path + "settings_icon_gray.png")
        self.settings_gray_ctk_img = ctk.CTkImage(light_image=settings_gray_img, size=(65, 65))

        logo_img = Image.open(img_path + "sky_atlas.png")
        self.logo_ctk_img = ctk.CTkImage(light_image=logo_img, size=(542, 180))
        
        info_img = Image.open(img_path + "info_icon.png")
        self.info_ctk_img = ctk.CTkImage(light_image = info_img, size = (40,40))
    
    def load_presets(self):
        dictionary = {"Atacama Desert, Chile":["-24.5","-69.25"],
              "Natural Bridges, Utah":["37.601383","-110.013744"],
              "Iriomote-Ishigaki National Park, Japan":["24.316667","123.883333"],
              "Kruger National Park, South Africa": ["-24.011389","31.485278"],
              "Pic du Midi Observatory, France": ["42.936389","0.142778"],
              "Mauna Kea, Hawaii, United States":["19.820667","-155.468056"],
              "Kiruna, Sweden":["67.848889","20.302778"],
              "Tenerife, Spain":["28.268611","-16.605556"]
              }
        
        self.selected_preset = tk.StringVar()
        self.selected_preset.set('Presets')
        
        def preset_callback(value):
            if self.selected_preset.get() != 'None':
                self.address_entry.delete(0, tk.END)
                self.address_entry.insert(0, value)
                
            self.selected_preset.set('Presets')
            
        self.preset_dropdown = ctk.CTkOptionMenu(self.entry_frame, variable = self.selected_preset, values = list(dictionary.keys()),
                                     fg_color = bg, button_color = bg, font = ("Arial Rounded MT Bold", 20), text_color = 'white', button_hover_color=lbg,
                                     dropdown_fg_color = bg, dropdown_font = font, dropdown_hover_color=lbg, dropdown_text_color='white',
                                     command = preset_callback)
     
    def place_tk_objects(self):
        '''
        Method for placing all of our objects
        '''
        xvalue = 0.067
        yvalue = 0.086
        
        self.map_frame.place(relx=0.015, rely=0.0267, relwidth=0.4775, relheight=0.9467)
        self.logo_frame.place(relx=0.5075, rely=0.0267, relwidth=0.4775, relheight=0.33868)
        self.entry_frame.place(relx=0.5075, rely=0.39208, relwidth=0.4775, relheight=0.58132)

        self.logo_button.place(relx=0.5, rely=0.6, anchor="center", relwidth=1, relheight=1)

        self.instructions.place(relx=xvalue, rely=yvalue)

        self.location_label.place(relx=xvalue, rely=yvalue+0.1325)
        self.location_info.place(relx=xvalue, rely=yvalue+0.2085)

        self.address_entry.place(relx=xvalue, rely=yvalue+0.2975, relwidth=0.6)
        
        self.date_label.place(relx=xvalue, rely=yvalue+0.4105)
        self.date_info.place(relx=xvalue, rely=yvalue+0.4765)
        self.date_entry_box.place(relx=xvalue, rely=yvalue+0.539, relwidth=0.413)

        self.time_label.place(relx=0.5, rely=yvalue+0.4105)
        self.time_info.place(relx=0.5, rely=yvalue+0.4765)
        self.time_entry_box.place(relx=0.5, rely=yvalue+0.539, relwidth=0.433)

        self.current_time_checkbox.place(relx=0.5, rely=yvalue+0.6375)
        self.current_date_checkbox.place(relx=xvalue, rely=yvalue+0.6375)
        self.pollution_checkbox.place(relx=xvalue, rely=0.820)
        
        self.generate_button.place(relx=0.41, rely=0.814, relwidth=0.523)
        self.settings_button.place(relx=xvalue+0.9, rely=yvalue-0.035, anchor="ne")
        self.preset_dropdown.place(relx=xvalue+0.616, rely=yvalue+0.2975, relwidth=0.25, relheight=0.079)
        self.no_canvaslbl.place(relx = 0.5, rely = 0.5, anchor = 'center')
        
        self.info_button.place(relx = 0.95, rely = 0.043, anchor = 'center')
        
    def show_space_error(self, title="Error", message = "An error has occurred. Please Check inputs and try again", width = 400): #Customize Message upon calling
        #CTkMessagebox.set_appearance_mode("dark")  
        #CTkMessagebox.set_widget_scaling(1.0)            
        box = CTkMessagebox.CTkMessagebox(
            master = self,
            title=title,
            message=message,
            width = width,
            icon="cancel",
            bg_color=bg,    
            fg_color= fg,            
            text_color="white",
            button_text_color="white",
            button_color = fg,
            font = font,
            wraplength = width
        )
        
        return box.get()
    
    def open_help(self, width):
        text1 = "Welcome to Sky Atlas – Your Interactive Star Chart Generator!"
        text2 = "Sky Atlas was developed by Ricky Quach, Beatrice Antoinette, Nicholas DeMatteo, and Fayaz Qadeer. Before you get started, here are a few things to keep in mind:"
        text3 = "If you are curious about what the sky looks like in famous stargazing locations across the world, try out some of the location presets."
        text4 = "Projected visibility accounts for light pollution but does not factor in weather conditions or moon brightness."
        text5 = "Generating a chart with projected visibility may take 8–18 seconds or more, depending on your CPU. If the program seems unresponsive, don’t worry—just give it some time."
        text6 = "Star sizes on the chart reflect their brightness. Brighter stars appear larger, while dimmer stars are smaller."
        text7  = "You can hover over stars to view more details, and double-click a star to open its Wikipedia page (if one exists)."
        text8 = "Enjoy exploring the night sky!"
        
        text_total = "\n\n".join([text1, text2,text3,text4,text5,text6,text7,text8])
        
        box = CTkMessagebox.CTkMessagebox(
            master = self,
            title='Help',
            message=text_total,
            width = width,
            icon=None,
            bg_color=bg,    
            fg_color= bg,            
            text_color="white",
            button_text_color="white",
            button_color = fg,
            button_hover_color=mfg,
            font = font,
            wraplength = width + 100,
            button_width= width / 15,
            height = width / 12,
            border_width= 0
        )
        return box.get()
    
    def quit_button(self):
        '''
        Turns out that mplcursors and mpl event handling uses event loops,
        which makes sense. plt.close('all') is necessary to close those
        If you do not include this, the terminal will not close -> inf loop
        
        Also, an invalid command error would pop up on quit,
        https://stackoverflow.com/questions/26168967/invalid-command-name-while-executing-after-script
        This fixes it.
        '''
        plt.close('all')
        if hasattr(self, 'toolbar'):
            self.toolbar.destroy()
        self.withdraw()
        self.quit()
        self.destroy()
    
    def disable_entry(self, entry, var):
        if var.get() == 1:
            entry.configure(state = 'disabled')
            entry.configure(fg_color = "#696b9e")
            entry.configure(border_color = "#696b9e")
        else:
            entry.configure(state = 'normal')
            entry.configure(fg_color = mfg)
            entry.configure(border_color = mfg)
            
    def clear_button(self):
        self.map_frame.place_forget()
    
    def filter_by_constellation(self, constellation):
        filtered_df = self.df.loc[self.df['parent_constellation'] == constellation]
        return filtered_df
    
    def constellation_dropdown(self, frame, df):
        visible_df = df.loc[df['X'] != 100]
        constellation_value_counts = visible_df['parent_constellation'].value_counts()
        limited_constellation_value_counts = constellation_value_counts.loc[constellation_value_counts > 5]
        constellations = list(limited_constellation_value_counts.index)
        text = [f'{x} : {dict(limited_constellation_value_counts)[x]}' for x in constellations]
        dropdown = ctk.CTkOptionMenu(frame, variable = self.selected_constellation, values = (['None'] + text),
                                     fg_color = bg, button_color = bg, font=("Arial Rounded MT Bold", 25),
                                     button_hover_color=lbg, text_color="white",
                                     dropdown_font=("Arial Rounded MT Bold", 15), dropdown_fg_color=bg, dropdown_hover_color=lbg, dropdown_text_color="white",command = self.update_dropdown)
        return dropdown
    
    def pick_dropdown(self):
        const = self.selected_constellation.get()
        if const == 'Select A Constellation':
            return self.df

        else:
            filtered_df = self.filter_by_constellation(const.split(':')[0].strip())
            return filtered_df
    
    def open_settings(self):
        if self.stored_map:
            add_tooltip(self.store_button, f"{self.stored_map.address} ({self.stored_map.time} UTC)")
        self.settings_frame.place(relx = 0.5075, rely = 0.0267, relwidth=0.4775, relheight=0.9467)
        self.place_settings_tooltips()
        
    def close_settings(self):
        self.settings_frame.place_forget()

    def press_generate(self):
        '''
        Generate Button Functionality
        '''            
        address = self.address_entry.get()
        
        if self.current_date_checkbox.get() == 1:
            user_date = datetime.now().strftime('%m/%d/%Y')
        else:
            try:
                user_date = self.date_entry_box.get()
                datetime.strptime(user_date,'%m/%d/%Y')
            except:
                self.show_space_error(title='Invalid Date', message = 'Invalid Date. Please enter a Date with format (MM/DD/YYYY)')
                return
        
        if self.current_time_checkbox.get() == 1:
            user_time = datetime.now().strftime('%I:%M%p')
        else:
            try:
                user_time = self.time_entry_box.get()
                datetime.strptime(user_time,'%I:%M%p')
            except:
                self.show_space_error(title='Invalid Time', message = 'Invalid Time. Please enter a Time with format (HH:MMam/pm)')
                return

        dt_str = f'{user_date} {user_time}'
        dt = datetime.strptime(dt_str, '%m/%d/%Y %I:%M%p')
        
        # Creating an instance of our LocStarMap object
        map = LocStarMap(address, dt)
        if map.status_code == '404':
            self.show_space_error(title='Invalid Address', message = 'Invalid Address. Try again with a different location.')
            return
        self.map = map
        self.update_canvas()
    
    def store_map(self, current = True):
        if current:
            self.show_compare_button.configure(state = 'normal')
            self.stored_map = self.map

        add_tooltip(self.store_button, f"{self.stored_map.address} ({self.stored_map.time} UTC)")
        stored_canvas = FigureCanvasTkAgg(self.stored_map.fig, master = self.comparison_frame)
        stored_canvas.draw()
        stored_canvas_widget = stored_canvas.get_tk_widget()
        stored_canvas_widget.configure(bg = fg)
        self.stored_canvas_widget = stored_canvas_widget
        self.stored_canvas_widget.place(anchor = 'center', relx = .49, rely = .535, relwidth = 1, relheight = 0.85)
        
    def show_comparison(self):
        self.comparison_frame.place(relx = 0.5075, rely = 0.0267, relwidth=0.4775, relheight=0.9467)
        self.hide_compare_button.place(relx = .747, rely = 0.02)
    
    def hide_comparison(self):
        self.comparison_frame.place_forget()           
        self.store_map(current = False)
        
    def update_canvas(self):
        '''
        Method used to update the existing canvas in the map frame.
        '''
        if hasattr(self, 'fig'):
            self.clear_button()
            self.map_frame.place(relx=0.015, rely=0.0267, relwidth=0.4775, relheight=0.9467)
            
        if self.bortle_check.get() == 1:
            if not hasattr(self.map, 'bortle'):
                self.limiting_am.set(self.map.find_limiting_am())
            else:
                self.limiting_am.set(self.map.bortle)
        
        # Constructing the table and reseting the index because we want the indexes to match with our star names
        limited_df = self.map.construct_table(self.df, am = self.limiting_am.get()).reset_index()
        #limited_df.to_csv(r'C:\Users\ricky\OneDrive\Documents\HARP151\Final Project\HARP-151-Final-Project\test.csv')
        
        self.map.plot_stars(limited_df)
        selected = self.selected_constellation.get()
        
        if selected != 'Select A Constellation' and selected != 'None':
            highlighted = self.map.construct_table(self.pick_dropdown(), am = self.limiting_am.get()).reset_index()
            self.map.highlight_constellation(highlighted, color = 'red', size_mult = 2, z=100)
                
        # Avoiding stacking dropdowns.
        if hasattr(self, 'dropdown'):
            self.dropdown.place_forget()
            #self.dropdown.destroy()
        
        self.fig = self.map.fig
        self.cursor = self.map.cursor
    
        canvas = FigureCanvasTkAgg(self.map.fig, master=self.map_frame)
        canvas.draw()
        
        # Figured out how to add figures into Tkinter here:
        # https://pythonprogramming.net/how-to-embed-matplotlib-graph-tkinter-gui/
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.configure(bg = fg)
        self.canvas = canvas
        self.canvas_widget = canvas_widget
        
        # Makes the settings button clickable
        self.settings_button.configure(state = 'normal', image=self.settings_ctk_img)
        self.create_settings_widgets(limited_df)
        if self.stored_map:
            self.show_compare_button.configure(state = 'normal')
            
        self.dropdown.place(relx=0.5, rely=0.676, anchor="center", relwidth=0.5, relheight=0.05)
        self.canvas_widget.place(anchor = 'center', relx = .49, rely = .535, relwidth = 1, relheight = 0.85)
    
    def create_toolbar(self):
        '''
        Method for styling and placing the toolbar
        This includes creating a dict with the name of the tool as the
        key and the tool object as the value. Tool objects are interactive CTk widgets with commands.
        Creating a dict was helpful because there was no attribute I could find to tell what tool was what.
        '''
        xvalue = 0.067
        yvalue = 0.049
        
        self.toolbar = CustomToolbar(self.canvas, self.settings_frame, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.config(background=fg)
        
        self.save_button = CustomToolbar(self.canvas, self.settings_frame, pack_toolbar = False)
        
        tooldict = {tool: self.toolbar.winfo_children()[self.toolbar.tool_list.index(tool)] for tool in self.toolbar.tool_list}
        savebutton = {'Save': self.save_button.winfo_children()[-1]}
        
        tooldict['Home'].configure(text = 'Reset', font=("Arial Rounded MT Bold", 22), fg_color = bg, bg_color = fg, hover_color = lbg)   
        tooldict['Back'].configure(text = '', image = self.undo_ctk_img,
                                   width = 50, height = 63, hover_color = lfg)
        tooldict['Forward'].configure(text = '', image = self.redo_ctk_img,
                                      width = 50, height = 63, hover_color = lfg)
        tooldict['Pan'].configure(text = 'Pan Mode', font=("Arial Rounded MT Bold", 20))
        tooldict['Zoom'].configure(text = 'Zoom Mode', font=("Arial Rounded MT Bold", 20))
        #tooldict['Save'].configure(text = 'Save')
        
        savebutton['Save'].configure(text = 'Download Star Chart', font=("Arial Rounded MT Bold", 25),
                                     fg_color = bg, bg_color = fg, hover_color = lbg)
        
        tooldict['Home'].place(relx=0.733, rely = 0.25, relheight = 0.5, relwidth = 0.2)
        tooldict['Back'].place(relx=0.395, rely = yvalue + 0.025)
        tooldict['Forward'].place(relx=0.547, rely =yvalue + 0.025)
        tooldict['Pan'].place(relx=xvalue, rely = 0.1)
        tooldict['Zoom'].place(relx=xvalue, rely = 0.55)
        #tooldict['Save'].place(relx=0, rely = 0.5)
        
        savebutton['Save'].place(relx = 0, rely = 0, relwidth=1, relheight=1, anchor = 'nw')
        
        self.toolbar.place(relx=0,rely=0.229, relheight=0.1, relwidth=1)
        self.save_button.place(relx = xvalue, rely = 0.951, relwidth = 0.866, anchor = 'sw')
        self.save_button.configure(bg = fg)
        
    def update_spinbox(self, count):
        self.limiting_am.set(count)
        self.bortle_check.set(0)
        self.update_canvas()
    
    def update_dropdown(self, value):
        self.update_canvas()
        
    def create_settings_widgets(self, df):
        '''
        Method for initializing widgets in the settings frame
        '''
        xvalue = 0.067
        yvalue = 0.049
        self.close_button = ctk.CTkButton(self.settings_frame, image=self.search_ctk_img, text = '', fg_color = fg, hover_color = lfg,
                                             font=("Arial Rounded MT Bold", 15), command = self.close_settings,
                                             width = 65, height=78)
        self.create_toolbar()
        self.dropdown = self.constellation_dropdown(self.settings_frame, df)
        self.am_spinbox = CTkSpinbox.CTkSpinbox(master = self.settings_frame, start_value=self.limiting_am.get(), font = ("Arial Rounded MT Bold", 30),
                                                min_value=-1, max_value = 8, variable = self.limiting_am, command=self.update_spinbox,
                                                fg_color = bg, button_color = fg, border_width = 0, button_hover_color=lfg, button_border_width=0)
        
        self.settingslbl = ctk.CTkLabel(self.settings_frame, text="Settings", text_color="white", font=("Arial Rounded MT Bold", 35))
        self.toolbar_label = ctk.CTkLabel(self.settings_frame, text="Toolbar", text_color="white", font=("Arial Rounded MT Bold", 25))
        self.toolbar_info = ctk.CTkLabel(self.settings_frame, text="Use to adjust the view and fine-tune your star chart's appearance.", text_color="white", font=("Arial Rounded MT Bold", 15, "italic"), justify="left")
        self.lm_label = ctk.CTkLabel(self.settings_frame, text="Limiting Magnitude", text_color="white", font=("Arial Rounded MT Bold", 25))
        self.lm_info = ctk.CTkLabel(self.settings_frame, text="Use to show more or fewer stars. Lower values display only bright stars,\nwhile higher values include dimmer stars visible under darker skies.", text_color="white", font=("Arial Rounded MT Bold", 15, "italic"), justify="left")
        self.comparison_label = ctk.CTkLabel(self.settings_frame, text="Comparison", text_color="white", font=("Arial Rounded MT Bold", 25))
        self.comparison_info = ctk.CTkLabel(self.settings_frame, text="Use to store your current chart so you can view it side by side with any\nnew chart you generate.", text_color="white", font=("Arial Rounded MT Bold", 15, "italic"), justify="left")
        self.constellation_label = ctk.CTkLabel(self.settings_frame, text="Constellations", text_color="white", font=("Arial Rounded MT Bold", 25))
        self.constellation_info = ctk.CTkLabel(self.settings_frame, text="Select a constellation to highlight.", text_color="white", font=("Arial Rounded MT Bold", 15, "italic"), justify="left")
        self.hide_compare_button = ctk.CTkButton(self.comparison_frame, text = 'Hide', fg_color = bg, bg_color = fg, font=("Arial Rounded MT Bold", 25), text_color="white", hover_color=lbg, command = self.hide_comparison)
        self.store_button = ctk.CTkButton(self.settings_frame, text = 'Store Chart', fg_color = bg, bg_color = fg, font=("Arial Rounded MT Bold", 25),
                                          command = self.store_map, hover_color=lbg, text_color="white")
        self.show_compare_button = ctk.CTkButton(self.settings_frame, text = 'View Stored Chart', font=("Arial Rounded MT Bold", 25), fg_color = bg, bg_color = fg,
                                                 command = self.show_comparison, state = 'disabled', text_color_disabled="#a4a6ad", text_color="white", hover_color=lbg
                                                 )

        self.settingslbl.place(relx=xvalue, rely=yvalue)
        self.toolbar_label.place(relx=xvalue, rely=yvalue+0.0825)
        self.toolbar_info.place(relx=xvalue, rely=yvalue+0.122)
        
        self.lm_label.place(relx=xvalue, rely=yvalue+0.315)
        self.lm_info.place(relx=xvalue, rely=yvalue+0.3615)
        
        self.constellation_label.place(relx=xvalue, rely=0.56)
        self.constellation_info.place(relx=xvalue, rely=0.6)
        
        self.comparison_label.place(relx=xvalue, rely=yvalue+0.66)
        self.comparison_info.place(relx=xvalue, rely=yvalue+0.705)
        
        self.am_spinbox.place(relx=0.5,rely=yvalue + 0.475, anchor = "center", relwidth=0.25, relheight=0.075)
        self.store_button.place(relx=xvalue, rely=0.82, relwidth=0.428)
        self.show_compare_button.place(relx=xvalue+0.438, rely=0.82, relwidth=0.433)
        
        self.close_button.place(relx = xvalue + .9, rely = yvalue - .022, anchor = "ne")

    def place_tooltips(self):
        '''
        Tooltips are added for toolbar items in the Matplotlib TKagg backends.
        We imported a function that adds those tooltips.
        '''
        add_tooltip(self.settings_button, 'Settings')
        
    def place_settings_tooltips(self):
        add_tooltip(self.close_button, "Back to Search")
        
        
        
        
'''
Styling Widgets in bulk
'''
class CustomFrame(ctk.CTkFrame):
    def __init__(self, reverse_color = False, *args, **kwargs):
        if not reverse_color:
            kwargs.setdefault('fg_color',fg)
            kwargs.setdefault('bg_color',bg)
        else:
            kwargs.setdefault('fg_color',bg)
            kwargs.setdefault('bg_color',fg)
            
        kwargs.setdefault('corner_radius',15)
            
        super().__init__(*args, **kwargs)

class H1Label(ctk.CTkLabel):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('font', ("Arial Rounded MT Bold", 35))
        kwargs.setdefault('text_color', 'white')
        kwargs.setdefault('justify', 'left')
        super().__init__(*args, **kwargs)
        
class H2Label(H1Label):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('font', ("Arial Rounded MT Bold", 25))
        super().__init__(*args, **kwargs)

class H3Label(H1Label):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('font', ("Arial Rounded MT Bold", 15, 'italic'))
        super().__init__(*args, **kwargs)

class EntryBox(ctk.CTkEntry):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("fg_color", mfg)
        kwargs.setdefault("border_color", mfg)
        kwargs.setdefault("text_color", "white")
        kwargs.setdefault("font",("Arial Rounded MT Bold", 25))
        super().__init__(*args, **kwargs)

class CheckBox(ctk.CTkCheckBox):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('font', ("Arial Rounded MT Bold", 15))
        super().__init__(*args, **kwargs)
        
# After much time of researching matplotlib, the backend for tkagg is here:
# https://github.com/matplotlib/matplotlib/blob/main/lib/matplotlib/backend_bases.py
# https://github.com/matplotlib/matplotlib/blob/main/lib/matplotlib/backends/_backend_tk.py

# The NavigationTookBar2 parent class is found on line 2779 of the  first github repo
# The Tk child class is found on line 621 of the second repo
class CustomToolbar(NavigationToolbar2Tk):
    toolitems = toolitems
    def __init__(self, *args, **kwargs):
        self.tool_list = [x[0] for x in toolitems[:-1]]
        super().__init__(*args, **kwargs)
        
        # Matplotlib backend devs used label to move packed toolbar
        # this removes all of them
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label):
                widget.destroy()
                
    # Making it so the toolbar wont show the x,y coords when hovering over.
    def mouse_move(self, event):
        pass
    
    def _Button(self, text, image_file, toggle, command):
        '''
        This method is found on line 827 of the _backend_tk.py file in the mpl backend
        Alters button generation slightly to make them ctk buttons instead of tk.
        '''
        if not toggle:
            b = ctk.CTkButton(
                master=self, text=text, command=command,
                fg_color = fg, hover_color = lfg, text_color="white"
            )
        else:
            var = tk.IntVar(master=self)
            b = ctk.CTkSwitch(
                master=self, text=text, command=command,
                variable=var, button_color="white", progress_color=mfg, fg_color=bg, text_color="white"
            )
            b.var = var

        b.configure(font=font)
        b.name = text
        
        return b