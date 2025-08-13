from django.core.management.base import BaseCommand
from mongo_models import MongoUser

class Command(BaseCommand):
    help = 'Promotes a user to an admin role in MongoDB.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='The email address of the user to promote.')

    def handle(self, *args, **options):
        email = options['email']
        user = MongoUser.get_by_email(email)

        if not user:
            self.stdout.write(self.style.ERROR(f'User with email "{email}" not found.'))
            return

        if user.role == 'admin':
            self.stdout.write(self.style.WARNING(f'User "{email}" is already an admin.'))
            return

        user.data['role'] = 'admin'
        user.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully promoted user "{email}" to admin.'))
