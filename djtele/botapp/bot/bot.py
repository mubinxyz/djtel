# botapp/bot/bot.py

import io
import ast
import matplotlib.pyplot as plt
import telebot
from django.conf import settings
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from .engine.macross import MaCross
from botapp.models import TelegramUser, UserAlert, UserCustom

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import threading
# --------------------------
# Config
# --------------------------
USE_WEBHOOK = True
WEBHOOK_URL = "https://exit-editorials-notes-gradually.trycloudflare.com/bot-webhook/"

class MaCrossBot:
    def __init__(self):
        self.bot = telebot.TeleBot(settings.BOT_TOKEN, parse_mode="HTML")
        self._register_handlers()

    def _register_handlers(self):
        """Register all command/message handlers"""

        # --------------------------
        # START
        # --------------------------
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

        # --------------------------
        # HELP
        # --------------------------
        @self.bot.message_handler(commands=['help'])
        def help_handler(message):
            help_text = (
                "📚 <b>MA Strategy Bot Commands</b>\n\n"
                "1️⃣ /chart <code>&lt;symbol&gt; &lt;tf&gt; [ma_type] [ma_fast] [ma_slow]</code>\n"
                "2️⃣ /hist_chart <code>&lt;symbol&gt; &lt;tf&gt; [ma_type] [ma_fast] [ma_slow]</code>\n"
                "3️⃣ /set_alert <code>&lt;symbol&gt; &lt;tf&gt; &lt;short_ma&gt; &lt;long_ma&gt; [ma_type]</code>\n"
                "4️⃣ /get_alerts\n"
                "5️⃣ /setcustom <code>&lt;key&gt; &lt;value&gt;</code>\n"
                "6️⃣ /listcustoms\n\n"
                "Use commands carefully. All symbols uppercase."
            )
            self.bot.send_message(message.chat.id, help_text, parse_mode="HTML")

        # --------------------------
        # CHART
        # --------------------------
        @self.bot.message_handler(commands=['chart'])
        def chart_handler(message):
            parts = message.text.split()
            if len(parts) < 3:
                self.bot.send_message(
                    message.chat.id,
                    "Usage: /chart <symbol> <tf> [ma_type] [ma_fast] [ma_slow]"
                )
                return

            username = message.from_user.username or str(message.from_user.id)
            symbol = parts[1].upper()
            tf = parts[2].lower()
            ma_type = parts[3] if len(parts) > 3 else "sma"
            ma_fast = int(parts[4]) if len(parts) > 4 else 21
            ma_slow = int(parts[5]) if len(parts) > 5 else 50

            # Load user custom settings
            user = TelegramUser.objects.get(uid=message.from_user.id)
            user_kwargs = {c.key: ast.literal_eval(c.value) for c in user.customs.all()}

            try:
                fig = MaCross(
                    symbol=symbol,
                    interval=tf,
                    ma_type=ma_type,
                    ma_fast=ma_fast,
                    ma_slow=ma_slow,
                    backtest=False,
                    **user_kwargs
                ).run_perc().alert_fig()

                if fig:
                    buf = io.BytesIO()
                    fig.savefig(buf, format="png")
                    buf.seek(0)
                    self.bot.send_photo(
                        message.chat.id,
                        buf,
                        caption=f"<b>{symbol} | {tf} | {ma_type.upper()}({ma_fast},{ma_slow})</b>",
                        parse_mode="HTML"
                    )
                    buf.close()
                    plt.close(fig)

            except Exception as e:
                self.bot.send_message(message.chat.id, f"❌ Error generating chart: {e}")

        # --------------------------
        # HISTORICAL CHART
        # --------------------------
        @self.bot.message_handler(commands=['hist_chart'])
        def hist_chart_handler(message):
            parts = message.text.split()
            if len(parts) < 3:
                self.bot.send_message(
                    message.chat.id,
                    "Usage: /hist_chart <symbol> <tf> [ma_type] [ma_fast] [ma_slow]"
                )
                return

            username = message.from_user.username or str(message.from_user.id)
            symbol = parts[1].upper()
            tf = parts[2].lower()
            ma_type = parts[3] if len(parts) > 3 else "sma"
            ma_fast = int(parts[4]) if len(parts) > 4 else 21
            ma_slow = int(parts[5]) if len(parts) > 5 else 50

            user = TelegramUser.objects.get(uid=message.from_user.id)
            user_kwargs = {c.key: ast.literal_eval(c.value) for c in user.customs.all()}

            try:
                fig = MaCross(
                    symbol=symbol,
                    interval=tf,
                    ma_type=ma_type,
                    ma_fast=ma_fast,
                    ma_slow=ma_slow,
                    backtest=True,
                    **user_kwargs
                ).run_perc().backtest_fig()

                if fig:
                    buf = io.BytesIO()
                    buf.name = f"{symbol}_{tf}.pdf"
                    fig.savefig(buf, format="pdf")
                    buf.seek(0)
                    self.bot.send_document(message.chat.id, buf, caption=f"{symbol} | {tf}")
                    buf.close()
                    plt.close(fig)
            except Exception as e:
                self.bot.send_message(message.chat.id, f"❌ Error generating historical chart: {e}")

        # --------------------------
        # SET ALERT
        # --------------------------
        @self.bot.message_handler(commands=['set_alert'])
        def set_alert_handler(message):
            parts = message.text.split()
            if len(parts) < 5:
                self.bot.send_message(
                    message.chat.id,
                    "Usage: /set_alert <symbol> <tf> <short_ma> <long_ma> [ma_type]"
                )
                return

            symbol = parts[1].upper()
            tf = parts[2].lower()
            try:
                short_ma = int(parts[3])
                long_ma = int(parts[4])
            except ValueError:
                self.bot.send_message(message.chat.id, "short_ma and long_ma must be numbers.")
                return
            ma_type = parts[5] if len(parts) > 5 else "sma"

            user = TelegramUser.objects.get(uid=message.from_user.id)
            alert, created = UserAlert.objects.get_or_create(
                user=user,
                symbol=symbol,
                timeframe=tf,
                ma_fast=short_ma,
                ma_slow=long_ma,
                ma_type=ma_type
            )
            if created:
                self.bot.send_message(
                    message.chat.id,
                    f"✅ Alert set: {symbol} | {tf} | {ma_type.upper()}({short_ma},{long_ma})"
                )
            else:
                self.bot.send_message(
                    message.chat.id,
                    f"⚠️ You already have this alert."
                )

        # --------------------------
        # GET ALERTS
        # --------------------------
        @self.bot.message_handler(commands=['get_alerts'])
        def get_alerts_handler(message):
            user = TelegramUser.objects.get(uid=message.from_user.id)
            alerts = user.alerts.all()
            if not alerts:
                self.bot.send_message(message.chat.id, "⚠️ No active alerts.")
                return

            markup = InlineKeyboardMarkup()
            for alert in alerts:
                btn = InlineKeyboardButton(
                    text=f"❌ {alert.symbol} | {alert.timeframe} | {alert.ma_type.upper()}({alert.ma_fast},{alert.ma_slow})",
                    callback_data=f"delete_alert:{alert.id}"
                )
                markup.add(btn)
            self.bot.send_message(message.chat.id, "📊 Your Active Alerts:", reply_markup=markup)

        # --------------------------
        # DELETE ALERT (callback)
        # --------------------------
        @self.bot.callback_query_handler(func=lambda c: c.data.startswith("delete_alert:"))
        def delete_alert_callback(call):
            alert_id = int(call.data.split(":")[1])
            try:
                alert = UserAlert.objects.get(id=alert_id)
                alert.delete()
                self.bot.answer_callback_query(call.id, "✅ Alert deleted")
                self.bot.edit_message_text(
                    call.message.chat.id,
                    call.message.message_id,
                    "✅ Alert deleted."
                )
            except UserAlert.DoesNotExist:
                self.bot.answer_callback_query(call.id, "⚠️ Alert not found")

        # --------------------------
        # CUSTOM SETTINGS
        # --------------------------
        @self.bot.message_handler(commands=['setcustom'])
        def set_custom_handler(message):
            try:
                _, key, value = message.text.split(maxsplit=2)
                user = TelegramUser.objects.get(uid=message.from_user.id)
                UserCustom.objects.update_or_create(
                    user=user, key=key, defaults={'value': value}
                )
                self.bot.send_message(message.chat.id, f"✅ Custom saved: {key} = {value}")
            except Exception as e:
                self.bot.send_message(message.chat.id, f"❌ Error: {e}")

        @self.bot.message_handler(commands=['listcustoms'])
        def list_customs_handler(message):
            user = TelegramUser.objects.get(uid=message.from_user.id)
            customs = user.customs.all()
            if not customs:
                self.bot.send_message(message.chat.id, "No custom settings.")
                return
            msg = "\n".join([f"• <b>{c.key}</b>: {c.value}" for c in customs])
            self.bot.send_message(message.chat.id, msg)

        # --------------------------
        # ECHO (fallback)
        # --------------------------
        @self.bot.message_handler(func=lambda m: True)
        def echo_handler(message):
            self.bot.send_message(message.chat.id, f"You said: {message.text}")

    # --------------------------
    # RUN MODES
    # --------------------------
    def run_polling(self):
        self.bot.remove_webhook()
        print("🤖 Bot running in POLLING mode...")
        self.bot.infinity_polling(skip_pending=True)

    def run_webhook(self):
        self.bot.remove_webhook()
        self.bot.set_webhook(url=WEBHOOK_URL)
        print("🤖 Bot running in WEBHOOK mode...")

    def process_webhook_update(self, request_body):
        """Process incoming webhook from Django view"""
        update = telebot.types.Update.de_json(request_body.decode("utf-8"))
        # Use a separate thread to avoid blocking
        threading.Thread(target=lambda: self.bot.process_new_updates([update])).start()

    def run(self):
        if USE_WEBHOOK:
            self.run_webhook()
        else:
            self.run_polling()


django_bot = MaCrossBot()
