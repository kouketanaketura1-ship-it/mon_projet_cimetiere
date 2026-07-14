from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from cimetiere.models import Utilisateur


class Command(BaseCommand):
    help = 'Create a Django superuser and an application super admin `Utilisateur`'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@gmail.com'
        password = 'admin123'

        # Create Django built-in superuser
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Django superuser '{username}' créé."))
        else:
            self.stdout.write(self.style.WARNING(f"Django superuser '{username}' existe déjà."))

        # Create application-level Utilisateur
        if not Utilisateur.objects.filter(email=email).exists():
            Utilisateur.objects.create(
                nom='admin',
                prenom='',
                email=email,
                mot_de_passe=make_password(password),
                role='ADMIN',
                telephone='',
                mfa_active=False,
                est_actif=True,
            )
            self.stdout.write(self.style.SUCCESS("Utilisateur application 'admin' créé."))
        else:
            self.stdout.write(self.style.WARNING("Utilisateur application 'admin' existe déjà."))
