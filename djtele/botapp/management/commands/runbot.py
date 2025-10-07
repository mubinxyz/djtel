from django.core.management.base import BaseCommand
from botapp.bot.bot import django_bot  # our class-based bot

class Command(BaseCommand):
    help = 'Run the Telegram bot (polling mode)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Starting Telegram bot in polling mode..."))
        try:
            django_bot.run_polling()  # we’ll add this method to our class
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("🛑 Bot stopped manually."))
