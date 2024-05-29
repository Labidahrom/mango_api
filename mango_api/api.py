import ast
from celery import shared_task
from datetime import date, datetime
from datetime import timedelta
from dateutil.rrule import rrule, DAILY
from django.db import IntegrityError, transaction
from django.utils import timezone
from dotenv import load_dotenv
import json
from hashlib import sha256
import logging
from logging.handlers import RotatingFileHandler
from mango_api import models
import os
import re
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


def fetch_mango_api_record_data(id):
    json_data = f'{{"recording_id": "{id}", "action": "download"}}'
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
        response = requests.post("https://app.mango-office.ru/vpbx/queries/recording/post", headers=headers, data=payload)
        if response.status_code == 200:
            return response.content
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
    elif context_type == 2:
        if context_status:
            napravlenie_data = "Исходящий внешний вызов"
        else:
            napravlenie_data = "Исходящий несостоявшийся"
    elif context_type == 3:
        if context_status:
            napravlenie_data = "Внутренний успешный вызов"
        else:
            napravlenie_data = "Внутренний несостоявшийся"
    else:
        napravlenie_data = "Неизвестный тип вызова"

    return napravlenie_data


def get_call_history_by_id(id):
    json_data = f'{{"key":"{id}"}}'
    for fetch in range(7):
        response = fetch_mango_api_data(json_data,
                                        "https://app.mango-office.ru/vpbx/stats/calls/result/")
        try:
            if response and response.get("data") != []:
                
                calls = response.get("data")[0].get("list")
                if calls:
                    return response
            elif response.get('status') == 'complete' and response.get("data") == []:
                return
            elif response.get('status') == 'work' and response.get("data") == []:
                return
            else:
                print(f"нет ответа сервера по истории звонков: {response}")
                time.sleep(60)
                continue

        except (IndexError, TypeError) as e:
            print("get_call_history_by_id - здесь произошла ошибка")
            time.sleep(60)
            continue

        except Exception as e:
            logger.error(f"Ошибка при получении данных с манго: {str(e)}")
            time.sleep(60)
            continue
    logger.error(f"Try to get call history by id 5 times, no response or no new calls, ключ: {id}")


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


def prepare_operator_group_field(groups):
    if groups and isinstance(groups, list):
        return groups[0]
    else:
        return "0"

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
            group = prepare_operator_group_field(operator.get("groups"))
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


def get_group_by_operator_name(operator_name):
    try:
        group_id = models.OperatorGolangVersion.objects.get(name=operator_name).group
        return models.GroupGolangVersion.objects.get(id=group_id)
    except:
        return ''
    
