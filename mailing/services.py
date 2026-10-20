from django.core.mail import send_mail
from django.utils import timezone
from .models import Mailing, MailingAttempt


def send_mailing(mailing_id: int) -> dict:
    """
    Выполняет отправку рассылки по ID.
    Возвращает словарь с результатами: {
        'success_count': int,
        'fail_count': int,
        'errors': list
    }
    """
    mailing = Mailing.objects.get(pk=mailing_id)
    now = timezone.now()

    # 1. Обновление статуса
    mailing.update_status()

    # 2. Валидация временного окна
    if not (mailing.start_time <= now <= mailing.end_time):
        raise PermissionError("Отправка запрещена: текущее время вне окна рассылки.")

    success_count = 0
    fail_count = 0
    errors = []

    # 3. Цикл по получателям
    for recipient in mailing.recipients.all():
        try:
            # Отправка письма
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email='noreply@projectshop.com',  # Укажите ваш email
                recipient_list=[recipient.email],
                fail_silently=False  # Важно: выбрасывает исключение при ошибке
            )

            # Запись успешной попытки
            MailingAttempt.objects.create(
                mailing=mailing,
                recipient=recipient,
                status='Успешно',
                server_response='OK'
            )
            success_count += 1

        except Exception as e:
            # Запись неудачной попытки
            MailingAttempt.objects.create(
                mailing=mailing,
                recipient=recipient,
                status='Не успешно',
                server_response=str(e)
            )
            fail_count += 1
            errors.append(f"Ошибка для {recipient.email}: {str(e)}")

    return {
        'success_count': success_count,
        'fail_count': fail_count,
        'errors': errors
    }
