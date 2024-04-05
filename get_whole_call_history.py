from datetime import datetime
from dotenv import load_dotenv
import requests
from hashlib import sha256
import os
import json

load_dotenv()
vpbx_api_key = os.getenv("MANGO_KEY")
vpbx_api_sign = os.getenv("MANGO_SALT")


def rewrite_json():
    with open("raw_api_response.json", "r") as file:
        json_text = file.read()
    full_json = f'[{json_text}]'
    python_dict = json.loads(full_json)
    json_data = python_dict[0].get("data")[0].get("list")
    for i in json_data:
        print(i.get("caller_name"))

def create_napravlenie_field(json_data):
    context_type = json_data.get("context_type")
    context_status = json_data.get("context_status")
    if context_type == 1:
        if context_status:
            napravlenie_data = "Входящий внешний вызов"
        else:
            napravlenie_data = "Входящий пропущенный"
    elif context_type == 3:
        if context_status:
            napravlenie_data = "Исходящий внешний вызов"
        else:
            napravlenie_data = "Исходящий несостоявшийся"
    else:
        napravlenie_data = "Внутренний вызов"

    return napravlenie_data


def get_call_history_id(date):
    json_data = f'{{"start_date":"{date} 10:00:00", "end_date":"{date} 15:59:59", "limit":"5000", "offset":"0"}}'

    res = (vpbx_api_key + json_data + vpbx_api_sign).encode('UTF-8')
    sign = sha256(res).hexdigest()
    url = "https://app.mango-office.ru/vpbx/stats/calls/request/"
    payload = {
        "vpbx_api_key": vpbx_api_key,
        "sign": sign,
        "json": json_data
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(url, headers=headers, data=payload)
    print(response.text)
    response_content = response.json()
    print(response_content.get("key"))
    return response_content.get("key")


def get_call_history(key):
    json_data = f'{{"key":"{key}"}}'
    res = (vpbx_api_key + json_data + vpbx_api_sign).encode('UTF-8')
    sign = sha256(res).hexdigest()
    url = "https://app.mango-office.ru/vpbx/stats/calls/result/"
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
        print('response ok')
        return response.json()
    else:
        print('response error')


def parse_json(response):
    json_data = response.json()

    data_to_write = ''
    for i in json_data.get('data', []):
        for j in i.get('list', []):
             context_start_time_timestamp = j.get("context_start_time")
             call_end_time_timestamp0 = j.get("context_calls")
             if call_end_time_timestamp0:
                call_end_time_timestamp = call_end_time_timestamp0[0].get("call_end_time")
             else:
                 call_end_time_timestamp = ''

             data_to_write += (f'{{'
                               f'"entry_id": "{j.get("entry_id")}", '
                               f'"napravlenie": "{create_napravlenie_field(j)}", '
                               f'"data_postupil": "{datetime.utcfromtimestamp(context_start_time_timestamp).date() if context_start_time_timestamp else None}", '
                               f'"time_postupil": "{datetime.utcfromtimestamp(context_start_time_timestamp).time() if context_start_time_timestamp else None}", '
                               f'"dlitelnost": "{j.get("duration")}",'
                               f'"tel_kto_zvonil": "{j.get("caller_number")}",'
                               f'"komu_zvonil": "{j.get("call_abonent_info")}", '
                               f'"tel_komu_zvonil": "{j.get("call_abonent_number")}", '
                               f'"kuda_zvonil": "{j.get("called_number")}", '
                               f'"data_okonchania_razgovora": "{datetime.utcfromtimestamp(call_end_time_timestamp).date() if call_end_time_timestamp else None}",'
                               f'"time_okonchania_razgovora": "{datetime.utcfromtimestamp(call_end_time_timestamp).time() if call_end_time_timestamp else None}",'
                               f'}}, ')
    with open('mango_call_history.txt', 'w') as file:
        file.write(data_to_write)



date = "30.03.2024"
id = get_call_history_id(date)
response_json = get_call_history(id)
with open('raw_api_response', 'w') as file:
    file.write(str(response_json))
