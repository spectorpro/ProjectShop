from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid


class Recipient(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField()  # Убрали unique=True для разделения по юзерам
    full_name = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return self.email


class Message(models.Model):
    subject = models.CharField(max_length=255)
    body = models.TextField()

    def __str__(self):
        return self.subject


class Mailing(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_RUNNING = 'running'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Черновик'),
        (STATUS_RUNNING, 'Запущена'),
        (STATUS_COMPLETED, 'Завершена'),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    is_enabled = models.BooleanField(default=True)  # Флаг блокировки менеджером

    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    recipients = models.ManyToManyField(Recipient)

    def update_status(self):
        now = timezone.now()
        if not self.is_enabled:
            new_status = self.STATUS_DRAFT  # Если отключена менеджером, считаем черновиком
        elif now < self.start_time:
            new_status = self.STATUS_DRAFT
        elif now <= self.end_time:
            new_status = self.STATUS_RUNNING
        else:
            new_status = self.STATUS_COMPLETED

        if self.status != new_status:
            self.status = new_status
            self.save()

    def __str__(self):
        return f"Mailing {self.id} ({self.status})"


class MailingAttempt(models.Model):
    attempt_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)
    server_response = models.TextField(blank=True)
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE)
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE)


class EmailConfirmation(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)
