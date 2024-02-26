from django.http import HttpResponse
from mango_api.api import (
    create_dates_sequence,
    get_call_history_from_the_last_date_in_db,
    get_last_call_history_entry_datetime,
    get_call_history_from_the_last_week,
    save_data_to_group_golang_version,
    save_data_to_distribution_schema_golang_version,
    save_data_to_operator_golang_version,
    save_data_to_phone_golang_version,
    test_call_history
    )

from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm
import logging

logger = logging.getLogger(__name__)


def index(request):
    logger.info('This is a direct test from a Django view.')
    last_call_history_entry_date = get_last_call_history_entry_datetime()
    return render(request, 'index.html', {
        'last_call_history_entry_date': last_call_history_entry_date
        })


class LoginUser(LoginView):
    template_name = 'login_user.html'
    next_page = reverse_lazy('index')
    form_class = AuthenticationForm


class LogoutUser(LogoutView):
    template_name = 'index.html'
    next_page = reverse_lazy('index')


class FetchTwoDays(View):

    def post(self, request, *args, **kwargs):
        get_call_history_from_the_last_date_in_db.delay()
        return render(request, 'index.html')

class FetchWeek(View):

    def post(self, request, *args, **kwargs):
        get_call_history_from_the_last_week.delay()
        return render(request, 'index.html')