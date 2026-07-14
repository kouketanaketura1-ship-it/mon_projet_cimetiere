from django.db import models
from django.utils import timezone

class Caveau(models.Model):
    numero = models.CharField(max_length=20, unique=True)
    section = models.CharField(max_length=50)
    bloc = models.CharField(max_length=50, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    longueur = models.FloatField(default=2.5)
    largeur = models.FloatField(default=1.0)
    
    STATUT_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('RESERVE', 'Réservé'),
        ('OCCUPE', 'Occupé'),
        ('NON_EXPLOITABLE', 'Non exploitable'),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='DISPONIBLE')
    
    nom_defunt = models.CharField(max_length=100, blank=True, null=True)
    proprietaire_nom = models.CharField(max_length=100, blank=True, null=True)
    
    # ⚠️ AJOUTE CE CHAMP SI CE N'EST PAS DÉJÀ FAIT
    date_creation = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    def __str__(self):
        return f"Caveau {self.numero}"


class Reservation(models.Model):
    caveau = models.ForeignKey(Caveau, on_delete=models.CASCADE)
    
    client_nom = models.CharField(max_length=100)
    client_prenom = models.CharField(max_length=100)
    client_email = models.EmailField()
    client_telephone = models.CharField(max_length=20)
    
    nom_defunt = models.CharField(max_length=100)
    prenom_defunt = models.CharField(max_length=100)
    date_naissance = models.DateField()
    date_deces = models.DateField()
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('VALIDE', 'Validé'),
        ('REFUSE', 'Refusé'),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    
    date_reservation = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Réservation {self.id}"


class Utilisateur(models.Model):
    ROLES = [
        ('ADMIN', 'Administrateur'),
        ('AGENT', 'Agent de terrain'),
        ('SECRETAIRE', 'Secrétariat'),
        ('CLIENT', 'Client'),
    ]
    
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mot_de_passe = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLES, default='CLIENT')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    date_inscription = models.DateTimeField(auto_now_add=True)
    mfa_active = models.BooleanField(default=True)
    est_actif = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.email} - {self.role}"


class MFACode(models.Model):
    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField()
    est_utilise = models.BooleanField(default=False)
    
    def est_valide(self):
        from django.utils import timezone
        return not self.est_utilise and self.date_expiration > timezone.now()


class Concession(models.Model):
    TYPE_CHOICES = [
        ('TEMPORAIRE', 'Temporaire'),
        ('PERPETUELLE', 'Perpétuelle'),
    ]

    caveau = models.ForeignKey(Caveau, on_delete=models.CASCADE, blank=True, null=True, related_name='concessions')
    proprietaire_nom = models.CharField(max_length=200)
    proprietaire_telephone = models.CharField(max_length=20, blank=True, null=True)
    proprietaire_email = models.EmailField(blank=True, null=True)
    type_concession = models.CharField(max_length=20, choices=TYPE_CHOICES, default='TEMPORAIRE')
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    date_renouvellement = models.DateField(blank=True, null=True)
    est_active = models.BooleanField(default=True)
    document_scan = models.FileField(upload_to='concessions/', blank=True, null=True)

    def __str__(self):
        return f"Concession {self.caveau.numero if self.caveau else '?'} - {self.proprietaire_nom}"


class Exhumation(models.Model):
    STATUT_CHOICES = [
        ('DEMANDE', 'Demande'),
        ('EN_ATTENTE', 'En attente de validation'),
        ('APPROUVEE', 'Approuvée'),
        ('REFUSEE', 'Refusée'),
        ('REALISEE', 'Réalisée'),
    ]

    concession = models.ForeignKey(Concession, on_delete=models.CASCADE, blank=True, null=True)
    defunt_nom = models.CharField(max_length=200)
    defunt_prenom = models.CharField(max_length=200, blank=True, default='')
    demandeur_nom = models.CharField(max_length=150, blank=True, default='')
    demandeur_telephone = models.CharField(max_length=20, blank=True, null=True)
    date_deces = models.DateField(blank=True, null=True)
    date_demande = models.DateTimeField(auto_now_add=True)
    date_exhumation = models.DateField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='DEMANDE')
    raison = models.TextField(blank=True, default='')
    lieu_depot = models.CharField(max_length=200, blank=True, null=True)
    autorisation = models.FileField(upload_to='exhumations/', blank=True, null=True)

    def __str__(self):
        return f"Exhumation {self.id} - {self.defunt_nom}"


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('MOBILE_MONEY', 'Mobile Money'),
        ('AIRTEL_MONEY', 'Airtel Money'),
        ('ESPECE', 'Espèces'),
        ('VIREMENT', 'Virement'),
    ]
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('VALIDE', 'Validé'),
        ('ANNULE', 'Annulé'),
    ]

    concession = models.ForeignKey(Concession, on_delete=models.CASCADE, blank=True, null=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    type_paiement = models.CharField(max_length=20, choices=TYPE_CHOICES)
    numero_telephone = models.CharField(max_length=20, blank=True, null=True)
    reference = models.CharField(max_length=100, unique=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    date_transaction = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(blank=True, null=True)
    commentaire = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Transaction {self.reference} - {self.montant}"


class AuditLog(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, blank=True, null=True)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    adresse_ip = models.GenericIPAddressField(blank=True, null=True)
    date_action = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date_action} - {self.action}"


class ConfigurationTerrain(models.Model):
    superficie_totale = models.FloatField(default=50000)
    zones = models.CharField(max_length=255, default="Zone A, Zone B, Zone C")
    longueur_tombeau = models.FloatField(default=2.5)
    largeur_tombeau = models.FloatField(default=1.0)
    zones_non_exploitables = models.FloatField(default=0)
    chemins_m2 = models.FloatField(default=0)

    def __str__(self):
        return "Configuration du terrain"