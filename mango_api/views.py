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

from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm


def index(request):
    return render(request, 'index.html')


class LoginUser(LoginView):
    template_name = 'login_user.html'
    next_page = reverse_lazy('index')
    form_class = AuthenticationForm


class LogoutUser(LogoutView):
    template_name = 'index.html'
    next_page = reverse_lazy('index')