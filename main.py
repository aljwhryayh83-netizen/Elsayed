#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, date, timedelta
import json
import os
import random
import sys
import time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
import requests
import threading
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TO = 30
BASE_URL = "https://spincoin.appmobile.top"
SIGNUP_FAUCET_URL = f"{BASE_URL}/api/v1/users/signupFaucetPay"
GRAPHQL_URL = f"{BASE_URL}/graphql"
AD_BASE_URL = "https://googleads.g.doubleclick.net/mads/gma"

ANDROID_VERSIONS = ["11", "12", "13", "14"]
DEVICE_MODELS = [
    "SM-G991B", "SM-A525F", "SM-M315F", "Pixel 6", "Pixel 7",
    "Xiaomi M2101K6G", "Redmi Note 10", "Infinix X6816", "SM-T505N"
]
CHROME_VERSIONS = ["118.0.5993.80", "120.0.6099.144", "122.0.6261.64", "125.0.6422.113", "130.0.6723.102"]

# ملفات التخزين
WITHDRAW_DATA_FILE = "withdraw_data.json"
SCHEDULE_DATA_FILE = "schedule_data.json"
CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default = {
            "telegram_bot_token": "YOUR_BOT_TOKEN_HERE",
            "update_interval": 5,
            "min_withdraw": 55000,
            "max_withdraw": 60000
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(default, f, indent=2)
        return default
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "telegram_bot_token": "YOUR_BOT_TOKEN_HERE",
            "update_interval": 5,
            "min_withdraw": 55000,
            "max_withdraw": 60000
        }

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def load_withdraw_data():
    if not os.path.exists(WITHDRAW_DATA_FILE):
        return {}
    try:
        with open(WITHDRAW_DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_withdraw_data(data):
    with open(WITHDRAW_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_schedule_data():
    if not os.path.exists(SCHEDULE_DATA_FILE):
        return {}
    try:
        with open(SCHEDULE_DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_schedule_data(data):
    with open(SCHEDULE_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_proxies(proxy_file="proxy.txt"):
    proxies = []
    if not os.path.exists(proxy_file):
        return proxies
    with open(proxy_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if not line.startswith("http://") and not line.startswith("https://") and not line.startswith("socks"):
                    line = f"http://{line}"
                proxies.append(line)
    return proxies

def wait_for_proxy():
    while True:
        proxies = load_proxies("proxy.txt")
        if proxies:
            return proxies[0]
        print("⚠️ لا يوجد بروكسي! في انتظار إضافة بروكسي...")
        time.sleep(5)

def get_ip(proxy):
    if not proxy:
        proxy = wait_for_proxy()
    
    while True:
        try:
            url = "https://api.ipify.org?format=json"
            resp = requests.get(url, proxies={"http": proxy, "https": proxy}, timeout=10)
            if resp.status_code == 200:
                ip = resp.json().get("ip", "Unknown")
                if ip and ip != "Unknown":
                    print(f"✅ تم جلب IP: {ip} من البروكسي: {proxy}")
                    return ip
        except Exception as e:
            print(f"⚠️ محاولة فاشلة لجلب IP من {proxy}: {str(e)[:50]}")
        
        try:
            url = "https://httpbin.org/ip"
            resp = requests.get(url, proxies={"http": proxy, "https": proxy}, timeout=10)
            if resp.status_code == 200:
                ip = resp.json().get("origin", "Unknown")
                if ip and ip != "Unknown":
                    print(f"✅ تم جلب IP: {ip} من البروكسي: {proxy}")
                    return ip
        except Exception as e:
            print(f"⚠️ محاولة فاشلة لجلب IP من {proxy}: {str(e)[:50]}")
        
        print(f"⏳ البروكسي {proxy} لا يعمل، في انتظار بروكسي جديد...")
        proxy = wait_for_proxy()

def generate_random_fingerprint():
    android_ver = random.choice(ANDROID_VERSIONS)
    device_model = random.choice(DEVICE_MODELS)
    chrome_ver = random.choice(CHROME_VERSIONS)
    
    user_agent = (
        f"Mozilla/5.0 (Linux; Android {android_ver}; {device_model} Build/SP1A.210812.016; wv) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{chrome_ver} Safari/537.36"
    )
    
    FARM_ADS_PARAMS = {
        "submodel": device_model,
        "adid_p": "1",
        "format": "interstitial_mb",
        "ini_pn": "com.android.vending",
        "ins_pn": "com.android.vending",
        "omid_v": "a.1.5.2-google_20241009",
        "dv": "261710500",
        "ev": "24.6.0",
        "gl": "US",
        "hl": "en",
        "js": f"afma-sdk-a-v261710999.{random.randint(200000000, 299999999)}.1",
        "kw": "clothing,fashion",
        "lv": "253410000",
        "ms": "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_", k=250)),
        "mv": "85273430.com.android.vending",
        "lft": "1",
        "tsi": str(random.randint(1000, 9999)),
        "vnm": "1.1.9",
        "plbs": "0",
        "plcs": "0",
        "tfat": "0",
        "u_sd": str(random.choice([1.5, 2.0, 2.5, 3.0])),
        "request_id": str(random.randint(1000000000, 9999999999)),
        "target_api": "36",
        "carrier": "60204",
        "request_agent": "rn-invertase-16.0.0",
        "seq_num": "1",
        "eid": "318500618,318486317,318491267,318509511,318515546,318518927",
        "gdpr": "1",
        "gdpr_consent": "CQpWQEAQpWQEAEsACBENCtFgAAAAAEPgAAKIAAAYNQD2F242EKEEGCuQXYIIACugSAAxY",
        "addtl_consent": "2~~dv.61.70.89.122.144.161.196.230.385.442.445",
        "guci": "0.0.0.0.0.0.0.128",
        "sdk_apis": "7,8",
        "omid_p": f"Google/afma-sdk-a-v261710999.{random.randint(200000000, 299999999)}.1",
        "cap": "m",
        "u_w": str(random.choice([800, 1080, 1440])),
        "u_h": str(random.choice([1286, 1920, 2340])),
        "msid": "com.spincoin.appmobile.top",
        "an": "19.android.com.spincoin.appmobile.top",
        "dvoln": "0",
        "u_audio": "3",
        "net": "wi",
        "u_so": "p",
        "rbv": "1",
        "loeid": "44766145,318502621",
        "preqs_in_session": "5",
        "preqs": "0",
        "time_in_session": str(random.randint(100000, 500000)),
        "pcc": "0",
        "output": "html",
        "region": "mobile_app",
        "u_tz": "180",
        "client": "ca-app-pub-5674874137587223",
        "slotname": "2490768366",
        "kw_type": "broad",
        "gsb": "wi",
        "lite": "0",
        "app_wp_code": "ca-app-pub-5674874137587223",
        "app_code": "6465111319",
        "num_ads": "1",
        "vpt": "8",
        "vfmt": "18",
        "vst": "0",
        "sdkv": f"o.261710999.{random.randint(200000000, 299999999)}.1",
        "sdmax": "0",
        "dmax": "1",
        "sdki": "3c4d",
        "stbg": "1",
        "bisch": "false",
        "blev": "0.39",
        "canm": "true",
        "_mv": "85273430.com.android.vending",
        "heap_free": str(random.randint(10000000, 20000000)),
        "heap_max": "201326592",
        "heap_total": "50331648",
        "wv_count": "1",
        "rdps": "15500",
        "_cv": "263131029",
        "is_lat": "false",
        "blob": "ABPQqLG39MpNSsghQ3u8R7-2uCNjTRqcV9-raiex72QG846Wd7qoOwCsiVle9S5ZOZjZ",
        "capsbf": "7FFFFFEE",
        "jsv": "sdk_20190107_RC02-production-sdk_20260813_RC00",
    }
    
    return user_agent, FARM_ADS_PARAMS

def save_proxies(proxies, proxy_file="proxy.txt"):
    with open(proxy_file, "w") as f:
        for proxy in proxies:
            proxy = proxy.replace("http://", "").replace("https://", "")
            f.write(f"{proxy}\n")

def load_accounts(account_file="email.txt"):
    if not os.path.exists(account_file):
        return []
    with open(account_file, "r") as f:
        return [line.strip() for line in f if line.strip()]

def save_accounts(accounts, account_file="email.txt"):
    with open(account_file, "w") as f:
        for acc in accounts:
            f.write(f"{acc}\n")

class AccountWorker:
    def __init__(self, email, proxy=None, index=0, bot_token=None, chat_id=None, withdraw_date=None, min_limit=55000, max_limit=60000):
        self.email = email
        self.proxy = proxy
        self.index = index
        self.token = None
        self.userid = None
        self.balance = 0
        self.credits = 0
        self.user_db_id = None
        self.headers_auth = {}
        self.running = True
        self.stopped = False
        self.fingerprint_ua, self.farm_ads_params = generate_random_fingerprint()
        self.bot_token = bot_token
        self.chat_id = chat_id
        
        self.last_withdraw_date = withdraw_date
        self.trx_coin_id = None
        self.stats = {"spins": 0, "earned": 0, "ads": 0}
        self.is_withdrawing = False
        self.last_update = datetime.now()
        self.has_withdrawn_before = False
        
        while not self.proxy:
            proxies = load_proxies("proxy.txt")
            if proxies:
                self.proxy = proxies[self.index % len(proxies)]
            else:
                time.sleep(5)
        
        self.current_ip = get_ip(self.proxy)
        self.target_withdraw_limit = random.randint(min_limit, max_limit)
        
        self.schedule_data = load_schedule_data()
        self.work_duration = random.randint(180, 600)
        self.rest_duration = random.randint(180, 600)
        self.next_action_time = time.time()
        self.is_working = True
        
        if self.email in self.schedule_data:
            sched = self.schedule_data[self.email]
            self.work_duration = sched.get("work_duration", self.work_duration)
            self.rest_duration = sched.get("rest_duration", self.rest_duration)
            self.is_working = sched.get("is_working", True)
            self.next_action_time = sched.get("next_action_time", time.time())
        
        if self.last_withdraw_date:
            current_date = self.get_network_date()
            if self.last_withdraw_date == current_date:
                self.stopped = True
            else:
                self.clear_withdraw_date()
    
    def save_schedule(self):
        self.schedule_data[self.email] = {
            "work_duration": self.work_duration,
            "rest_duration": self.rest_duration,
            "is_working": self.is_working,
            "next_action_time": self.next_action_time,
            "last_update": datetime.now().isoformat()
        }
        save_schedule_data(self.schedule_data)
    
    def update_withdraw_date(self, new_date):
        withdraw_data = load_withdraw_data()
        if self.email in withdraw_data:
            withdraw_data[self.email]["last_withdraw_date"] = new_date.strftime("%Y-%m-%d")
            withdraw_data[self.email]["balance"] = self.balance
            withdraw_data[self.email]["target"] = self.target_withdraw_limit
            withdraw_data[self.email]["updated_at"] = datetime.now().isoformat()
        else:
            withdraw_data[self.email] = {
                "last_withdraw_date": new_date.strftime("%Y-%m-%d"),
                "balance": self.balance,
                "target": self.target_withdraw_limit,
                "first_withdraw": True,
                "updated_at": datetime.now().isoformat()
            }
            self.has_withdrawn_before = True
        
        save_withdraw_data(withdraw_data)
        self.last_withdraw_date = new_date
    
    def clear_withdraw_date(self):
        withdraw_data = load_withdraw_data()
        if self.email in withdraw_data:
            del withdraw_data[self.email]
            save_withdraw_data(withdraw_data)
            self.last_withdraw_date = None
    
    def send_notification(self, message):
        if self.bot_token and self.chat_id:
            try:
                def send():
                    url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                    data = {
                        "chat_id": self.chat_id,
                        "text": message,
                        "parse_mode": "HTML"
                    }
                    try:
                        requests.post(url, json=data, timeout=10)
                    except:
                        pass
                threading.Thread(target=send, daemon=True).start()
            except:
                pass
    
    def fetch_latest_withdrawal_details(self, current_date_str):
        """جلب تفاصيل آخر عملية سحب فقط لعرضها في الإشعار"""
        try:
            payload = {
                "operationName": "getWithdraw",
                "variables": {
                    "offset": 0,
                    "limit": 1,
                    "filterStatus": 2,
                    "filterDate": "2026-01-01",
                    "filterDateLast": current_date_str,
                    "sigla": "ALL"
                },
                "query": """
                query getWithdraw($offset: Int, $limit: Int, $filterStatus: Int, $filterDate: String, $filterDateLast: String, $sigla: String) {
                  getWithdraw(
                    offset: $offset
                    limit: $limit
                    filterStatus: $filterStatus
                    filterDate: $filterDate
                    filterDateLast: $filterDateLast
                    sigla: $sigla
                  ) {
                    withdraw {
                      id
                      status
                      createAt
                      date_send
                      value
                      address
                      currency
                      type_wallet
                      hash
                      id_type_coin
                    }
                    total
                  }
                }
                """
            }
            res = self.req("POST", GRAPHQL_URL, headers=self.headers_auth, json=payload, timeout=15)
            if res and res.status_code == 200:
                res_data = res.json()
                get_withdraw = res_data.get("data", {}).get("getWithdraw", {})
                withdraws = get_withdraw.get("withdraw", [])
                
                if not withdraws:
                    return "--- لا توجد عمليات سحب مسجلة ---"
                
                item = withdraws[0]
                text = (
                    f"--- آخر عملية سحب ---\n"
                    f"  • القيمة (Value)  : {item.get('value')}\n"
                    f"  • العملة (Currency): {item.get('currency')}\n"
                    f"  • حالة الـ (Status): {item.get('status')}\n"
                    f"  • نوع المحفظة    : {item.get('type_wallet')}\n"
                    f"  • تاريخ الإنشاء   : {item.get('createAt')}\n"
                    f"----------------------------------------"
                )
                return text
        except Exception:
            pass
        return "[تعذر جلب تفاصيل السحب]"

    def fetch_all_withdrawals_grouped(self, current_date_str):
        """جلب عمليات السحب وتقسيمها لصفحات داخل رسالة واحدة متكاملة"""
        try:
            payload = {
                "operationName": "getWithdraw",
                "variables": {
                    "offset": 0,
                    "limit": 50,
                    "filterStatus": 2,
                    "filterDate": "2026-01-01",
                    "filterDateLast": current_date_str,
                    "sigla": "ALL"
                },
                "query": """
                query getWithdraw($offset: Int, $limit: Int, $filterStatus: Int, $filterDate: String, $filterDateLast: String, $sigla: String) {
                  getWithdraw(
                    offset: $offset
                    limit: $limit
                    filterStatus: $filterStatus
                    filterDate: $filterDate
                    filterDateLast: $filterDateLast
                    sigla: $sigla
                  ) {
                    withdraw {
                      id
                      status
                      createAt
                      date_send
                      value
                      address
                      currency
                      type_wallet
                      hash
                      id_type_coin
                    }
                    total
                  }
                }
                """
            }
            res = self.req("POST", GRAPHQL_URL, headers=self.headers_auth, json=payload, timeout=15)
            if res and res.status_code == 200:
                res_data = res.json()
                get_withdraw = res_data.get("data", {}).get("getWithdraw", {})
                total = get_withdraw.get("total", 0)
                withdraws = get_withdraw.get("withdraw", [])
                
                if not withdraws:
                    return [f"[*] Fetching up to date: {current_date_str}\n\n[*] Total Withdrawals Found: 0\n--- لا توجد عمليات سحب مسجلة ---"]
                
                items_per_page = 5
                pages = []
                for i in range(0, len(withdraws), items_per_page):
                    chunk = withdraws[i:i + items_per_page]
                    page_text = f"[*] Fetching up to date: {current_date_str}\n\n[*] Total Withdrawals Found: {total}\n"
                    page_text += f"📄 الصفحة {(i // items_per_page) + 1} من {((len(withdraws) - 1) // items_per_page) + 1}\n"
                    page_text += "========================================\n"
                    
                    for idx, item in enumerate(chunk, i + 1):
                        page_text += (
                            f"--- عملية السحب رقم {idx} ---\n"
                            f"  • القيمة (Value)  : {item.get('value')}\n"
                            f"  • العملة (Currency): {item.get('currency')}\n"
                            f"  • حالة الـ (Status): {self.get_status_text(item.get('status'))}\n"
                            f"  • نوع المحفظة    : {item.get('type_wallet')}\n"
                            f"  • تاريخ الإنشاء   : {item.get('createAt')}\n"
                            f"----------------------------------------\n"
                        )
                    pages.append(page_text)
                return pages
        except Exception:
            pass
        return [f"[*] Fetching up to date: {current_date_str}\n\n[تعذر جلب حالات السحب]"]
    
    def get_status_text(self, status_code):
        """تحويل رمز الحالة إلى نص مفهوم"""
        status_map = {
            '1': '✅ ناجح',
            '2': '⏳ قيد المعالجة',
            '3': '❌ فشل',
            '4': '⏸️ معلق'
        }
        return status_map.get(str(status_code), f'❓ غير معروف ({status_code})')

    def req(self, method, url, **kw):
        while not self.proxy:
            proxies = load_proxies("proxy.txt")
            if proxies:
                self.proxy = proxies[self.index % len(proxies)]
                self.current_ip = get_ip(self.proxy)
            else:
                time.sleep(5)
        
        kw.setdefault("timeout", TO)
        kw["proxies"] = {"http": self.proxy, "https": self.proxy}
        
        for attempt in range(3):
            try:
                return requests.request(method, url, **kw)
            except (requests.Timeout, requests.ConnectionError):
                if attempt < 2:
                    time.sleep(3)
                else:
                    proxies = load_proxies("proxy.txt")
                    if proxies:
                        self.proxy = proxies[(self.index + 1) % len(proxies)]
                        self.current_ip = get_ip(self.proxy)
                    else:
                        time.sleep(5)
        return None
    
    def get_network_date(self):
        while not self.proxy:
            proxies = load_proxies("proxy.txt")
            if proxies:
                self.proxy = proxies[self.index % len(proxies)]
            else:
                time.sleep(5)
        
        try:
            res = requests.get("http://worldtimeapi.org/api/ip", proxies={"http": self.proxy, "https": self.proxy}, timeout=5)
            if res.status_code == 200:
                data = res.json()
                datetime_str = data.get("datetime", "")
                if datetime_str:
                    return datetime.strptime(datetime_str.split("T")[0], "%Y-%m-%d").date()
        except Exception:
            pass
        return date.today()
    
    def execute_initial_sequence(self):
        okhttp_headers = {
            "User-Agent": "okhttp/4.12.0",
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {self.token}"
        }
        self.req("GET", f"{BASE_URL}/api/v1/users/getClick", headers=okhttp_headers)
        self.req("GET", f"{BASE_URL}/api/v1/checkVersion", headers=okhttp_headers)
        self.req("GET", f"{BASE_URL}/api/v1/users/getTimeClick", headers=okhttp_headers)
        self.req("GET", f"{BASE_URL}/mobile/{self.userid}", headers={"User-Agent": self.fingerprint_ua})
        self.req("GET", f"{BASE_URL}/dashboard", headers={"User-Agent": self.fingerprint_ua, "Authorization": f"Bearer {self.token}"})
    
    def do_login(self):
        while not self.proxy:
            proxies = load_proxies("proxy.txt")
            if proxies:
                self.proxy = proxies[self.index % len(proxies)]
                self.current_ip = get_ip(self.proxy)
            else:
                time.sleep(5)
        
        try:
            res = self.req(
                "POST",
                SIGNUP_FAUCET_URL,
                data=json.dumps({"email": self.email, "up": True}),
                headers={
                    "User-Agent": "okhttp/4.12.0",
                    "Accept": "application/json, text/plain, */*",
                    "Content-Type": "application/json",
                },
            )
            if not res:
                return self.do_login()
            
            data = res.json()
            user_data = data.get("data", {}).get("user")
            if not user_data:
                return self.do_login()
            
            self.userid = user_data.get("_id")
            
            graphql_query = {
                "operationName": "register",
                "variables": {"input": {"username": "username", "email": self.userid, "password": "123", "ref": "", "token_recaptcha": "token_recaptcha", "last_url": "no-refe"}},
                "query": "mutation register($input: UserInput) {\n  register(input: $input) {\n    token\n    status\n    refresh_token\n    __typename\n  }\n}"
            }
            res_reg = self.req("POST", GRAPHQL_URL, json=graphql_query, headers={"Content-Type": "application/json"})
            reg_json = res_reg.json()
            self.token = reg_json["data"]["register"]["token"]
            
            self.headers_auth = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.token}",
                "user-agent": self.fingerprint_ua
            }
            return True
        except Exception:
            time.sleep(5)
            return self.do_login()
    
    def trigger_ad(self):
        resp = self.req("GET", AD_BASE_URL, params=self.farm_ads_params, headers={"User-Agent": self.fingerprint_ua})
        if not resp:
            return
        try:
            json_data = resp.json()
            nets = json_data.get("ad_networks", [])
            for net in nets:
                for vid in net.get("video_reward_urls", []):
                    p = urlparse(vid)
                    qs = parse_qs(p.query, keep_blank_values=True)
                    qs["rwd_userid"] = [str(self.userid)]
                    new = p._replace(query=urlencode(qs, doseq=True))
                    final_url = urlunparse(new)
                    self.req("GET", final_url, headers={"User-Agent": self.fingerprint_ua})
                    self.stats["ads"] += 1
        except Exception:
            pass
    
    def get_trx_coin_id(self):
        query = {
            "operationName": "getTypeCoinAll",
            "variables": {},
            "query": "query getTypeCoinAll {\n  getTypeCoinAll {\n    id\n    sigla\n  }\n}"
        }
        try:
            res = self.req("POST", GRAPHQL_URL, headers=self.headers_auth, json=query)
            coins = res.json()["data"]["getTypeCoinAll"]
            for coin in coins:
                if coin.get("sigla", "").lower() == "trx":
                    return coin.get("id")
        except Exception:
            pass
        return "66bd3ede56df3c77675b869d"
    
    def run(self):
        while not self.proxy:
            proxies = load_proxies("proxy.txt")
            if proxies:
                self.proxy = proxies[self.index % len(proxies)]
                self.current_ip = get_ip(self.proxy)
            else:
                time.sleep(5)
        
        if self.stopped:
            while self.running and self.stopped:
                time.sleep(60)
                current_date = self.get_network_date()
                if self.last_withdraw_date and self.last_withdraw_date < current_date:
                    self.clear_withdraw_date()
                    self.stopped = False
                    msg = (
                        f"🔄 <b>تم إعادة تشغيل الحساب!</b>\n"
                        f"━━━━━━━━━━━━━━━━━\n"
                        f"📧 الحساب: {self.email}\n"
                        f"📅 التاريخ: {current_date.strftime('%Y-%m-%d')}\n"
                        f"🟢 الحالة: يعمل الآن"
                    )
                    self.send_notification(msg)
                    break
            if not self.running:
                return
        
        if not self.do_login():
            self.running = False
            return
        
        self.execute_initial_sequence()
        self.trx_coin_id = self.get_trx_coin_id()
        
        get_user_query = {
            "operationName": "getUser",
            "variables": {},
            "query": "query getUser {\n  getUser {\n    id\n    balance\n    credits\n  }\n}"
        }
        
        earn_query = {
            "operationName": "earnRollGame",
            "variables": {"token": "token_recaptcha"},
            "query": "mutation earnRollGame($token: String) {\n  earnRollGame(token: $token) {\n    user {\n      id\n      balance\n      credits\n    }\n  }\n}"
        }
        
        response_user = self.req("POST", GRAPHQL_URL, headers=self.headers_auth, json=get_user_query)
        try:
            result_user = response_user.json()
            self.credits = result_user["data"]["getUser"]["credits"]
            self.balance = result_user["data"]["getUser"]["balance"]
            self.user_db_id = result_user["data"]["getUser"]["id"]
        except Exception:
            self.credits = 0
            self.balance = 0
            self.user_db_id = self.userid
        
        self.save_schedule()
        
        while self.running:
            try:
                current_time = time.time()
                if current_time >= self.next_action_time:
                    self.is_working = not self.is_working
                    if self.is_working:
                        self.work_duration = random.randint(180, 600)
                        self.next_action_time = current_time + self.work_duration
                    else:
                        self.rest_duration = random.randint(180, 600)
                        self.next_action_time = current_time + self.rest_duration
                    self.save_schedule()
                
                if not self.is_working:
                    time.sleep(5)
                    continue
                
                current_date = self.get_network_date()
                
                if self.balance >= self.target_withdraw_limit:
                    self.is_withdrawing = True
                    withdraw_query = {
                        "operationName": "withdraw",
                        "variables": {
                            "input": {
                                "address": self.email,
                                "value": self.balance,
                                "token_recaptcha": "token_recaptcha",
                                "id": self.trx_coin_id,
                                "type_wallet": "FP"
                            }
                        },
                        "query": "mutation withdraw($input: WithdrawInput) {\n  withdraw(input: $input) {\n    id\n    status\n    createAt\n    date_send\n    value\n    address\n    currency\n    type_wallet\n    hash\n    __typename\n  }\n}"
                    }
                    
                    res_withdraw = self.req("POST", GRAPHQL_URL, headers=self.headers_auth, json=withdraw_query)
                    try:
                        withdraw_res_data = res_withdraw.json()
                        if "errors" not in withdraw_res_data:
                            self.update_withdraw_date(current_date)
                            self.stopped = True
                            self.is_withdrawing = False
                            
                            next_date = current_date + timedelta(days=1)
                            date_str = current_date.strftime('%Y-%m-%d')
                            
                            latest_withdrawal_str = self.fetch_latest_withdrawal_details(date_str)
                            
                            msg = (
                                f"💰 <b>✅ تم سحب الرصيد بنجاح!</b>\n"
                                f"━━━━━━━━━━━━━━━━━\n"
                                f"📧 الحساب: {self.email}\n"
                                f"💰 المبلغ: {self.balance:,.2f}\n"
                                f"📅 تاريخ السحب: {date_str}\n"
                                f"⏰ إعادة التشغيل: {next_date.strftime('%Y-%m-%d')} (بعد منتصف الليل)\n"
                                f"━━━━━━━━━━━━━━━━━\n"
                                f"🟡 الحالة: متوقف مؤقتاً\n\n"
                                f"{latest_withdrawal_str}"
                            )
                            self.send_notification(msg)
                    except Exception:
                        pass
                    
                    config = load_config()
                    self.target_withdraw_limit = random.randint(config.get("min_withdraw", 55000), config.get("max_withdraw", 60000))
                    time.sleep(2)
                    
                    while self.running and self.stopped:
                        time.sleep(60)
                        new_date = self.get_network_date()
                        if new_date > current_date:
                            self.stopped = False
                            self.clear_withdraw_date()
                            msg = (
                                f"🔄 <b>تم إعادة تشغيل الحساب!</b>\n"
                                f"━━━━━━━━━━━━━━━━━\n"
                                f"📧 الحساب: {self.email}\n"
                                f"📅 التاريخ: {new_date.strftime('%Y-%m-%d')}\n"
                                f"🟢 الحالة: يعمل الآن"
                            )
                            self.send_notification(msg)
                            break
                    continue
                
                if self.credits <= 0:
                    self.trigger_ad()
                    time.sleep(random.uniform(10, 20))
                    response_user = self.req("POST", GRAPHQL_URL, headers=self.headers_auth, json=get_user_query)
                    try:
                        result_user = response_user.json()
                        self.credits = result_user["data"]["getUser"]["credits"]
                        self.balance = result_user["data"]["getUser"]["balance"]
                        self.user_db_id = result_user["data"]["getUser"]["id"]
                    except Exception:
                        pass
                    continue
                
                response_earn = self.req("POST", GRAPHQL_URL, headers=self.headers_auth, json=earn_query)
                earn_result = response_earn.json()
                
                try:
                    user_obj = earn_result["data"]["earnRollGame"]["user"]
                    reward = user_obj.get("balance", 0) - self.balance
                    if reward > 0:
                        self.stats["earned"] += reward
                    self.stats["spins"] += 1
                    self.credits = user_obj["credits"]
                    self.balance = user_obj["balance"]
                    self.last_update = datetime.now()
                except Exception:
                    pass
                
                time.sleep(random.uniform(0.3, 0.7))
                
            except Exception:
                time.sleep(2)

class BotManager:
    def __init__(self):
        self.workers = []
        self.threads = []
        self.running = False
        self.bot_token = None
        self.update_interval = 5
        self.main_message_id = None
        self.dashboard_message_id = None
        self.chat_id = None
        self.current_view = "main"
        self.update_job = None
        self.is_updating = False
        self.delete_page = 0
        self.accounts_page = 0
        self.withdraw_status_page = 0
        self.items_per_page = 10
    
    def load_config(self):
        config = load_config()
        self.bot_token = config.get("telegram_bot_token")
        self.update_interval = config.get("update_interval", 5)
        return config
    
    def start_accounts(self):
        if self.running:
            return
        
        proxies = load_proxies("proxy.txt")
        if not proxies:
            while not load_proxies("proxy.txt"):
                time.sleep(5)
            proxies = load_proxies("proxy.txt")
        
        accounts = load_accounts("email.txt")
        if not accounts:
            return
        
        withdraw_data = load_withdraw_data()
        config = load_config()
        min_l = config.get("min_withdraw", 55000)
        max_l = config.get("max_withdraw", 60000)
        
        self.running = True
        self.workers = []
        self.threads = []
        
        for idx, email in enumerate(accounts):
            proxy = proxies[idx % len(proxies)]
            withdraw_date = None
            if email in withdraw_data:
                date_str = withdraw_data[email].get("last_withdraw_date", "")
                if date_str:
                    try:
                        withdraw_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except:
                        pass
            
            self._start_single_account(email, proxy, idx, withdraw_date, min_l, max_l)
            time.sleep(0.3)
    
    def _start_single_account(self, email, proxy=None, index=None, withdraw_date=None, min_l=55000, max_l=60000):
        if index is None:
            index = len(self.workers)
        
        if not proxy:
            proxies = load_proxies("proxy.txt")
            if not proxies:
                while not load_proxies("proxy.txt"):
                    time.sleep(5)
                proxies = load_proxies("proxy.txt")
            proxy = proxies[index % len(proxies)]
        
        for w in self.workers:
            if w.email == email:
                return False
        
        worker = AccountWorker(email, proxy, index, self.bot_token, self.chat_id, withdraw_date, min_l, max_l)
        self.workers.append(worker)
        t = threading.Thread(target=worker.run, daemon=True)
        t.start()
        self.threads.append(t)
        return True
    
    def start_new_account(self, email):
        proxies = load_proxies("proxy.txt")
        if not proxies:
            while not load_proxies("proxy.txt"):
                time.sleep(5)
            proxies = load_proxies("proxy.txt")
        
        proxy = proxies[len(self.workers) % len(proxies)]
        accounts = load_accounts("email.txt")
        if email not in accounts:
            accounts.append(email)
            save_accounts(accounts, "email.txt")
        
        withdraw_data = load_withdraw_data()
        withdraw_date = None
        if email in withdraw_data:
            date_str = withdraw_data[email].get("last_withdraw_date", "")
            if date_str:
                try:
                    withdraw_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except:
                    pass
        
        config = load_config()
        self.running = True
        return self._start_single_account(email, proxy, None, withdraw_date, config.get("min_withdraw", 55000), config.get("max_withdraw", 60000))
    
    def stop_accounts(self):
        self.running = False
        for w in self.workers:
            w.running = False
        for t in self.threads:
            t.join(timeout=3)
        self.workers = []
        self.threads = []
    
    def get_status(self):
        lines = []
        total_balance = 0
        active_count = 0
        
        for i, w in enumerate(self.workers):
            if w.running:
                active_count += 1
                total_balance += w.balance
                if w.stopped:
                    status_icon = "⏸️"
                elif not w.is_working:
                    status_icon = "🔄"
                else:
                    status_icon = "▶️"
                
                date_info = ""
                if w.last_withdraw_date:
                    date_info = f" | 📅{w.last_withdraw_date}"
                
                lines.append(
                    f"{i+1}. {w.email[:18]} | 💰{w.balance:,.0f} | 🎯{w.target_withdraw_limit}{date_info} | {status_icon}"
                )
        
        status_text = "\n".join(lines) if lines else "⚠️ لا يوجد حسابات نشطة"
        return {
            "total_accounts": len(self.workers),
            "active_accounts": active_count,
            "total_balance": total_balance,
            "details": status_text,
            "proxies_count": len(load_proxies())
        }
    
    def add_accounts(self, accounts_text):
        accounts = [acc.strip() for acc in accounts_text.split('\n') if acc.strip()]
        current_accounts = load_accounts("email.txt")
        new_accounts = []
        added = 0
        
        for acc in accounts:
            if acc not in current_accounts:
                current_accounts.append(acc)
                new_accounts.append(acc)
                added += 1
        
        if added > 0:
            save_accounts(current_accounts, "email.txt")
        
        for acc in new_accounts:
            self.start_new_account(acc)
            time.sleep(0.5)
        
        return added, new_accounts
    
    def delete_account(self, email):
        current_accounts = load_accounts("email.txt")
        if email in current_accounts:
            current_accounts.remove(email)
            save_accounts(current_accounts, "email.txt")
            
            withdraw_data = load_withdraw_data()
            if email in withdraw_data:
                del withdraw_data[email]
                save_withdraw_data(withdraw_data)
            
            schedule_data = load_schedule_data()
            if email in schedule_data:
                del schedule_data[email]
                save_schedule_data(schedule_data)
            
            for i, w in enumerate(self.workers):
                if w.email == email:
                    w.running = False
                    del self.workers[i]
                    if i < len(self.threads):
                        del self.threads[i]
                    return True
        return False
    
    def get_accounts(self):
        return load_accounts("email.txt")
    
    def add_proxy(self, proxy_text):
        proxies = [p.strip() for p in proxy_text.split('\n') if p.strip()]
        current_proxies = load_proxies("proxy.txt")
        added = 0
        clean_proxies = []
        for p in proxies:
            if not p.startswith("http://") and not p.startswith("https://") and not p.startswith("socks"):
                p = f"http://{p}"
            if p not in current_proxies:
                current_proxies.append(p)
                clean_proxies.append(p)
                added += 1
        save_proxies(current_proxies, "proxy.txt")
        return added, clean_proxies
    
    def delete_proxy(self, proxy):
        current_proxies = load_proxies("proxy.txt")
        if proxy in current_proxies:
            current_proxies.remove(proxy)
            save_proxies(current_proxies, "proxy.txt")
            return True
        return False
    
    def get_proxies(self):
        return load_proxies("proxy.txt")
    
    def test_proxy(self, proxy):
        if not proxy:
            return {"status": "failed", "error": "لا يوجد بروكسي"}
        try:
            if not proxy.startswith("http://") and not proxy.startswith("https://") and not proxy.startswith("socks"):
                proxy = f"http://{proxy}"
            start_time = time.time()
            url = "https://api.ipify.org?format=json"
            resp = requests.get(url, proxies={"http": proxy, "https": proxy}, timeout=15)
            response_time = time.time() - start_time
            if resp.status_code == 200:
                ip = resp.json().get("ip", "Unknown")
                return {"status": "working", "ip": ip, "speed": round(response_time, 2), "proxy": proxy}
        except Exception:
            pass
        return {"status": "failed"}

bot_manager = BotManager()
bot_manager.load_config()

temp_messages = {}

async def safe_edit_message(query, text, reply_markup=None, parse_mode="HTML"):
    try:
        if reply_markup:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await query.edit_message_text(text, parse_mode=parse_mode)
        return True
    except Exception as e:
        error_msg = str(e)
        if "message to edit" in error_msg or "message is not modified" in error_msg:
            try:
                if reply_markup:
                    await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
                else:
                    await query.message.reply_text(text, parse_mode=parse_mode)
                return True
            except:
                return False
        elif "Flood" in error_msg or "RetryAfter" in error_msg or "429" in error_msg:
            await asyncio.sleep(3)
            try:
                if reply_markup:
                    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
                else:
                    await query.edit_message_text(text, parse_mode=parse_mode)
                return True
            except:
                return False
        else:
            return False

async def auto_update_main(context: ContextTypes.DEFAULT_TYPE):
    if bot_manager.current_view != "main" or not bot_manager.running:
        return
    
    status = bot_manager.get_status()
    main_text = (
        f"🤖 <b>SpinCoin Bot - لوحة التحكم</b>\n\n"
        f"📧 الحسابات: {status['total_accounts']}\n"
        f"🟢 النشطة: {status['active_accounts']}\n"
        f"💰 الرصيد الكلي: {status['total_balance']:,.2f}\n"
        f"🌐 البروكسيات: {status['proxies_count']}\n\n"
        f"اختر الإجراء المناسب:"
    )
    keyboard = [
        [InlineKeyboardButton("🚀 تشغيل الكل", callback_data="start_all")],
        [InlineKeyboardButton("⏹️ إيقاف الكل", callback_data="stop_all")],
        [InlineKeyboardButton("📊 لوحة التحكم", callback_data="dashboard")],
        [InlineKeyboardButton("📧 الحسابات", callback_data="accounts_menu")],
        [InlineKeyboardButton("🌐 البروكسيات", callback_data="proxies_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        if bot_manager.main_message_id and bot_manager.chat_id:
            await context.bot.edit_message_text(
                chat_id=bot_manager.chat_id,
                message_id=bot_manager.main_message_id,
                text=main_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception:
        pass

async def auto_update_dashboard(context: ContextTypes.DEFAULT_TYPE):
    if bot_manager.current_view != "dashboard" or not bot_manager.running:
        return
    
    status = bot_manager.get_status()
    text = (
        f"📊 <b>لوحة التحكم</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📧 إجمالي الحسابات: {status['total_accounts']}\n"
        f"🟢 الحسابات النشطة: {status['active_accounts']}\n"
        f"💰 إجمالي الرصيد: {status['total_balance']:,.2f}\n"
        f"🌐 عدد البروكسيات: {status['proxies_count']}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"<b>تفاصيل الحسابات:</b>\n"
        f"{status['details']}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🔄 {datetime.now().strftime('%H:%M:%S')}"
    )
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        if bot_manager.dashboard_message_id and bot_manager.chat_id:
            await context.bot.edit_message_text(
                chat_id=bot_manager.chat_id,
                message_id=bot_manager.dashboard_message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception:
        pass

def manage_auto_update(context, view):
    if bot_manager.update_job:
        try:
            bot_manager.update_job.schedule_removal()
        except:
            pass
        bot_manager.update_job = None
        bot_manager.is_updating = False
    
    if view in ["main", "dashboard"] and bot_manager.running:
        if view == "main":
            bot_manager.update_job = context.job_queue.run_repeating(auto_update_main, interval=10, first=3)
        elif view == "dashboard":
            bot_manager.update_job = context.job_queue.run_repeating(auto_update_dashboard, interval=10, first=3)
        bot_manager.is_updating = True

async def show_delete_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accounts = bot_manager.get_accounts()
    if not accounts:
        if update.callback_query:
            await safe_edit_message(update.callback_query, "📭 لا يوجد حسابات لحذفها!")
        return
    
    total = len(accounts)
    per_page = bot_manager.items_per_page
    page = bot_manager.delete_page
    start = page * per_page
    end = min(start + per_page, total)
    
    if start >= total:
        bot_manager.delete_page = 0
        page = 0
        start = 0
        end = min(per_page, total)
    
    keyboard = []
    for i in range(start, end):
        acc = accounts[i]
        display = acc[:35] + "..." if len(acc) > 35 else acc
        keyboard.append([InlineKeyboardButton(f"🗑️ {display}", callback_data=f"delacc_{i}")])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data="delete_prev"))
    if end < total:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data="delete_next"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="accounts_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data['delete_accounts'] = {str(i): acc for i, acc in enumerate(accounts)}
    
    text = (
        f"🗑️ <b>حذف الحسابات</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📧 إجمالي: {total} حساب\n"
        f"📄 عرض: {start+1} - {end} من {total}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"اختر الحساب للحذف:"
    )
    if update.callback_query:
        await safe_edit_message(update.callback_query, text, reply_markup)

async def show_view_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accounts = bot_manager.get_accounts()
    if not accounts:
        if update.callback_query:
            await safe_edit_message(update.callback_query, "📭 لا يوجد حسابات!")
        return
    
    total = len(accounts)
    per_page = bot_manager.items_per_page
    page = bot_manager.accounts_page
    start = page * per_page
    end = min(start + per_page, total)
    
    if start >= total:
        bot_manager.accounts_page = 0
        page = 0
        start = 0
        end = min(per_page, total)
    
    text = f"📋 <b>قائمة الحسابات</b> (صفحة {page+1})\n━━━━━━━━━━━━━━━━━\n"
    for i in range(start, end):
        text += f"{i+1}. {accounts[i]}\n"
    text += f"\n📁 إجمالي الحسابات: {total}"
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data="acc_prev"))
    if end < total:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data="acc_next"))
    
    keyboard = []
    if nav_buttons:
        keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="accounts_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await safe_edit_message(update.callback_query, text, reply_markup)

