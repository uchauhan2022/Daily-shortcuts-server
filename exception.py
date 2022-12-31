"""Get Electrcity Bill Exceptions"""


class GetElectricityBillError(Exception):
    """Base Get Electricity Bill Error"""

    status_code = 500


class GetCookieError(GetElectricityBillError):
    """Get Cookie Error"""


class DataframeCreationError(GetElectricityBillError):
    """Error while creating dataframe from response"""


class GetElectricityUsageRequestError(GetElectricityBillError):
    """Error while requesting electricity usage"""


"""Get Electrcity Bill Exceptions"""


class PushoverSendNotificationError(Exception):
    """Failed to send notification"""


"""WebDriver Exceptions"""


class WebDriverError(Exception):
    """Base Web driver error"""


class WebDriverCreationError(WebDriverError):
    """Web driver creation error"""


class WebDriverRuntimeError(WebDriverError):
    """Web driver run time error"""
