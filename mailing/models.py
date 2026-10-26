from django.conf import settings
from django.db import models
from django.utils import timezone

class Recipient(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipients'
    )
    email = models.EmailField("Email")
    first_name = models.CharField("Имя", max_length=100, blank=True)
    last_name = models.CharField("Фамилия", max_length=100, blank=True)
    comment = models.TextField("Комментарий", blank=True)

    def __str__(self):
        return f"{self.email} ({self.first_name} {self.last_name})"


class Mailing(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('scheduled', 'Запланирована'),
        ('sending', 'В отправке'),
        ('sent', 'Отправлена'),
        ('failed', 'Ошибка'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mailings'
    )
    # Добавил default, чтобы старые строки не ломались
    subject = models.CharField("Тема", max_length=200, default="Тема рассылки")
    # Добавил default
    body = models.TextField("Текст письма", default="Текст письма по умолчанию")
    # Для дат используем timezone.now (без скобок!)
    start_time = models.DateTimeField("Время старта", default=timezone.now)
    end_time = models.DateTimeField("Время окончания", default=timezone.now)
    recipients = models.ManyToManyField('Recipient', related_name='mailings', blank=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField("Активна", default=True)

    # ВАЖНО: Заменили auto_now_add на default для успешной миграции со старыми данными
    created_at = models.DateTimeField("Дата создания", default=timezone.now, editable=False)

    def __str__(self):
        return self.subject

    def update_status(self):
        if self.attempts.filter(success=False).exists():
            self.status = 'failed'
        elif self.attempts.count() == self.recipients.count():
            self.status = 'sent'
        else:
            self.status = 'sending'
        self.save()


class SendAttempt(models.Model):
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name='attempts')
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE, related_name='attempts')
    success = models.BooleanField("Успешно", default=False)
    error_message = models.TextField("Ошибка", blank=True, null=True)
    sent_at = models.DateTimeField("Отправлено", auto_now_add=True)

    def __str__(self):
        return f"Попытка для {self.recipient.email}: {'OK' if self.success else 'FAIL'}"
