from django.contrib import admin
from .models import Caveau, Reservation, Utilisateur, MFACode

@admin.register(Caveau)
class CaveauAdmin(admin.ModelAdmin):
    list_display = ('id', 'numero', 'section', 'statut', 'proprietaire_nom')
    list_filter = ('statut', 'section')
    search_fields = ('numero', 'nom_defunt', 'proprietaire_nom')
    ordering = ('section', 'numero')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'caveau', 'client_nom', 'client_prenom', 'statut', 'date_reservation')
    list_filter = ('statut',)
    search_fields = ('client_nom', 'client_prenom', 'client_email')

@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'nom', 'prenom', 'role', 'date_inscription')
    list_filter = ('role',)
    search_fields = ('email', 'nom', 'prenom')

@admin.register(MFACode)
class MFACodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur', 'code', 'date_creation', 'est_utilise')
    list_filter = ('est_utilise',)