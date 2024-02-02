from django.http import HttpResponse
from mango_api.api import (
    create_dates_sequence,
    get_call_history_from_the_last_date_in_db,
    save_data_to_group_golang_version,
    save_data_to_distribution_schema_golang_version,
    save_data_to_operator_golang_version,
    save_data_to_phone_golang_version,
    test_call_history
    )


def index(request):
    get_call_history_from_the_last_date_in_db()
    return HttpResponse("все функции выполнились")