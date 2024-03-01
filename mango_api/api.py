from celery import shared_task
from datetime import date, datetime
from datetime import timedelta
from dateutil.rrule import rrule, DAILY
from django.db import IntegrityError
from dotenv import load_dotenv
import json
from hashlib import sha256
import logging
from logging.handlers import RotatingFileHandler
from mango_api import models
import os
import pytz
import requests
import time

load_dotenv()
vpbx_api_key = os.getenv("MANGO_KEY")
vpbx_api_sign = os.getenv("MANGO_SALT")

logger = logging.getLogger(__name__)


def get_last_call_history_entry_date():
    latest_database_date = models.CallHistoryGolangVersion.objects.order_by('-data_postupil').first()
    if latest_database_date:
        return latest_database_date.data_postupil


def get_last_call_history_entry_datetime():
    latest_database_datetime = models.CallHistoryGolangVersion.objects.order_by('-date_time_postupil').first()
    if latest_database_datetime:
        return latest_database_datetime.date_time_postupil


def get_utc_time():
    return datetime.utcnow().replace(tzinfo=pytz.utc)


def convert_utc_to_moskow_time(utc_time):
    moscow_tz = pytz.timezone('Europe/Moscow')
    return utc_time.astimezone(moscow_tz)
                

def convert_time_to_string(time):
    return time.strftime("%H:%M:%S")


def prepare_time_seconds_gap(seconds):
    moskow_time_now = convert_utc_to_moskow_time(get_utc_time())
    moskow_time_ago = moskow_time_now - timedelta(seconds=seconds)
    return (
        convert_time_to_string(moskow_time_ago),
        convert_time_to_string(moskow_time_now)
    )



def convert_unix_to_moscow_time(unix_time):
    date_time_utc = datetime.fromtimestamp(unix_time, pytz.utc)
    date_time_moscow = date_time_utc.astimezone(pytz.timezone('Europe/Moscow'))

    return {
        "time": date_time_moscow.strftime("%H:%M:%S"),
        "date": date_time_moscow.strftime("%d.%m.%Y")
    }