def format_seconds_to_time(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_telephone_number(phone_number):
    return re.sub(r"7(\d{3})(\d{3})(\d{4})", r"(\1)\2-\3", phone_number)


def process_call(call):    
    moscow_tz = pytz.timezone('Europe/Moscow')
    call_data = {}
    call_data['entry_id'] = call.get("entry_id")



    call_start_time = datetime.fromtimestamp(call.get("context_start_time"), moscow_tz)
    call_data['data_postupil'] = call_start_time.date() if call_start_time else None
    call_data['time_postupil'] = call_start_time.time() if call_start_time else None
    # print(f"это идет в типа в москвоское время разговора в базе {call_data['time_postupil']}")
    call_data['date_time_postupil'] = call_start_time if call_start_time else None
    # print(f"это идет в типа в бывшее ютс время разговора {call_data['date_time_postupil']}")

    context_calls = call.get("context_calls")
    context_type = call.get("context_type")
    
    if context_calls:
        members = context_calls[0].get("members")
        if context_type == 2:
            call_data['komu_zvonil'] = call.get("caller_name")
            call_data['tel_komu_zvonil'] = format_telephone_number(call.get('called_number'))
        else:
            call_data['komu_zvonil'] = members[0].get("call_abonent_info") if members else ''
            call_data['tel_komu_zvonil'] = members[0].get("call_abonent_number") if members else ''
            if call_data['tel_komu_zvonil'] == '':
                call_data['tel_komu_zvonil'] = context_calls[0].get("call_abonent_info")
        call_data['gruppa'] = get_group_by_operator_name(call_data['komu_zvonil'])
        if not call_data['gruppa'] and call_data['komu_zvonil']:
            call_data['gruppa'] = context_calls[0].get("call_abonent_info")
            
        call_end_time  = datetime.fromtimestamp(context_calls[0].get("call_end_time"), moscow_tz)
        call_data['data_okonchania_razgovora'] = call_end_time.date() if call_end_time else None
        call_data['time_okonchania_razgovora'] = call_end_time.time() if call_end_time else None
        
        call_data['recording_id'] = context_calls[0].get("recording_id")
        
        

    else:
        call_data['gruppa'] = None
        call_data['recording_id'] = None
        call_data['komu_zvonil'] = ''
        call_data['tel_komu_zvonil'] = ''
    call_data['napravlenie'] = create_napravlenie_field(call)

    call_data['dlitelnost'] = format_seconds_to_time(call.get("duration"))
    call_data['tel_kto_zvonil'] = format_telephone_number(call.get("caller_number"))
    call_data['kuda_zvonil'] = call.get("called_number")
    number_name = models.PhoneGolangVersion.objects.filter(number=call.get("called_number")).first()
    call_data['komment_k_nomeru'] = number_name.comment if number_name else None
    return call_data


def save_call_to_database(call_data):
    if call_data:
        try:
            obj, created = models.CallHistoryGolangVersion.objects.get_or_create(
                entry_id=call_data.get('entry_id'),
                defaults={
                    'napravlenie': call_data.get('napravlenie'),
                    'data_postupil': call_data.get('data_postupil'),
                    'time_postupil': call_data.get('time_postupil'),
                    'date_time_postupil': call_data.get('date_time_postupil'),
                    'dlitelnost': call_data.get('dlitelnost'),
                    'gruppa': call_data.get('gruppa'),
                    'tel_kto_zvonil': call_data.get('tel_kto_zvonil'),
                    'komu_zvonil': call_data.get('komu_zvonil'),
                    'tel_komu_zvonil': call_data.get('tel_komu_zvonil'),
                    'kuda_zvonil': call_data.get('kuda_zvonil'),
                    'komment_k_nomeru': call_data.get('komment_k_nomeru'),
                    'data_okonchania_razgovora': call_data.get('data_okonchania_razgovora'),
                    'time_okonchania_razgovora': call_data.get('time_okonchania_razgovora'),
                    'recording_id': call_data.get('recording_id')
                }
            )
        except IntegrityError:
            logger.info(f"entry_id already exsist in database")
        except Exception as e:
            logger.info(f"{e}")



def save_data_to_call_history_golang_version(json_response):
    if not json_response:
        return
    json_calls = json_response.get("data")[0].get("list")
    unsorted_calls = []
    for call in json_calls:
        unsorted_calls.append(process_call(call))
    sorted_calls = sorted(unsorted_calls, key=lambda x: x.get("date_time_postupil"))
    for call in sorted_calls:
        save_call_to_database(call)
            


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


def get_recording_ids():
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    recording_ids = models.CallHistoryGolangVersion.objects.filter(
    data_okonchania_razgovora__range=[yesterday, today]
    ).values_list('recording_id', flat=True)
    return recording_ids


def save_recording_ids_to_database(recording_ids):
    recording_list = []
    for i in recording_ids:
        recording_list.extend(ast.literal_eval(i))
    with transaction.atomic():
        for record_id in recording_list:
            recording, created = models.CallRecordingGolangVersion.objects.get_or_create(mango_id=record_id)
            if not created:
                continue


def save_recordings_to_database():
    ids_with_no_recording = list(models.CallRecordingGolangVersion.objects.filter(recording__isnull=True).values_list('mango_id', flat=True))
    for id in ids_with_no_recording:        
        recording_instance = models.CallRecordingGolangVersion.objects.get(mango_id=id)
        audio_recording = fetch_mango_api_record_data(id)
        recording_instance.date = timezone.now().date()
        recording_instance.recording = audio_recording
        recording_instance.save()


def add_recordings_to_database():
    recording_ids = get_recording_ids()
    save_recording_ids_to_database(recording_ids)
    save_recordings_to_database()

            
@shared_task
def get_call_history_by_gap(gap=14400):
    print("качаем звонки за последние 4 часа")
    time_ago, time_now = prepare_time_seconds_gap(gap)
    dates_sequence = create_dates_sequence(date.today())
    get_call_history_by_dates(dates_sequence, time_ago, time_now)
    add_recordings_to_database()
    

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
def get_call_history_from_the_date_now():
    start_date = datetime.now()
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


@shared_task()
def run_database_update_on_app_start():
    save_data_to_group_golang_version()
    save_data_to_distribution_schema_golang_version()
    save_data_to_operator_golang_version()
    save_data_to_phone_golang_version()
    get_call_history_from_the_last_date_in_db()
    add_recordings_to_database()
    

@shared_task()
def get_call_history_from_last_entry():
    last_entry = models.CallHistoryGolangVersion.objects.order_by('-date_time_postupil').first()

    if last_entry and last_entry.date_time_postupil:
        last_entry_date_time = last_entry.date_time_postupil
    else:
        last_entry_date_time = None

    if last_entry_date_time:
        moscow_tz = pytz.timezone('Europe/Moscow')
        last_entry_date_time = last_entry_date_time.astimezone(moscow_tz)
        now_date_time = timezone.now().astimezone(moscow_tz)


        time_gap = now_date_time - last_entry_date_time
        time_gap_hours = time_gap.total_seconds() / 3600
        if time_gap_hours > 24:
            update_tables_except_call_history()
            get_call_history_from_the_last_date_in_db()
        else:
            date_from = {
                "time": last_entry_date_time.strftime('%H:%M:%S'),
                "date": last_entry_date_time.strftime('%d.%m.%Y')
            }
            date_to = {
                "time": now_date_time.strftime('%H:%M:%S'),
                "date": now_date_time.strftime('%d.%m.%Y')
            }
            call_history_id = get_call_history_id(date_from, date_to)
            call_history_response = get_call_history_by_id(call_history_id)
            save_data_to_call_history_golang_version(call_history_response)
            add_recordings_to_database()
    elif not last_entry_date_time:
        update_tables_except_call_history()
        get_call_history_by_gap(500)
