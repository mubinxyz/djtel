# botapp/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("bot-webhook/", views.telegram_webhook, name="telegram_webhook"),
]
