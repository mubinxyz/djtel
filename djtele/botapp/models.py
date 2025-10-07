# botapp/models.py

from django.db import models


class TelegramUser(models.Model):
    """Represents a Telegram user"""
    uid = models.BigIntegerField(unique=True)  # Telegram user_id
    username = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username or str(self.uid)


class UserAlert(models.Model):
    """Stores user-specific alerts"""
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='alerts')
    symbol = models.CharField(max_length=50)
    timeframe = models.CharField(max_length=10)
    ma_fast = models.IntegerField()
    ma_slow = models.IntegerField()
    ma_type = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.user.username} - {self.symbol} ({self.timeframe})"


class UserCustom(models.Model):
    """Stores user-specific custom settings like figsize, sl, tp"""
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, related_name='customs')
    key = models.CharField(max_length=100)
    value = models.JSONField()  # Flexible storage for any type (int, list, dict, etc.)

    def __str__(self):
        return f"{self.user.username} - {self.key}: {self.value}"
