from classes import *
import os

# Getting the path of the py file
# https://stackoverflow.com/questions/5137497/find-the-current-directory-and-files-directory
path = os.path.dirname(os.path.realpath(__file__))
directory = path + '/datasets/star_data_clean.csv'

def main():
    stars = pd.read_csv(directory)
    
    gui = GUI(stars, path)
    gui.place_tk_objects()
    gui.mainloop()
    
if __name__ == '__main__':
    main() 