import requests
import json
from datetime import datetime
from astropy.time import Time
from math import cos, sin, radians, degrees, asin, acos, pi
import numpy as np

# Makes an API call to the geocoding api. Returns latitude and longitude from an address
def geocode_address(address):
    api_key = "67e16f5b9807f168073335qvo675dcd"
    base_url = "https://geocode.maps.co/search"
    params = {
        "q": address, "api_key": api_key }
    response = requests.get(base_url, params=params)
    
    respjson = response.json()
    result = respjson[0]
    latitude = float(result["lat"])
    longitude = float(result["lon"])
    return (latitude, longitude)

# Converts right ascension and declination into degrees
def conv_rasc_decl(rightascension, declination):
    ra_split = rightascension.split()
    hours = float(ra_split[0].replace("h", ""))
    minutes = float(ra_split[1].replace("m", ""))
    seconds = float(ra_split[2].replace("s", ""))
    radegrees = hours*15 + minutes*(15/60) + seconds*(15/3600)
    # ^ Convert right ascension
   
    sign = 1
    if declination.strip()[0] == '-' or declination.strip()[0] =='−':
        sign = -1

    declination = declination.strip().lstrip("+-")
    dec_split = declination.split()
    degrees = float(dec_split[0].replace("°", ""))
    arcminutes = float(dec_split[1].replace("′", ""))
    arcseconds = float(dec_split[2].replace("″", ""))
    decdegrees = sign*(degrees + arcminutes/60 + arcseconds/3600)
    # ^ Convert declination
    
    return radegrees, decdegrees

def get_days_since_J2000(caldate, UTC): #Create function with date and UTC as paramaters
    yyyyddmm = caldate.strftime("%Y-%m-%d") # astropy requires this formatting
    time_new_str = (f"{yyyyddmm} {UTC}") #adds into to string in order
    J2000 = 2451545.0 #J2000 is the julian day that the year 2000 was
    yyyymmdd_utc = Time(time_new_str, scale="utc")
    time_new = yyyymmdd_utc.jd -J2000 #.jd makes the the utc date time into julian days
    return(time_new)

def get_siderial_time(caldate, UTC, lon):
    jd2000 = get_days_since_J2000(caldate,UTC) #get days since jd2000
    UTC =  datetime.strptime(UTC, '%H:%M')
    UTC = UTC.hour + (UTC.minute/60) #get decimal hours
    LST = 100.46 + 0.985647 * jd2000 + lon + 15*UTC
    while LST < 0: #in order to convert to degrees while LST is less than zero add 360
        LST = LST + 360
    while LST > 360: #in order to convert to degrees while LST is greater than 360 minus 360
        LST = LST - 360
    return LST

def hour_angle(LST, RA): #local siderial time and right ascension angle
    HA = LST - RA
    while HA < 0:
        HA = HA + 360 #if HA is less than zero add 360 to make it in degrees
    return HA

def az_alt_calc(dec, ha, lat):
    #calculating alt
    raddec = radians(dec)
    radha = radians(ha)
    radlat = radians(lat)
    
    #finding the sine of the altitude using this formula
    sine_of_alt = (sin(raddec)*sin(radlat))+(cos(raddec)*cos(radlat)*cos(radha))
    #"undo" the sine by taking the arcsine (inverse of sine)
    alt = asin(sine_of_alt)

    #calculating az

    #finding the cosine of "a" using this formula

    cosine_of_a = (sin(raddec)-(sin(alt)*sin(radlat)))/(cos(alt)*cos(radlat))
    
    #"undo" the cosine by taking the arccosine (inverse of cosine)
    try:
        a = degrees(acos(cosine_of_a))
        
    except ValueError:
        a = 0

    #if sine of the hour angle is negative, then az = a
    if sin(radha) < 0:
        az = a
    #otherwise,
    else:
        az = 360-a

    if dec - lat > 90 or dec - lat < -90:
        return 0, 0
    else:
        return alt, az

def cartesian_conversion(alt, az):
    #equivalent variable names in spherical coordinates
    if az > 0 and az <= 90:
        theta = 90-az
    elif az > 90 and az <= 180:
        theta = 180-(az-270)
    elif az > 180 and az <= 270:
        theta = 270-(az-180)
    elif az > 270 and az <= 360:
        theta = 360-(az-90)
    elif az == 0 or az == 360:
        return (100,100)

    phi = pi/2-alt

    #converting spherical coordinates to cartesian coordinates
    x = cos(radians(theta))*sin(phi)
    y = sin(radians(theta))*sin(phi)
    
    return (x,y)
