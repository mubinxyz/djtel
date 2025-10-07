# botapp/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("bot-webhook/", views.webhook, name="telegram_webhook"),
]
