import requests
import pandas as pd
from io import StringIO
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from pyvirtualdisplay import Display
from config import Config
from constants import Constants
import platform

def buildCookieDict(cookies):
    '''
    Converts cookies into a dictionary of name:value
    '''
    cookie = ""
    space = 1
    for c in cookies:
        name = c['name']
        value = c['value']
        temp = name + "=" + value + ";"
        if space == 1:
            space = 0
            cookie = temp
            continue
        cookie = cookie + " " + temp 
    return cookie

def getCookie(username, password):
    '''
    Gets a login cookie from energia website
    '''
    # Set up the webdriver instance
    if platform.system()!="Darwin":
        display = Display(visible=False, size=(800, 600))
        display.start()
    driver = webdriver.Chrome()

    # Navigate to the login page
    driver.get("https://energyonline.energia.ie/")

    # Find the login form elements
    username_field = driver.find_element("id","login-username")
    password_field = driver.find_element("id","login-password")
    login_button = driver.find_element("id","submitButton")

    # Enter the necessary information into the form
    username_field.send_keys(username)
    password_field.send_keys(password)

    # Submit button
    driver.find_element("id","onetrust-accept-btn-handler").click()
    sleep(5)
    login_button.click()
    sleep(10)
    cookies = driver.get_cookies()
    driver.close()

    return buildCookieDict(cookies)

def getLatestReading(df):
    '''
    Gets the latest date of reading in the interval of dates
    '''
    latestDay = ""
    for index, row in df.iterrows():
        if(row["Total"]>0):
            latestDay=index
    return latestDay

def calculateRequiredMetrics(responseData):
    data = responseData.split('\r\n')
    data.remove(data[0])
    csvStringIO = StringIO("\n".join(data))
    df = pd.read_csv(csvStringIO, sep=",",index_col=0)
    df['Total']=df.sum(axis=1)
    df['Day']=df.iloc[:,16:34].sum(axis=1)+df.iloc[:,38:46].sum(axis=1)
    df['Night']=df.iloc[:,0:16].sum(axis=1)+df.iloc[:,46:48].sum(axis=1)
    df['Peak']=df.iloc[:,34:38].sum(axis=1)
    day_units = df.sum()[49]
    night_units = df.sum()[50]
    peak_units = df.sum()[51]
    total_units = df.sum()[48]
    latest_reading = getLatestReading(df)
    bill = (day_units*0.4664 + night_units*0.2497 + peak_units*0.4887 + len(df.index)*0.59)*1.09
    metrics = {
        'Total Units' : total_units,
        'Day Units' : day_units,
        'Night Units' : night_units,
        'Peak Units' : peak_units,
        'Expected Bill' : bill,
        'Latest Reading' : latest_reading
    }
    return metrics


def getElectrictyUsageInfo(startDate,endDate):
    
    # Get login cookie
    cookie = getCookie(Config.USERNAME_ENERGIA,Config.PASSWORD_ENERGIA)
    # Request builder
    url = Constants.ENERGIA_URL
    headers = Constants.ENERGIA_HEADERS
    headers['Cookie'] = cookie
    params = {
        'StartDate' : startDate,
        'EndDate' : endDate,
        'Mprn' : Constants.MPRN_HASH
    }
    response = requests.request("GET", url, headers=headers, params=params)
    metrics = calculateRequiredMetrics(response.text)
    
    return metrics
    
