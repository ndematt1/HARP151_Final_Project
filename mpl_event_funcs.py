import mplcursors
import matplotlib.pyplot as plt
import webbrowser
import tkinter as tk
import customtkinter as ctk

base = 'https://en.wikipedia.org'
bg = "#3c4276"
fg = "#51568d"
font = ("Arial Rounded MT Bold", 15)
def onhover(sel, df = None):
    # Getting a the index of our selector
    index = sel.index
    
    # Pairing the selector with an annotation, which is a matplotlib object to annotate points.
    # In this case, the pair is the link to the star
    try: 
        name = df.loc[index, 'name']
        pc = df.loc[index,'parent_constellation']
        am = df.loc[index,'apparent_magnitude']
        ra = df.loc[index, 'right_ascension']
        dec = df.loc[index, 'declination'].replace("′", "'").replace("″",'"')
        dist = df.loc[index, 'distance (ly)']
        text = f'{name}\nParent Constellation: {pc}\nApparent Magnitude: {am}\nRight Ascension: {ra}\nDeclination: {dec}\nDistance (ly): {dist}'
        sel.annotation.set_text(text)
        
    except KeyError:
        sel.annotation.set_text('Unnamed Star')
    
    # Just some simple styling
    # The annotation object has the same kwargs as any text object in MPL
    sel.annotation.get_bbox_patch().set(facecolor="#51568d", alpha=0.7) 
    
# TWO WAYS TO ADD THE CLICKABLE EVENT
# the pick events don't actually have double click functionality
def onpick(event, df = None):
    ind = event.ind
    webbrowser.open(base + df['link'][ind])
#fig.canvas.mpl_connect('pick_event', onpick)

# Click events do
#Using contains to check the closest point
#https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.contains.html
def onclick(event, plot = None, df = None):
    if event.dblclick:
        contains, index_dict = plot.contains(event)
        if contains:
            ind = index_dict['ind']
            if len(ind) > 1:
                choose_pop_up(ind, df)
            else:
                print(str(base + df.loc[ind, 'link'].values[0]))
                webbrowser.open(base + str(df['link'][ind].values[0]))

def choose_pop_up(ind_list, df):
    choose_root = ctk.CTkToplevel()
    choose_root.title('Multiple Stars Selected')
    choose_root.configure(fg_color = fg)
    h1lbl = ctk.CTkLabel(choose_root, text = 'Trying to open multiple stars.\nSelect one in the dropdown.',
                         font = ("Arial Rounded MT Bold", 15)).pack()
    h2lbl = ctk.CTkLabel(choose_root, text = 'To avoid selecting multiple stars, use the zoom feature.',
                         font = ("Arial Rounded MT Bold", 10)).pack(padx = 10)
    name_dict = {}
    
    for i in ind_list:
        name_dict.update({df['name'][i]: i})
        
    selected = tk.StringVar(choose_root, value = list(name_dict.keys())[0])
    
    dropdown = ctk.CTkOptionMenu(master = choose_root, variable = selected, values = list(name_dict.keys()),
                                 fg_color = bg, button_color = bg, font = font, text_color='white',
                                 dropdown_fg_color=fg, dropdown_font=font)
    dropdown.pack()
    
    def submit():
        name = selected.get()
        choose_label = tk.Label(choose_root, textvariable=selected) 
        selected.set(name)
        ind = name_dict[name]
        webbrowser.open(base + df['link'][ind])
        choose_root.destroy()
    
    submit_button = ctk.CTkButton(choose_root, text = 'Submit', command = submit, fg_color = bg)
    quit_button = ctk.CTkButton(choose_root, text = 'Quit', fg_color = bg, command = choose_root.destroy)
    
    submit_button.pack()
    quit_button.pack()
    
    choose_root.mainloop()