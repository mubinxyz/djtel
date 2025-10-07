# botapp/bot/bot.py

import telebot
from django.conf import settings
from botapp.models import TelegramUser, UserAlert, UserCustom

# Choose between webhook or polling
USE_WEBHOOK = False
WEBHOOK_URL = "https://yourdomain.com"  # change later


class MaCrossBot:
    def __init__(self):
        self.bot = telebot.TeleBot(settings.BOT_TOKEN, parse_mode="HTML")
        self._register_handlers()

    def _register_handlers(self):
        """Register all command/message handlers"""

        @self.bot.message_handler(commands=['start'])
        def start_handler(message):
            user, created = TelegramUser.objects.get_or_create(
                uid=message.from_user.id,
                defaults={'username': message.from_user.username}
            )
            if created:
                text = f"👋 Welcome, {message.from_user.username or 'friend'}! You are now registered."
            else:
                text = f"Welcome back, {message.from_user.username or 'friend'}!"
            self.bot.send_message(message.chat.id, text)

        @self.bot.message_handler(commands=['setcustom'])
        def set_custom_handler(message):
            try:
                # Example: /setcustom tp 0.004
                _, key, value = message.text.split(maxsplit=2)
                user = TelegramUser.objects.get(uid=message.from_user.id)
                UserCustom.objects.update_or_create(user=user, key=key, defaults={'value': value})
                self.bot.send_message(message.chat.id, f"✅ Custom setting saved: {key} = {value}")
            except Exception as e:
                self.bot.send_message(message.chat.id, f"❌ Error: {e}")

        @self.bot.message_handler(commands=['listcustoms'])
        def list_customs(message):
            user = TelegramUser.objects.get(uid=message.from_user.id)
            customs = user.customs.all()
            if not customs:
                self.bot.send_message(message.chat.id, "No custom settings yet.")
                return
            msg = "\n".join([f"• <b>{c.key}</b>: {c.value}" for c in customs])
            self.bot.send_message(message.chat.id, msg)

        @self.bot.message_handler(func=lambda msg: True)
        def echo_handler(message):
            """Simple echo for now"""
            self.bot.send_message(message.chat.id, f"You said: {message.text}")

    # --------------------------
    # Run Modes
    # --------------------------
    def run_polling(self):
        self.bot.remove_webhook()
        print("🤖 Bot running in POLLING mode...")
        self.bot.infinity_polling(skip_pending=True)

    def run_webhook(self):
        print("🤖 Bot running in WEBHOOK mode...")
        self.bot.remove_webhook()
        self.bot.set_webhook(url=WEBHOOK_URL)

    def run(self):
        if USE_WEBHOOK:
            self.run_webhook()
        else:
            self.run_polling()


django_bot = MaCrossBot()
