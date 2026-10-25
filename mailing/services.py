from django.core.mail import send_mail
from .models import SendAttempt


def send_mailing(mailing_instance):
    """
    Отправляет рассылку и сохраняет попытки через bulk_create.
    Возвращает количество успешных и неуспешных попыток.
    """
    recipients = mailing_instance.recipients.all()

    attempts_to_create = []

    for recipient in recipients:
        success = False
        error_msg = ""

        try:
            send_mail(
                subject=mailing_instance.subject,
                message=mailing_instance.body,
                from_email='noreply@example.com',
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            success = True
        except Exception as e:
            error_msg = str(e)

        attempt = SendAttempt(
            mailing=mailing_instance,
            recipient=recipient,
            success=success,
            error_message=error_msg,
        )
        attempts_to_create.append(attempt)

    # Массовое сохранение одним запросом
    if attempts_to_create:  # защита от пустого списка
        SendAttempt.objects.bulk_create(attempts_to_create, batch_size=100)

    mailing_instance.update_status()
    return len(attempts_to_create)
