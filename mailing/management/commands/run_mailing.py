from django.core.management.base import BaseCommand
from mailing.models import Mailing
from mailing.services import send_mailing

class Command(BaseCommand):
    help = "Запускает рассылку по ID"

    def add_arguments(self, parser):
        parser.add_argument('mailing_id', type=int, help='ID рассылки')

    def handle(self, *args, **options):
        mailing_id = options['mailing_id']
        try:
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Рассылка с ID {mailing_id} не найдена"))
            return

        count = send_mailing(mailing)
        self.stdout.write(self.style.SUCCESS(f"Обработано получателей: {count}"))
