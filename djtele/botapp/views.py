# botapp/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from botapp.bot.bot import django_bot
import json

@csrf_exempt
def telegram_webhook(request):
    if request.method == "POST":
        try:
            django_bot.process_webhook_update(request.body)
        except Exception as e:
            return JsonResponse({"ok": False, "error": str(e)})
        return HttpResponse("OK")
    else:
        return HttpResponse("Hello, this is your bot webhook endpoint!")
