from typing import Any, Dict, List, Optional


class ProxyConfig:

    def __init__(
        self,
        server: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        bypass: Optional[str] = None,
    ):
        self.server = server
        self.username = username
        self.password = password
        self.bypass = bypass
    
    def model_dump(self) -> Dict[str, Any]:

        result = {}
        if self.server:
            result["server"] = self.server
        if self.username:
            result["username"] = self.username
        if self.password:
            result["password"] = self.password
        if self.bypass:
            result["bypass"] = self.bypass
        return result


class BrowserConfig:
    
    def __init__(
        self,
        headless: bool = False,
        proxy: Optional[ProxyConfig] = None,
        browser_class: str = "chromium",
    ):
        self.headless = headless
        self.proxy = proxy
        self.browser_class = browser_class


class HttpCredentials:
    
    def __init__(
        self,
        username: str,
        password: str,
        origin: Optional[str] = None,
    ):
        self.username = username
        self.password = password
        self.origin = origin


class Geolocation:
    
    def __init__(
        self,
        latitude: float,
        longitude: float,
        accuracy: Optional[float] = None,
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.accuracy = accuracy


class BrowserContextConfig:
    
    def __init__(
        self,
        user_agent: Optional[str] = None,
        locale: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        geolocation: Optional[Geolocation] = None,
        timezone_id: Optional[str] = None,
        http_credentials: Optional[HttpCredentials] = None,
        is_mobile: Optional[bool] = None,
        has_touch: Optional[bool] = None,
        save_recording_path: Optional[str] = None,
        save_har_path: Optional[str] = None,
        no_viewport: bool = False,
        window_width: int = 1280,
        window_height: int = 720,
        maximum_wait_page_load_time: float = 90.0,
        cookies_file: Optional[str] = None,
        save_downloads_path: Optional[str] = None,
    ):
        self.user_agent = user_agent
        self.locale = locale
        self.permissions = permissions
        self.geolocation = geolocation
        self.timezone_id = timezone_id
        self.http_credentials = http_credentials
        self.is_mobile = is_mobile
        self.has_touch = has_touch
        self.save_recording_path = save_recording_path
        self.save_har_path = save_har_path
        self.no_viewport = no_viewport
        self.window_width = window_width
        self.window_height = window_height
        self.maximum_wait_page_load_time = maximum_wait_page_load_time
        self.cookies_file = cookies_file
        self.save_downloads_path = save_downloads_path
