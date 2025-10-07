
# botapp/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from botapp.bot.bot import django_bot

@csrf_exempt
def webhook(request):
    print("\n=== Webhook Request Received ===")
    print(f"Method: {request.method}")
    print(f"Headers: {dict(request.headers)}")
    if request.method == "POST":
        try:
            print(f"Body length: {len(request.body)} bytes")
            django_bot.process_webhook_update(request.body)
            print("Successfully processed webhook update")
            return JsonResponse({"ok": True})
        except Exception as e:
            print(f"Error processing webhook: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"ok": False, "error": str(e)}, status=500)
    return JsonResponse({"status": "running"})
