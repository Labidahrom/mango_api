from django.http import HttpResponse
from mango_api.api import (
    create_dates_sequence,
    get_call_history_from_the_last_date_in_db,
    get_last_call_history_entry_datetime,
    get_call_history_from_the_last_week,
    get_call_history_from_the_last_month,
    save_data_to_group_golang_version,
    save_data_to_distribution_schema_golang_version,
    save_data_to_operator_golang_version,
    save_data_to_phone_golang_version
    )

from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm
import logging

logger = logging.getLogger(__name__)


def index(request):
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
        messages.success(request, 'Обновляем данные за 2 дня')
        return render(request, 'index.html')

class FetchWeek(View):

    def post(self, request, *args, **kwargs):
        get_call_history_from_the_last_week.delay()
        messages.success(request, 'Обновляем данные за неделю')
        return render(request, 'index.html')
    
class FetchMonth(View):

    def post(self, request, *args, **kwargs):
        get_call_history_from_the_last_month.delay()
        messages.success(request, 'Обновляем данные за месяц')
        return render(request, 'index.html')