from dotenv import load_dotenv
import requests
from hashlib import sha256
import os

load_dotenv()
vpbx_api_key = os.getenv("MANGO_KEY")
vpbx_api_sign = os.getenv("MANGO_SALT")
json_data = f'{{"recording_id": "MToxMDEyODIxOToyMDIzMDU5NDk5Mjow", "action": "download"}}'
res = (vpbx_api_key + json_data + vpbx_api_sign).encode('UTF-8')
sign = sha256(res).hexdigest()
print("sign:", sign)
url = "https://app.mango-office.ru/vpbx/queries/recording/post"
payload = {
    "vpbx_api_key": vpbx_api_key,
    "sign": sign,
    "json": json_data
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}
response = requests.post(url, headers=headers, data=payload)
if response.status_code == 200:
    file_path = "downloaded_audio.mp3"
    with open(file_path, 'wb') as audio_file:
        audio_file.write(response.content)