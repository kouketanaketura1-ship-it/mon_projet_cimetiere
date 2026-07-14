from django.core.management.base import BaseCommand
from cimetiere.models import Caveau, Utilisateur


class Command(BaseCommand):
    help = 'Seed demo data for the cemetery management app'

    def handle(self, *args, **options):
        Caveau.objects.get_or_create(
            numero='A-001',
            defaults={
                'section': 'Section A',
                'bloc': 'Bloc 1',
                'allee': 'Allée 1',
                'latitude': -4.7692,
                'longitude': 11.8664,
                'statut': 'DISPONIBLE',
            },
        )
        Caveau.objects.get_or_create(
            numero='A-002',
            defaults={
                'section': 'Section A',
                'bloc': 'Bloc 1',
                'allee': 'Allée 1',
                'latitude': -4.7693,
                'longitude': 11.8665,
                'statut': 'RESERVE',
            },
        )
        Caveau.objects.get_or_create(
            numero='B-001',
            defaults={
                'section': 'Section B',
                'bloc': 'Bloc 2',
                'allee': 'Allée 2',
                'latitude': -4.7688,
                'longitude': 11.8670,
                'statut': 'OCCUPE',
            },
        )
        Caveau.objects.get_or_create(
            numero='C-001',
            defaults={
                'section': 'Section C',
                'bloc': 'Bloc 3',
                'allee': 'Allée 3',
                'latitude': -4.7685,
                'longitude': 11.8673,
                'statut': 'NON_EXPLOITABLE',
            },
        )
        Utilisateur.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'nom': 'Admin',
                'prenom': 'Super',
                'mot_de_passe': 'pbkdf2_sha256$260000$demo$demo',
                'role': 'SUPER_ADMIN',
                'mfa_active': True,
            },
        )
        self.stdout.write(self.style.SUCCESS('Demo data seeded'))
