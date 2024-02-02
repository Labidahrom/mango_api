from dotenv import load_dotenv
import requests
from hashlib import sha256
import os

load_dotenv()
vpbx_api_key = os.getenv("MANGO_KEY")
vpbx_api_sign = os.getenv("MANGO_SALT")
json_data = "{}"
res = (vpbx_api_key + json_data + vpbx_api_sign).encode('UTF-8')
sign = sha256(res).hexdigest()
print("sign:", sign)
url = "https://app.mango-office.ru/vpbx/schemas"
payload = {
    "vpbx_api_key": vpbx_api_key,
    "sign": sign,
    "json": json_data
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}
response = requests.post(url, headers=headers, data=payload)
print(response.json())