async def show_withdraw_statuses_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accounts = bot_manager.get_accounts()
    if not accounts:
        if update.callback_query:
            await safe_edit_message(update.callback_query, "📭 لا يوجد حسابات لعرض حالات سحبها!")
        return
    
    total = len(accounts)
    per_page = bot_manager.items_per_page
    page = bot_manager.withdraw_status_page
    start = page * per_page
    end = min(start + per_page, total)
    
    if start >= total:
        bot_manager.withdraw_status_page = 0
        page = 0
        start = 0
        end = min(per_page, total)
    
    keyboard = []
    for i in range(start, end):
        acc = accounts[i]
        display = acc[:30] + "..." if len(acc) > 30 else acc
        keyboard.append([InlineKeyboardButton(f"📥 سحوبات: {display}", callback_data=f"get_wd_stat_{i}_0")])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data="wd_stat_prev"))
    if end < total:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data="wd_stat_next"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="accounts_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data['withdraw_status_accounts'] = {str(i): acc for i, acc in enumerate(accounts)}
    
    text = (
        f"📊 <b>عرض حالات السحب للحسابات</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"اختر الحساب لعرض حالات السحب في رسالة واحدة:"
    )
    if update.callback_query:
        await safe_edit_message(update.callback_query, text, reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 تشغيل الكل", callback_data="start_all")],
        [InlineKeyboardButton("⏹️ إيقاف الكل", callback_data="stop_all")],
        [InlineKeyboardButton("📊 لوحة التحكم", callback_data="dashboard")],
        [InlineKeyboardButton("📧 الحسابات", callback_data="accounts_menu")],
        [InlineKeyboardButton("🌐 البروكسيات", callback_data="proxies_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    bot_manager.chat_id = update.message.chat_id
    bot_manager.current_view = "main"
    
    if bot_manager.running:
        status = bot_manager.get_status()
        main_text = (
            f"🤖 <b>SpinCoin Bot - لوحة التحكم</b>\n\n"
            f"📧 الحسابات: {status['total_accounts']}\n"
            f"🟢 النشطة: {status['active_accounts']}\n"
            f"💰 الرصيد الكلي: {status['total_balance']:,.2f}\n"
            f"🌐 البروكسيات: {status['proxies_count']}\n\n"
            f"اختر الإجراء المناسب:"
        )
    else:
        main_text = (
            f"🤖 <b>SpinCoin Bot - لوحة التحكم</b>\n\n"
            f"⚠️ البوت متوقف\n"
            f"استخدم زر 'تشغيل الكل' للبدء\n\n"
            f"اختر الإجراء المناسب:"
        )
    
    msg = await update.message.reply_text(main_text, reply_markup=reply_markup, parse_mode="HTML")
    bot_manager.main_message_id = msg.message_id
    if context.job_queue:
        manage_auto_update(context, "main")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "start_all":
        if bot_manager.running:
            await safe_edit_message(query, "✅ البوت يعمل بالفعل!")
            return
        bot_manager.start_accounts()
        bot_manager.current_view = "main"
        status = bot_manager.get_status()
        main_text = (
            f"🤖 <b>SpinCoin Bot - لوحة التحكم</b>\n\n"
            f"📧 الحسابات: {status['total_accounts']}\n"
            f"🟢 النشطة: {status['active_accounts']}\n"
            f"💰 الرصيد الكلي: {status['total_balance']:,.2f}\n"
            f"🌐 البروكسيات: {status['proxies_count']}\n\n"
            f"اختر الإجراء المناسب:"
        )
        keyboard = [
            [InlineKeyboardButton("🚀 تشغيل الكل", callback_data="start_all")],
            [InlineKeyboardButton("⏹️ إيقاف الكل", callback_data="stop_all")],
            [InlineKeyboardButton("📊 لوحة التحكم", callback_data="dashboard")],
            [InlineKeyboardButton("📧 الحسابات", callback_data="accounts_menu")],
            [InlineKeyboardButton("🌐 البروكسيات", callback_data="proxies_menu")],
        ]
        await safe_edit_message(query, main_text, InlineKeyboardMarkup(keyboard))
        bot_manager.main_message_id = query.message.message_id
        if context.job_queue:
            manage_auto_update(context, "main")
    
    elif query.data == "stop_all":
        if not bot_manager.running:
            await safe_edit_message(query, "❌ البوت لا يعمل!")
            return
        bot_manager.stop_accounts()
        bot_manager.current_view = "main"
        main_text = (
            f"🤖 <b>SpinCoin Bot - لوحة التحكم</b>\n\n"
            f"⚠️ البوت متوقف (الحسابات محفوظة)\n"
            f"استخدم زر 'تشغيل الكل' للبدء\n\n"
            f"اختر الإجراء المناسب:"
        )
        keyboard = [
            [InlineKeyboardButton("🚀 تشغيل الكل", callback_data="start_all")],
            [InlineKeyboardButton("⏹️ إيقاف الكل", callback_data="stop_all")],
            [InlineKeyboardButton("📊 لوحة التحكم", callback_data="dashboard")],
            [InlineKeyboardButton("📧 الحسابات", callback_data="accounts_menu")],
            [InlineKeyboardButton("🌐 البروكسيات", callback_data="proxies_menu")],
        ]
        await safe_edit_message(query, main_text, InlineKeyboardMarkup(keyboard))
        bot_manager.main_message_id = query.message.message_id
        if context.job_queue and bot_manager.update_job:
            try:
                bot_manager.update_job.schedule_removal()
            except:
                pass
            bot_manager.update_job = None
            bot_manager.is_updating = False
    
    elif query.data == "dashboard":
        if not bot_manager.running:
            await safe_edit_message(query, "❌ البوت لا يعمل! قم بتشغيله أولاً.")
            return
        bot_manager.current_view = "dashboard"
        status = bot_manager.get_status()
        text = (
            f"📊 <b>لوحة التحكم</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📧 إجمالي الحسابات: {status['total_accounts']}\n"
            f"🟢 الحسابات النشطة: {status['active_accounts']}\n"
            f"💰 إجمالي الرصيد: {status['total_balance']:,.2f}\n"
            f"🌐 عدد البروكسيات: {status['proxies_count']}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"<b>تفاصيل الحسابات:</b>\n"
            f"{status['details']}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🔄 {datetime.now().strftime('%H:%M:%S')}"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        bot_manager.dashboard_message_id = query.message.message_id
        if context.job_queue:
            manage_auto_update(context, "dashboard")
    
    elif query.data == "accounts_menu":
        bot_manager.current_view = "accounts"
        bot_manager.delete_page = 0
        bot_manager.accounts_page = 0
        bot_manager.withdraw_status_page = 0
        
        if context.job_queue and bot_manager.update_job:
            try:
                bot_manager.update_job.schedule_removal()
            except:
                pass
            bot_manager.update_job = None
            bot_manager.is_updating = False
        
        keyboard = [
            [InlineKeyboardButton("📋 عرض الحسابات", callback_data="view_accounts")],
            [InlineKeyboardButton("📊 عرض حالات السحب", callback_data="withdraw_statuses_menu")],
            [InlineKeyboardButton("➕ إضافة حسابات", callback_data="add_accounts")],
            [InlineKeyboardButton("🗑️ حذف حساب", callback_data="delete_account")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
        ]
        await safe_edit_message(query,
            "📧 <b>إدارة الحسابات</b>\n\n"
            "اختر الإجراء المناسب:\n"
            "⚠️ حذف حساب يمسحه من الملف نهائياً",
            InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "view_accounts":
        bot_manager.accounts_page = 0
        await show_view_accounts(update, context)
    
    elif query.data == "acc_next":
        bot_manager.accounts_page += 1
        await show_view_accounts(update, context)
    
    elif query.data == "acc_prev":
        if bot_manager.accounts_page > 0:
            bot_manager.accounts_page -= 1
        await show_view_accounts(update, context)
    
    elif query.data == "withdraw_statuses_menu":
        bot_manager.withdraw_status_page = 0
        await show_withdraw_statuses_list(update, context)
    
    elif query.data == "wd_stat_next":
        bot_manager.withdraw_status_page += 1
        await show_withdraw_statuses_list(update, context)
    
    elif query.data == "wd_stat_prev":
        if bot_manager.withdraw_status_page > 0:
            bot_manager.withdraw_status_page -= 1
        await show_withdraw_statuses_list(update, context)
    
    elif query.data.startswith("get_wd_stat_"):
        parts = query.data.split("_")
        idx = parts[3]
        page_idx = int(parts[4])
        
        acc_map = context.user_data.get('withdraw_status_accounts', {})
        email = acc_map.get(idx)
        if email:
            worker_obj = None
            for w in bot_manager.workers:
                if w.email == email:
                    worker_obj = w
                    break
            
            if not worker_obj:
                proxies = load_proxies("proxy.txt")
                proxy = proxies[0] if proxies else None
                worker_obj = AccountWorker(email, proxy, 0, bot_manager.bot_token, bot_manager.chat_id)
                if not worker_obj.do_login():
                    await safe_edit_message(query, f"❌ فشل تسجيل الدخول للحساب {email}")
                    return
            
            today_date_str = datetime.now().strftime("%Y-%m-%d")
            pages_list = worker_obj.fetch_all_withdrawals_grouped(today_date_str)
            
            if page_idx >= len(pages_list):
                page_idx = 0
            
            current_text = pages_list[page_idx]
            
            nav_buttons = []
            if page_idx > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"get_wd_stat_{idx}_{page_idx - 1}"))
            if page_idx < len(pages_list) - 1:
                nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"get_wd_stat_{idx}_{page_idx + 1}"))
            
            keyboard = []
            if nav_buttons:
                keyboard.append(nav_buttons)
            keyboard.append([InlineKeyboardButton("🔙 رجوع لقائمة الحسابات", callback_data="withdraw_statuses_menu")])
            
            final_message = (
                f"📥 <b>حالة السحب للحساب:</b> {email}\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"<pre>{current_text}</pre>"
            )
            await safe_edit_message(query, final_message, InlineKeyboardMarkup(keyboard))
    
    elif query.data == "add_accounts":
        temp_messages[user_id] = "add_accounts"
        await safe_edit_message(query,
            "✏️ <b>إضافة حسابات جديدة</b>\n\n"
            "أرسل قائمة الحسابات (كل حساب في سطر منفصل):\n"
            "مثال:\n"
            "user1@gmail.com\n"
            "user2@gmail.com\n\n"
            "🔙 لإلغاء العملية أرسل /cancel"
        )
    
    elif query.data == "delete_account":
        await show_delete_accounts(update, context)
    
    elif query.data.startswith("delacc_"):
        idx = query.data.replace("delacc_", "")
        delete_map = context.user_data.get('delete_accounts', {})
        email = delete_map.get(idx)
        if email:
            if bot_manager.delete_account(email):
                await safe_edit_message(query, f"✅ تم حذف الحساب: {email}")
                await asyncio.sleep(0.5)
                await show_delete_accounts(update, context)
            else:
                await safe_edit_message(query, f"❌ لم يتم العثور على الحساب")
    
    elif query.data == "delete_next":
        bot_manager.delete_page += 1
        await show_delete_accounts(update, context)
    
    elif query.data == "delete_prev":
        if bot_manager.delete_page > 0:
            bot_manager.delete_page -= 1
        await show_delete_accounts(update, context)
    
    elif query.data == "proxies_menu":
        bot_manager.current_view = "proxies"
        if context.job_queue and bot_manager.update_job:
            try:
                bot_manager.update_job.schedule_removal()
            except:
                pass
            bot_manager.update_job = None
            bot_manager.is_updating = False
        
        keyboard = [
            [InlineKeyboardButton("📋 عرض البروكسيات", callback_data="view_proxies")],
            [InlineKeyboardButton("➕ إضافة بروكسيات", callback_data="add_proxies")],
            [InlineKeyboardButton("🗑️ حذف بروكسي", callback_data="delete_proxy")],
            [InlineKeyboardButton("🧪 اختبار بروكسي", callback_data="test_proxy_menu")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
        ]
        await safe_edit_message(query, "🌐 <b>إدارة البروكسيات</b>\n\nاختر الإجراء المناسب:", InlineKeyboardMarkup(keyboard))
    
    elif query.data == "view_proxies":
        proxies = bot_manager.get_proxies()
        if not proxies:
            await safe_edit_message(query, "📭 لا يوجد بروكسيات!")
            return
        text = "🌐 <b>قائمة البروكسيات</b>\n━━━━━━━━━━━━━━━━━\n"
        for i, p in enumerate(proxies[:30], 1):
            text += f"{i}. {p}\n"
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="proxies_menu")]]
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
    
    elif query.data == "add_proxies":
        temp_messages[user_id] = "add_proxies"
        await safe_edit_message(query,
            "✏️ <b>إضافة بروكسيات جديدة</b>\n\n"
            "أرسل قائمة البروكسيات (كل بروكسي في سطر منفصل):\n"
            "🔙 لإلغاء العملية أرسل /cancel"
        )
    
    elif query.data == "delete_proxy":
        proxies = bot_manager.get_proxies()
        if not proxies:
            await safe_edit_message(query, "📭 لا يوجد بروكسيات لحذفها!")
            return
        keyboard = []
        for i, p in enumerate(proxies[:20]):
            display = p[:30] + "..." if len(p) > 30 else p
            keyboard.append([InlineKeyboardButton(f"🗑️ {display}", callback_data=f"delproxy_{i}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="proxies_menu")])
        context.user_data['delete_proxies'] = {str(i): p for i, p in enumerate(proxies[:20])}
        await safe_edit_message(query, "🗑️ <b>اختر البروكسي للحذف:</b>", InlineKeyboardMarkup(keyboard))
    
    elif query.data.startswith("delproxy_"):
        idx = query.data.replace("delproxy_", "")
        delete_map = context.user_data.get('delete_proxies', {})
        proxy = delete_map.get(idx)
        if proxy:
            bot_manager.delete_proxy(proxy)
            proxies = bot_manager.get_proxies()
            if proxies:
                keyboard = []
                for i, p in enumerate(proxies[:20]):
                    display = p[:30] + "..." if len(p) > 30 else p
                    keyboard.append([InlineKeyboardButton(f"🗑️ {display}", callback_data=f"delproxy_{i}")])
                keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="proxies_menu")])
                context.user_data['delete_proxies'] = {str(i): p for i, p in enumerate(proxies[:20])}
                await safe_edit_message(query, "🗑️ <b>اختر البروكسي للحذف:</b>", InlineKeyboardMarkup(keyboard))
            else:
                await safe_edit_message(query, "📭 لا يوجد بروكسيات متبقية!")
    
    elif query.data == "test_proxy_menu":
        proxies = bot_manager.get_proxies()
        if not proxies:
            await safe_edit_message(query, "📭 لا يوجد بروكسيات لاختبارها!")
            return
        keyboard = []
        for i, p in enumerate(proxies[:15]):
            display = p[:25] + "..." if len(p) > 25 else p
            keyboard.append([InlineKeyboardButton(f"🧪 {display}", callback_data=f"testproxy_{i}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="proxies_menu")])
        context.user_data['test_proxies'] = {str(i): p for i, p in enumerate(proxies[:15])}
        await safe_edit_message(query, "🧪 <b>اختر البروكسي لاختباره:</b>", InlineKeyboardMarkup(keyboard))
    
    elif query.data.startswith("testproxy_"):
        idx = query.data.replace("testproxy_", "")
        test_map = context.user_data.get('test_proxies', {})
        proxy = test_map.get(idx)
        if proxy:
            await query.message.reply_text("🔄 جاري اختبار البروكسي...")
            await asyncio.sleep(1)
            result = bot_manager.test_proxy(proxy)
            if result["status"] == "working":
                await query.message.reply_text(
                    f"✅ <b>البروكسي يعمل!</b>\n🌐 <b>IP:</b> {result['ip']}\n⚡ <b>السرعة:</b> {result['speed']} ثانية",
                    parse_mode="HTML"
                )
            else:
                await query.message.reply_text("❌ <b>البروكسي لا يعمل!</b>", parse_mode="HTML")
    
    elif query.data == "back_main":
        bot_manager.current_view = "main"
        keyboard = [
            [InlineKeyboardButton("🚀 تشغيل الكل", callback_data="start_all")],
            [InlineKeyboardButton("⏹️ إيقاف الكل", callback_data="stop_all")],
            [InlineKeyboardButton("📊 لوحة التحكم", callback_data="dashboard")],
            [InlineKeyboardButton("📧 الحسابات", callback_data="accounts_menu")],
            [InlineKeyboardButton("🌐 البروكسيات", callback_data="proxies_menu")],
        ]
        if bot_manager.running:
            status = bot_manager.get_status()
            main_text = (
                f"🤖 <b>SpinCoin Bot - لوحة التحكم</b>\n\n"
                f"📧 الحسابات: {status['total_accounts']}\n"
                f"🟢 النشطة: {status['active_accounts']}\n"
                f"💰 الرصيد الكلي: {status['total_balance']:,.2f}\n"
                f"🌐 البروكسيات: {status['proxies_count']}\n\n"
                f"اختر الإجراء المناسب:"
            )
        else:
            main_text = (
                f"🤖 <b>SpinCoin Bot - لوحة التحكم</b>\n\n"
                f"⚠️ البوت متوقف\n"
                f"اختر الإجراء المناسب:"
            )
        await safe_edit_message(query, main_text, InlineKeyboardMarkup(keyboard))
        bot_manager.main_message_id = query.message.message_id
        if context.job_queue:
            manage_auto_update(context, "main")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    
    if text == "/cancel":
        if user_id in temp_messages:
            del temp_messages[user_id]
        await update.message.reply_text("❌ تم إلغاء العملية!")
        return
    
    action = temp_messages.get(user_id)
    if action == "add_accounts":
        added, new_accounts = bot_manager.add_accounts(text)
        if added > 0:
            await update.message.reply_text(f"✅ تم إضافة وتشغيل {added} حساب بنجاح!")
        else:
            await update.message.reply_text("⚠️ لم يتم إضافة أي حساب جديد.")
        del temp_messages[user_id]
    elif action == "add_proxies":
        added, new_proxies = bot_manager.add_proxy(text)
        if added > 0:
            await update.message.reply_text(f"✅ تم إضافة {added} بروكسي جديد!")
        else:
            await update.message.reply_text("⚠️ لم يتم إضافة أي بروكسي جديد.")
        del temp_messages[user_id]
    else:
        await update.message.reply_text("❌ أمر غير معروف. استخدم /start للبدء.")

async def setlimit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعيين حد السحب للحسابات"""
    args = context.args
    
    # عرض الإعدادات الحالية
    if not args:
        config = load_config()
        workers_info = ""
        if bot_manager.workers:
            first_worker = bot_manager.workers[0]
            workers_info = f"\n👤 مثال لحساب: {first_worker.email[:15]}... | 🎯 {first_worker.target_withdraw_limit}"
        
        await update.message.reply_text(
            f"⚙️ <b>إعدادات ليمت السحب الحالية:</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📊 الحد الأدنى العام: {config.get('min_withdraw', 55000):,}\n"
            f"📊 الحد الأقصى العام: {config.get('max_withdraw', 60000):,}\n"
            f"{workers_info}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"<b>📖 الأوامر المتاحة:</b>\n"
            f"<code>/setlimit min max</code> - تعيين لكل الحسابات\n"
            f"<code>/setlimit حساب@example.com min max</code> - لحساب محدد\n"
            f"<code>/setlimit all min max</code> - تعيين لكل الحسابات (نفس الأول)\n"
            f"<code>/setlimit show</code> - عرض إعدادات كل حساب\n\n"
            f"📌 مثال: <code>/setlimit 50000 65000</code>",
            parse_mode="HTML"
        )
        return
    
    # عرض إعدادات كل حساب
    if args[0].lower() == "show":
        if not bot_manager.workers:
            await update.message.reply_text("⚠️ لا يوجد حسابات نشطة لعرض إعداداتها!")
            return
        
        text = "📊 <b>إعدادات ليمت السحب لكل حساب:</b>\n━━━━━━━━━━━━━━━━━\n"
        for i, w in enumerate(bot_manager.workers, 1):
            status = "🟢" if w.running else "🔴"
            stopped = " ⏸️" if w.stopped else ""
            text += f"{i}. {status} {w.email[:25]}... | 🎯 {w.target_withdraw_limit:,}{stopped}\n"
        await update.message.reply_text(text, parse_mode="HTML")
        return
    
    # معالجة التعيين
    try:
        # حالة 1: تعيين لحساب محدد
        if "@" in args[0] and len(args) >= 3:
            email = args[0]
            min_l = int(args[1])
            max_l = int(args[2])
            
            if min_l > max_l:
                min_l, max_l = max_l, min_l
            
            found = False
            for w in bot_manager.workers:
                if w.email == email:
                    w.target_withdraw_limit = random.randint(min_l, max_l)
                    found = True
                    break
            
            if found:
                await update.message.reply_text(
                    f"✅ <b>تم تحديث ليمت السحب للحساب:</b>\n"
                    f"📧 {email[:30]}...\n"
                    f"🎯 النطاق الجديد: من {min_l:,} إلى {max_l:,}",
                    parse_mode="HTML"
                )
            else:
                accounts = load_accounts("email.txt")
                if email in accounts:
                    await update.message.reply_text(
                        f"⚠️ الحساب موجود في الملف لكنه غير نشط!\n"
                        f"قم بتشغيل البوت أولاً ثم حاول مرة أخرى.",
                        parse_mode="HTML"
                    )
                else:
                    await update.message.reply_text(
                        f"❌ الحساب {email[:30]}... غير موجود!\n"
                        f"تأكد من كتابته بشكل صحيح.",
                        parse_mode="HTML"
                    )
            return
        
        # حالة 2: تعيين لكل الحسابات
        if args[0].lower() == "all":
            min_l = int(args[1])
            max_l = int(args[2])
        else:
            min_l = int(args[0])
            max_l = int(args[1]) if len(args) > 1 else min_l
        
        if min_l > max_l:
            min_l, max_l = max_l, min_l
        
        # تحديث الملف
        config = load_config()
        config["min_withdraw"] = min_l
        config["max_withdraw"] = max_l
        save_config(config)
        
        # تحديث جميع العمال النشطين
        updated_count = 0
        for w in bot_manager.workers:
            w.target_withdraw_limit = random.randint(min_l, max_l)
            updated_count += 1
        
        await update.message.reply_text(
            f"✅ <b>تم تحديث ليمت السحب بنجاح!</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🎯 النطاق الجديد: من {min_l:,} إلى {max_l:,}\n"
            f"👤 عدد الحسابات المحدثة: {updated_count}\n"
            f"📁 تم حفظ الإعدادات في الملف",
            parse_mode="HTML"
        )
        
    except (ValueError, IndexError) as e:
        await update.message.reply_text(
            f"❌ <b>خطأ في الصيغة!</b>\n\n"
            f"الصيغة الصحيحة:\n"
            f"<code>/setlimit min max</code>\n"
            f"مثال: <code>/setlimit 50000 65000</code>\n\n"
            f"أو لحساب محدد:\n"
            f"<code>/setlimit email@example.com min max</code>",
            parse_mode="HTML"
        )

async def showlimits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إعدادات ليمت السحب لكل حساب"""
    if not bot_manager.workers:
        await update.message.reply_text("⚠️ لا يوجد حسابات نشطة!")
        return
    
    config = load_config()
    text = (
        f"📊 <b>إعدادات ليمت السحب</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📈 الحد العام الأدنى: {config.get('min_withdraw', 55000):,}\n"
        f"📈 الحد العام الأقصى: {config.get('max_withdraw', 60000):,}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"<b>👤 إعدادات كل حساب:</b>\n"
    )
    
    for i, w in enumerate(bot_manager.workers, 1):
        status = "🟢" if w.running else "🔴"
        stopped = " ⏸️" if w.stopped else ""
        text += f"{i}. {status} {w.email[:20]}... | 🎯 {w.target_withdraw_limit:,}{stopped}\n"
    
    await update.message.reply_text(text, parse_mode="HTML")

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_manager.running:
        await update.message.reply_text("❌ البوت لا يعمل! استخدم /start لتشغيله.")
        return
    status = bot_manager.get_status()
    text = (
        f"📊 <b>لوحة التحكم</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📧 إجمالي الحسابات: {status['total_accounts']}\n"
        f"🟢 الحسابات النشطة: {status['active_accounts']}\n"
        f"💰 إجمالي الرصيد: {status['total_balance']:,.2f}\n"
        f"🌐 عدد البروكسيات: {status['proxies_count']}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"<b>تفاصيل الحسابات:</b>\n"
        f"{status['details']}"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in temp_messages:
        del temp_messages[user_id]
    await update.message.reply_text("❌ تم إلغاء العملية!")

async def allwithdrawals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جلب جميع عمليات السحب لجميع الحسابات"""
    await update.message.reply_text("🔄 جاري جلب جميع عمليات السحب لجميع الحسابات...")
    
    # الحصول على جميع الحسابات من الملف
    accounts = bot_manager.get_accounts()
    if not accounts:
        await update.message.reply_text("❌ لا يوجد حسابات مسجلة!")
        return
    
    today_date_str = datetime.now().strftime("%Y-%m-%d")
    total_withdrawals_count = 0
    messages_to_send = []
    
    # جلب السحوبات لكل حساب على حدة
    for idx, email in enumerate(accounts):
        try:
            # البحث عن العامل النشط لهذا الحساب
            worker_obj = None
            for w in bot_manager.workers:
                if w.email == email:
                    worker_obj = w
                    break
            
            # إذا لم يكن الحساب نشطاً، نقوم بإنشاء كائن مؤقت
            if not worker_obj:
                proxies = load_proxies("proxy.txt")
                proxy = proxies[idx % len(proxies)] if proxies else None
                if not proxy:
                    messages_to_send.append(f"❌ <b>{email}</b>: لا يوجد بروكسي متاح")
                    continue
                worker_obj = AccountWorker(email, proxy, idx, bot_manager.bot_token, bot_manager.chat_id)
                if not worker_obj.do_login():
                    messages_to_send.append(f"❌ <b>{email}</b>: فشل تسجيل الدخول")
                    continue
            
            # جلب السحوبات
            pages = worker_obj.fetch_all_withdrawals_grouped(today_date_str)
            
            # استخراج السحوبات من الصفحات
            withdrawals_list = []
            for page in pages:
                lines = page.split('\n')
                current_withdraw = {}
                for line in lines:
                    if 'القيمة (Value)' in line:
                        current_withdraw['value'] = line.split(':')[1].strip()
                    elif 'العملة (Currency)' in line:
                        current_withdraw['currency'] = line.split(':')[1].strip()
                    elif 'حالة الـ (Status)' in line:
                        current_withdraw['status'] = line.split(':')[1].strip()
                    elif 'نوع المحفظة' in line:
                        current_withdraw['type_wallet'] = line.split(':')[1].strip()
                    elif 'تاريخ الإنشاء' in line:
                        current_withdraw['date'] = line.split(':')[1].strip()
                    elif '--- عملية السحب' in line and current_withdraw:
                        if current_withdraw:
                            withdrawals_list.append(current_withdraw)
                        current_withdraw = {}
                if current_withdraw:
                    withdrawals_list.append(current_withdraw)
            
            # بناء رسالة الحساب
            if not withdrawals_list:
                messages_to_send.append(f"📧 <b>{email}</b>: لا توجد سحوبات")
                continue
            
            # بناء رسالة لكل حساب مع جميع سحوباته
            account_msg = f"📧 <b>{email}</b> ({len(withdrawals_list)} سحوبات)\n"
            account_msg += "─────────────────────\n"
            
            for i, w in enumerate(withdrawals_list, 1):
                account_msg += (
                    f"  {i}. 💰 {w.get('value', 'N/A')} "
                    f"| {w.get('currency', 'N/A')} "
                    f"| {w.get('status', 'N/A')} "
                    f"| {w.get('type_wallet', 'N/A')}\n"
                )
            
            total_withdrawals_count += len(withdrawals_list)
            messages_to_send.append(account_msg)
            
        except Exception as e:
            messages_to_send.append(f"❌ <b>{email}</b>: خطأ - {str(e)[:50]}")
    
    # إرسال كل رسالة حساب على حدة
    if not messages_to_send:
        await update.message.reply_text("❌ لا توجد بيانات لعرضها!")
        return
    
    # إرسال رسالة تمهيدية
    header = (
        f"📊 <b>جميع عمليات السحب لجميع الحسابات</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 التاريخ: {today_date_str}\n"
        f"👤 عدد الحسابات: {len(accounts)}\n"
        f"💰 إجمالي عمليات السحب: {total_withdrawals_count}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    await update.message.reply_text(header, parse_mode="HTML")
    
    # إرسال كل حساب في رسالة منفصلة
    for msg in messages_to_send:
        # التحقق من طول الرسالة وتقسيمها إذا لزم الأمر
        if len(msg) > 4000:
            # تقسيم الرسالة الطويلة
            parts = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode="HTML")
        else:
            await update.message.reply_text(msg, parse_mode="HTML")
    
    # إرسال رسالة ختامية
    await update.message.reply_text(
        f"✅ <b>تم عرض جميع السحوبات بنجاح!</b>\n"
        f"📊 إجمالي السحوبات: {total_withdrawals_count}\n"
        f"📧 عدد الحسابات المعروضة: {len([m for m in messages_to_send if 'لا توجد سحوبات' not in m and 'خطأ' not in m])}",
        parse_mode="HTML"
    )

async def single_withdrawals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """جلب سحوبات لحساب واحد محدد"""
    args = context.args
    
    if not args:
        await update.message.reply_text(
            f"❌ <b>يرجى تحديد البريد الإلكتروني</b>\n\n"
            f"الاستخدام: <code>/singlewd email@example.com</code>\n"
            f"مثال: <code>/singlewd user1@gmail.com</code>",
            parse_mode="HTML"
        )
        return
    
    email = args[0]
    
    # التحقق من وجود الحساب
    accounts = bot_manager.get_accounts()
    if email not in accounts:
        await update.message.reply_text(f"❌ الحساب {email} غير موجود في القائمة!")
        return
    
    await update.message.reply_text(f"🔄 جاري جلب سحوبات الحساب: {email}...")
    
    try:
        # البحث عن العامل النشط
        worker_obj = None
        for w in bot_manager.workers:
            if w.email == email:
                worker_obj = w
                break
        
        # إنشاء كائن مؤقت إذا لم يكن نشطاً
        if not worker_obj:
            proxies = load_proxies("proxy.txt")
            proxy = proxies[0] if proxies else None
            if not proxy:
                await update.message.reply_text("❌ لا يوجد بروكسي متاح!")
                return
            worker_obj = AccountWorker(email, proxy, 0, bot_manager.bot_token, bot_manager.chat_id)
            if not worker_obj.do_login():
                await update.message.reply_text(f"❌ فشل تسجيل الدخول للحساب {email}")
                return
        
        today_date_str = datetime.now().strftime("%Y-%m-%d")
        pages = worker_obj.fetch_all_withdrawals_grouped(today_date_str)
        
        if not pages or "لا توجد عمليات سحب" in pages[0]:
            await update.message.reply_text(
                f"📧 <b>{email}</b>\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"📭 لا توجد عمليات سحب مسجلة لهذا الحساب",
                parse_mode="HTML"
            )
            return
        
        # إرسال كل صفحة كرسالة منفصلة
        for i, page in enumerate(pages, 1):
            msg = (
                f"📧 <b>{email}</b> - صفحة {i}/{len(pages)}\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"<pre>{page}</pre>"
            )
            await update.message.reply_text(msg, parse_mode="HTML")
        
        await update.message.reply_text(
            f"✅ <b>تم عرض جميع سحوبات الحساب بنجاح!</b>\n"
            f"📧 {email}\n"
            f"📄 عدد الصفحات: {len(pages)}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء جلب السحوبات: {str(e)[:100]}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض لوحة تحكم بجميع الأوامر مع شرح"""
    help_text = (
        f"🤖 <b>دليل استخدام بوت SpinCoin</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        f"<b>📋 الأوامر الأساسية:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<code>/start</code> - تشغيل البوت وعرض القائمة الرئيسية\n"
        f"<code>/help</code> - عرض هذه التعليمات\n"
        f"<code>/dashboard</code> - عرض لوحة التحكم مع تفاصيل الحسابات\n"
        f"<code>/cancel</code> - إلغاء أي عملية جارية\n\n"
        
        f"<b>⚙️ أوامر إدارة الليميت:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<code>/setlimit</code> - عرض الإعدادات الحالية\n"
        f"<code>/setlimit min max</code> - تعيين حد لكل الحسابات\n"
        f"<code>/setlimit email min max</code> - تعيين حد لحساب محدد\n"
        f"<code>/setlimit show</code> - عرض إعدادات كل حساب\n"
        f"<code>/showlimits</code> - اختصار لعرض الإعدادات\n\n"
        
        f"<b>📊 أوامر السحوبات:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<code>/allwithdrawals</code> - جلب سحوبات جميع الحسابات\n"
        f"<code>/allwd</code> - اختصار للأمر السابق\n"
        f"<code>/singlewd email</code> - جلب سحوبات حساب محدد\n"
        f"<code>/singlewd user1@gmail.com</code> - مثال\n\n"
        
        f"<b>📌 أمثلة عملية:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• تعيين حد السحب العام:\n"
        f"  <code>/setlimit 40000 70000</code>\n\n"
        f"• تعيين حد لحساب محدد:\n"
        f"  <code>/setlimit user1@gmail.com 30000 50000</code>\n\n"
        f"• عرض إعدادات جميع الحسابات:\n"
        f"  <code>/setlimit show</code>\n\n"
        f"• جلب سحوبات حساب واحد:\n"
        f"  <code>/singlewd user1@gmail.com</code>\n\n"
        
        f"<b>🎯 القوائم التفاعلية:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• 📧 <b>الحسابات</b> - إدارة الحسابات\n"
        f"  - عرض الحسابات\n"
        f"  - عرض حالات السحب\n"
        f"  - إضافة حسابات جديدة\n"
        f"  - حذف حساب\n\n"
        f"• 🌐 <b>البروكسيات</b> - إدارة البروكسيات\n"
        f"  - عرض البروكسيات\n"
        f"  - إضافة بروكسيات جديدة\n"
        f"  - حذف بروكسي\n"
        f"  - اختبار بروكسي\n\n"
        
        f"<b>💡 ملاحظات مهمة:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• كل حساب يسحب مرة واحدة يومياً\n"
        f"• السحب يتم لكامل الرصيد عند الوصول للهدف\n"
        f"• الحساب يتوقف بعد السحب حتى اليوم التالي\n"
        f"• يمكن تعديل الهدف لكل حساب على حدة\n"
        f"• استخدم /cancel لإلغاء أي عملية إدخال\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <b>البوت يعمل بكفاءة عالية</b> ✅"
    )
    
    # تقسيم الرسالة إذا كانت طويلة جداً
    if len(help_text) > 4000:
        parts = [help_text[i:i+4000] for i in range(0, len(help_text), 4000)]
        for i, part in enumerate(parts):
            if i == 0:
                await update.message.reply_text(part, parse_mode="HTML")
            else:
                await update.message.reply_text(
                    f"📄 <b>تابع التعليمات ({i+1}/{len(parts)})</b>\n━━━━━━━━━━━━━━━━━\n{part}",
                    parse_mode="HTML"
                )
    else:
        await update.message.reply_text(help_text, parse_mode="HTML")

def main():
    config = bot_manager.load_config()
    token = config.get("telegram_bot_token")
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        print("Please set your bot token in config.json")
        return
    
    application = Application.builder().token(token).build()
    
    # الأوامر الأساسية
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # أوامر الليميت
    application.add_handler(CommandHandler("setlimit", setlimit_command))
    application.add_handler(CommandHandler("showlimits", showlimits_command))
    
    # أوامر السحوبات
    application.add_handler(CommandHandler("allwithdrawals", allwithdrawals_command))
    application.add_handler(CommandHandler("allwd", allwithdrawals_command))  # اختصار
    application.add_handler(CommandHandler("singlewd", single_withdrawals_command))
    application.add_handler(CommandHandler("withdrawals", single_withdrawals_command))  # اختصار
    
    # معالج الأزرار والرسائل
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot is running with all updates...")
    print("📋 Available commands: /start, /help, /dashboard, /setlimit, /showlimits, /allwithdrawals, /singlewd")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()