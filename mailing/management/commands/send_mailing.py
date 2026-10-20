
from django.core.management.base import BaseCommand, CommandError
from .services import send_mailing

class Command(BaseCommand):
    help = 'Запускает рассылку по ID'

    def add_arguments(self, parser):
        parser.add_argument('mailing_id', type=int, help='ID рассылки')

    def handle(self, *args, **options):
        mailing_id = options['mailing_id']
        try:
            result = send_mailing(mailing_id)
            self.stdout.write(self.style.SUCCESS(f'Готово! Успешно: {result["success_count"]}, Ошибок: {result["fail_count"]}'))
            if result['errors']:
                self.stdout.write(self.style.WARNING('Ошибки:'))
                for err in result['errors']:
                    self.stdout.write(f' - {err}')
        except Exception as e:
            raise CommandError(str(e))
