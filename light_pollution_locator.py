from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from time import sleep

def to_the_fifth_decimal(coord): #the light pollution website requires five decimal places
    coord =  f"{(coord):.5f}" #gets five decimal places
    return coord

def get_bortle(lat, lon):
    service = Service(ChromeDriverManager().install())

    '''
    I have prior experience with command line args when I had
    a horrible laptop and was trying to speed up Chrome.
    Works the same with Selenium

    A list of Command Line Args can be found here:
    https://peter.sh/experiments/chromium-command-line-switches/
    '''
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    
    # The terminal told me to add this bc of depreciation
    options.add_argument("--enable-unsafe-swiftshader")
    
    lat_updated = to_the_fifth_decimal(lat)
    lon_updated = to_the_fifth_decimal(lon)

    driver = webdriver.Chrome(service=service, options = options)

    driver.get(f"https://www.lightpollutionmap.info/#zoom=9&lat={lat_updated}&lon={lon_updated}")
    try:
        main = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "searchBox"))
            )
        main.send_keys(f"{lat_updated}, {lon_updated}", Keys.RETURN)
        
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "tableCellValues")))
        #driver.execute_script("document.body.style.zoom = '50%'") #zoom out and make the screen 50% because it would not scrape the box because it did not appear on the screen 
        bortle = driver.find_elements(By.CLASS_NAME, "tableCellValues")[5] 
        bort = bortle.find_element(By.TAG_NAME, "a").text.strip()[6:]
        
        if "-" in bort:
            bort_list = bort.split('-') #creates a list if the variable is split by "-"" 
            bort = bort_list[1] #takes the highest value of the range
            bort = int(bort) #makes integer 
        
        else:
            bort = int(bort) #if there is no rate it makes bort a integer

    finally:
        driver.quit()
        return bort
    