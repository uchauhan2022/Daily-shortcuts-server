import requests
import pandas as pd
from io import StringIO
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from pyvirtualdisplay import Display, abstractdisplay
from config import Config
from constants import Constants
import platform
import logging
import exception
import sys

log = logging.getLogger("server.helper")


def buildCookieDict(cookies):
    """
    Converts cookies into a dictionary of name : value

    Args:
        cookies: login cookies

    Returns:
        Dict: cookies in a dict
    """
    cookie = ""
    space = 1
    for c in cookies:
        name = c["name"]
        value = c["value"]
        temp = name + "=" + value + ";"
        if space == 1:
            space = 0
            cookie = temp
            continue
        cookie = cookie + " " + temp
    return cookie


def getWebDriver():
    """
    Checks for platform and returns (actual/virtual) web driver

    Returns:
        webdriver: chrome web driver

    Raises:
        WebDriverCreationError
    """
    try:
        if platform.system() != "Darwin":
            display = Display(visible=False, size=(800, 600))
            display.start()
        return webdriver.Chrome()
    except abstractdisplay.XStartError:
        log.exception("Failed to create web driver, possible reason : OSX")
        raise exception.WebDriverCreationError
    except:
        log.exception("Failed to create web driver")
        raise exception.WebDriverCreationError


def getCookie(username, password):
    """
    Gets a login cookie from energia website

    Args:
        username: energia username
        password: energia password

    Return:
        Dict: dict containing login cookie

    Raises:
        WebDriverRuntimeError
    """
    try:
        # Gets web driver
        driver = getWebDriver()
        log.info("Webdriver created.")
        # Navigate to the login page
        driver.get(Constants.ENERGIA_URL_HOME)

        # Find the login form elements
        username_field = driver.find_element("id", "login-username")
        password_field = driver.find_element("id", "login-password")
        login_button = driver.find_element("id", "submitButton")

        # Enter the necessary information into the form
        username_field.send_keys(username)
        password_field.send_keys(password)

        # Submit button
        driver.find_element("id", "onetrust-accept-btn-handler").click()
        sleep(5)
        login_button.click()
        sleep(10)
        cookies = driver.get_cookies()
        log.info("Cookies received.")
        driver.close()
        return buildCookieDict(cookies)
    except:
        log.exception("Failed to get cookie")
        raise exception.WebDriverRuntimeError


def getLatestReading(df):
    """
    Gets the latest date of reading in the interval of dates

    Args:
        df: dataframe of usage history

    Returns:
        String: Lastest date with reading
    """
    latestDay = ""
    for index, row in df.iterrows():
        if row["Total"] > 0:
            latestDay = index
    return latestDay


def calculateRequiredMetrics(responseData):
    """
    Does the required calculation on csv

    Args:
        responseData: csv data of usage history

    Returns:
        Dict: metrics required

    Raises:
        DataframeCreationError
    """
    try:
        data = responseData.split("\r\n")
        data.remove(data[0])
        csvStringIO = StringIO("\n".join(data))
        df = pd.read_csv(csvStringIO, sep=",", index_col=0)
        df["Total"] = df.sum(axis=1)
        df["Day"] = df.iloc[:, 16:34].sum(axis=1) + df.iloc[:, 38:46].sum(axis=1)
        df["Night"] = df.iloc[:, 0:16].sum(axis=1) + df.iloc[:, 46:48].sum(axis=1)
        df["Peak"] = df.iloc[:, 34:38].sum(axis=1)
        log.info("Dataframe created successfully.")
        day_units = df.sum()[49]
        night_units = df.sum()[50]
        peak_units = df.sum()[51]
        total_units = df.sum()[48]
        latest_reading = getLatestReading(df)
        bill = (
            day_units * 0.4664
            + night_units * 0.2497
            + peak_units * 0.4887
            + len(df.index) * 0.59
        ) * 1.09
        metrics = {
            "Total Units": total_units,
            "Day Units": day_units,
            "Night Units": night_units,
            "Peak Units": peak_units,
            "Expected Bill": bill,
            "Latest Reading": latest_reading,
        }
        return metrics
    except:
        log.exception("Error while creating dataframe")
        raise exception.DataframeCreationError


def getElectrictyUsageInfo(startDate, endDate):
    """
    Gets half hourly usage for the specified interval
    Args:
        startDate: start date
        endDate: end date

    Return:
        Dict: dict containing metrics

    Raises:
        GetElectricityUsageRequestError
    """
    try:
        # Get login cookie
        cookie = getCookie(Config.USERNAME_ENERGIA, Config.PASSWORD_ENERGIA)
        # Request builder
        url = Constants.ENERGIA_URL
        headers = Constants.ENERGIA_HEADERS
        headers["Cookie"] = cookie
        params = {"StartDate": startDate, "EndDate": endDate, "Mprn": Config.MPRN_HASH}
        response = requests.request("GET", url, headers=headers, params=params)
        metrics = calculateRequiredMetrics(response.text)
        return metrics
    except requests.exceptions.RequestException:
        log.exception("Get half hourly usage request failed")
        return exception.GetElectricityUsageRequestError


def createMessageFromMetrics(metrics):
    """
    Creates message dict from metrics

    Args:
        metrics: Dict with message data

    Returns:
        Dict: title and message strings
    """
    data = {}
    data["title"] = "Expected bill is €{:.2f}".format(metrics["Expected Bill"])
    data[
        "message"
    ] = "Latest Reading: {}\nTotal Units: {:.2f}\nNight Units: {:.2f}\nDay Units: {:.2f}\nPeak Units: {:.2f}".format(
        metrics["Latest Reading"],
        metrics["Total Units"],
        metrics["Night Units"],
        metrics["Day Units"],
        metrics["Peak Units"],
    )
    return data


def sendNotification(title, message):
    """
    Sends pushover notification to devices

    Args:
        title: title of msg
        message: msg string

    Raises:
        PushoverSendNotificationError
    """
    try:
        url = Constants.PUSHOVER_URL
        payload = {
            "token": Config.PUSHOVER_TOKEN,
            "user": Config.PUSHOVER_KEY,
            "title": title,
            "message": message,
        }
        log.info("Sending pushover notification with title: {}.".format(title))
        response = requests.post(url=url, data=payload)
        if response.status_code != 200:
            log.error(
                "send pushover notification request failed with status code : {}".format(
                    response.status_code
                )
            )
            raise exception.PushoverSendNotificationError
        return response
    except requests.exceptions.RequestException as e:
        log.exception("Send pushover notification request failed")
        raise exception.PushoverSendNotificationError(e)


def getElectricityBillThreaded(startDate, endDate):
    """
    fetches electricity bill data and sends pushover notificaton

    Args:
        startDate: start date of the interval
        endDate: end date of the interval

    Raises:
        GetElectricityBillError
    """
    try:
        metrics = getElectrictyUsageInfo(startDate=startDate, endDate=endDate)
        data = createMessageFromMetrics(metrics=metrics)
        sendNotification(title=data["title"], message=data["message"])
    except:
        log.error("getElectricityBill Failed")
        sendNotification(
            title="500 - Internal Server Error", message="Some error, check logs"
        )
        raise exception.GetElectricityBillError()
