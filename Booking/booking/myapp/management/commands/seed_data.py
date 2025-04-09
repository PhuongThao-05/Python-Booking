from django.core.management.base import BaseCommand
from myapp.seeder import seed_acount,seed_users,seed_partner,seed_hotel

class Command(BaseCommand):
    help = 'Seed data for the database'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')
        # seed_acount()  
        # seed_users()    
        # seed_partner()
        seed_hotel()
        self.stdout.write(self.style.SUCCESS('Seeding completed successfully.'))