def fetch_mango_api_data(json_data, url):
    res = (vpbx_api_key + json_data + vpbx_api_sign).encode('UTF-8')
    sign = sha256(res).hexdigest()
    payload = {
        "vpbx_api_key": vpbx_api_key,
        "sign": sign,
        "json": json_data
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    for i in range(5):
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            time.sleep(60)
    logger.error("Try to get data 5 times, no response")



def prepare_actual_time_segment(time_gap=135):
    time_now_unix = datetime.now().timestamp()
    time_ago_unix = time_now_unix - time_gap

    date_from = convert_unix_to_moscow_time(time_ago_unix)
    date_to = convert_unix_to_moscow_time(time_now_unix)
    return date_from, date_to


def get_call_history_id(date_from, date_to):
    json_data = (f'{{"start_date":"{date_from.get("date")} {date_from.get("time")}", '
                 f'"end_date":"{date_to.get("date")} {date_to.get("time")}", '
                 f'"limit":"5000", '
                 f'"offset":"0"}}')

    response_content = fetch_mango_api_data(json_data, "https://app.mango-office.ru/vpbx/stats/calls/request/")
    return response_content.get("key")


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


def get_call_history_by_id(id):
    json_data = f'{{"key":"{id}"}}'
    for fetch in range(5):
        response = fetch_mango_api_data(json_data,
                                        "https://app.mango-office.ru/vpbx/stats/calls/result/")
        try:
            if response and response.get("data"):    
                calls = response.get("data")[0].get("list")
                if calls:
                    return response

        except (IndexError, TypeError) as e:
            
            time.sleep(60)
            continue
    logger.error("Try to get call history by id 5 times, no response")


def save_data_to_group_golang_version():
    json_response = fetch_mango_api_data(
        "{}",
        "https://app.mango-office.ru/vpbx/groups"
    )
    if not json_response:
        return
    groups = json_response.get("groups")
    existing_ids = set(models.GroupGolangVersion.objects.filter(
        id__in=[group.get("id") for group in groups]
    ).values_list('id', flat=True))
    new_entries = [
        models.GroupGolangVersion(
            id=group.get("id"),
            name=group.get("name")
        )
        for group in groups if group.get("id") not in existing_ids
    ]
    models.GroupGolangVersion.objects.bulk_create(new_entries)


def save_data_to_distribution_schema_golang_version():
    json_response = fetch_mango_api_data(
        "{}",
        "https://app.mango-office.ru/vpbx/schemas"
    )
    if not json_response:
        return
    schemas = json_response.get("data")
    existing_ids = set(models.DistributionSchemaGolangVersion.objects.values_list('id', flat=True))
    new_entries = [
        models.DistributionSchemaGolangVersion(
            id=schema.get("schema_id"),
            name=schema.get("name"),
            description=schema.get("description")
        )
        for schema in schemas if schema.get("schema_id") not in existing_ids
    ]
    models.DistributionSchemaGolangVersion.objects.bulk_create(new_entries)


def save_data_to_operator_golang_version():
    json_response = fetch_mango_api_data(
        f'{{"ext_fields":["groups"]}}',
        "https://app.mango-office.ru/vpbx/config/users/request"
    )
    if not json_response:
        return
    operators = json_response.get("users")
    existing_ids = set(models.OperatorGolangVersion.objects.values_list('id', flat=True))
    new_entries = [
        models.OperatorGolangVersion(
            id = operator.get("telephony").get("extension"),
            name = operator.get("general").get("name"),
            group = operator.get("groups")
        )
        for operator in operators if int(operator.get("telephony").get("extension")) not in existing_ids
    ]
    models.OperatorGolangVersion.objects.bulk_create(new_entries)


def save_data_to_phone_golang_version():
    json_response = fetch_mango_api_data(
        "{}",
        "https://app.mango-office.ru/vpbx/incominglines"
    )
    if not json_response:
        return
    phones = json_response.get("lines")
    existing_numbers = set(models.PhoneGolangVersion.objects.values_list('number', flat=True))
    new_entries = [
        models.PhoneGolangVersion(
            number = phone.get("number"),
            comment = phone.get("comment"),
            schema_id = phone.get("schema_id")
        )
        for phone in phones if phone.get("number") not in existing_numbers
    ]
    models.PhoneGolangVersion.objects.bulk_create(new_entries)


def save_data_to_call_history_golang_version(json_response):
    if not json_response:
        return
    moscow_tz = pytz.timezone('Europe/Moscow')
    calls = json_response.get("data")[0].get("list")
    for call in calls:
         entry_id = call.get("entry_id")
         call_start_time = datetime.fromtimestamp(call.get("context_start_time"), moscow_tz)

         context_calls = call.get("context_calls")
         if context_calls:
            call_end_time  = datetime.fromtimestamp(context_calls[0].get("call_end_time"), moscow_tz)
            gruppa = context_calls[0].get("call_abonent_info")
            recording_id = context_calls[0].get("recording_id")
            members = context_calls[0].get("members")
            if members:
                komu_zvonil = members[0].get("call_abonent_info")
                tel_komu_zvonil = members[0].get("call_abonent_number")
            else:
                komu_zvonil = ''
                tel_komu_zvonil = ''
         else:
             call_end_time = ''
             gruppa = None
             recording_id = None
             komu_zvonil = ''
             tel_komu_zvonil = ''
         napravlenie = create_napravlenie_field(call)
         data_postupil = call_start_time.date() if call_start_time else None
         time_postupil = call_start_time.time() if call_start_time else None
         date_time_postupil = call_start_time if call_start_time else None
         dlitelnost = call.get("duration")
         tel_kto_zvonil = call.get("caller_number")

         kuda_zvonil = call.get("called_number")
         number_name = models.PhoneGolangVersion.objects.filter(number=call.get("called_number")).first()
         komment_k_nomeru = number_name.comment if number_name else None
         data_okonchania_razgovora = call_end_time.date() if call_end_time else None
         time_okonchania_razgovora = call_end_time.time() if call_end_time else None

         try:
            models.CallHistoryGolangVersion.objects.get_or_create(
                entry_id=entry_id,
                defaults={
                    'napravlenie': napravlenie,
                    'data_postupil': data_postupil,
                    'time_postupil': time_postupil,
                    'date_time_postupil': date_time_postupil,
                    'dlitelnost': dlitelnost,
                    'gruppa': gruppa,
                    'tel_kto_zvonil': tel_kto_zvonil,
                    'komu_zvonil': komu_zvonil,
                    'tel_komu_zvonil': tel_komu_zvonil,
                    'kuda_zvonil': kuda_zvonil,
                    'komment_k_nomeru': komment_k_nomeru,
                    'data_okonchania_razgovora': data_okonchania_razgovora,
                    'time_okonchania_razgovora': time_okonchania_razgovora,
                    'recording_id': recording_id
                }
            )
         except IntegrityError:
            logger.info(f"entry_id already exsist in database")
            continue
            

def test_call_history():
    date_from, date_to = prepare_actual_time_segment(4000)
    print("dates:", date_from, date_to)
    call_history_id = get_call_history_id(date_from, date_to)
    print("id:", call_history_id)
    time.sleep(5)
    call_history_response = get_call_history_by_id(call_history_id)
    save_data_to_call_history_golang_version(call_history_response)


def create_dates_sequence(start_date):
    """
    Dividing the time gap between last day in a CallHistoryGolangVersion and preset date into dates
    """
    end_date = datetime.now()
    return [date.strftime("%d.%m.%Y") for date in rrule(DAILY, dtstart=start_date, until=end_date)]


def get_call_history_by_dates(dates_sequence, start_time="00:00:00", end_time="23:59:59"):
    for date in dates_sequence:
        print(f"Записываем данные за дату {date}")
        date_from = {
        "time": start_time,
        "date": date
    }
        date_to = {
            "time": end_time,
            "date": date
        }
        call_history_id = get_call_history_id(date_from, date_to)
        call_history_response = get_call_history_by_id(call_history_id)
        save_data_to_call_history_golang_version(call_history_response)
        
            
@shared_task
def get_call_history_by_one_minute():
    time_70_sec_ago, time_now = prepare_time_seconds_gap(270)
    dates_sequence = create_dates_sequence(date.today())
    get_call_history_by_dates(dates_sequence, time_70_sec_ago, time_now)


@shared_task
def get_call_history_from_the_last_date_in_db():
    start_date = get_last_call_history_entry_date()
    dates_sequence = create_dates_sequence(start_date)
    get_call_history_by_dates(dates_sequence)


@shared_task
def get_call_history_from_the_last_week():
    start_date = datetime.now() - timedelta(days=7)
    dates_sequence = create_dates_sequence(start_date.date())
    get_call_history_by_dates(dates_sequence)

@shared_task
def get_call_history_from_the_last_month():
    start_date = datetime.now() - timedelta(days=30)
    dates_sequence = create_dates_sequence(start_date.date())
    get_call_history_by_dates(dates_sequence)


@shared_task
def update_tables_except_call_history():
    save_data_to_group_golang_version()
    save_data_to_distribution_schema_golang_version()
    save_data_to_operator_golang_version()
    save_data_to_phone_golang_version()


@shared_task
def run_database_update_on_app_start():
    save_data_to_group_golang_version()
    save_data_to_distribution_schema_golang_version()
    save_data_to_operator_golang_version()
    save_data_to_phone_golang_version()
    get_call_history_from_the_last_date_in_db()

