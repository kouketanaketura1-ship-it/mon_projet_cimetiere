# pages/reservations.py
# EMPLACEMENT : frontend/pages/reservations.py
# CORRECTIONS :
#   - page.show_dialog() → page.snack_bar (compatible mode web)
#   - api_get_caveaux dans un thread pour éviter asyncio.run()
#   - Dropdown mis à jour dynamiquement après chargement
import flet as ft
import threading
from pages.layout import build_layout
from utils.api import api_get_caveaux, api_creer_reservation


def create_reservations_view(page, naviguer):
    """Page de réservation"""

    def notifier(message, succes=True):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN_600 if succes else ft.Colors.RED_600,
        )
        page.snack_bar.open = True
        page.update()

    caveau_dropdown = ft.Dropdown(
        label="Choisir un caveau disponible",
        options=[],
        width=400,
        bgcolor=ft.Colors.WHITE,
        hint_text="Chargement des caveaux...",
    )

    def charger_caveaux():
        statut_api, tous_caveaux = api_get_caveaux()
        if statut_api != 200 or not isinstance(tous_caveaux, list):
            caveau_dropdown.hint_text = "Erreur de chargement — Django lancé ?"
            page.update()
            return
        caveaux_dispo = [c for c in tous_caveaux if c.get("statut") == "DISPONIBLE"]
        caveau_dropdown.options = [
            ft.dropdown.Option(str(c["id"]), f"{c['numero']} - Section {c['section']} 🟢 Disponible")
            for c in caveaux_dispo
        ]
        if not caveaux_dispo:
            caveau_dropdown.hint_text = "Aucun caveau disponible actuellement"
        else:
            caveau_dropdown.hint_text = f"{len(caveaux_dispo)} caveau(x) disponible(s)"
        page.update()

    threading.Thread(target=charger_caveaux, daemon=True).start()

    nom_field           = ft.TextField(label="Nom",                            width=300)
    prenom_field        = ft.TextField(label="Prénom",                         width=300)
    email_field         = ft.TextField(label="Email",                          width=300)
    telephone_field     = ft.TextField(label="Téléphone",                      width=300)
    nom_defunt_field    = ft.TextField(label="Nom du défunt",                  width=300)
    prenom_defunt_field = ft.TextField(label="Prénom du défunt",               width=300)
    date_naissance_field = ft.TextField(label="Date de naissance (AAAA-MM-JJ)", width=300, hint_text="1950-01-15")
    date_deces_field    = ft.TextField(label="Date de décès (AAAA-MM-JJ)",     width=300, hint_text="2026-06-01")

    def envoyer_reservation(e):
        champs = [
            caveau_dropdown.value, nom_field.value, prenom_field.value,
            email_field.value, telephone_field.value, nom_defunt_field.value,
            prenom_defunt_field.value, date_naissance_field.value, date_deces_field.value,
        ]
        if not all(champs):
            notifier("❌ Merci de remplir tous les champs", succes=False)
            return

        def faire_reservation():
            statut, resultat = api_creer_reservation(
                caveau_id=int(caveau_dropdown.value),
                client_nom=nom_field.value,
                client_prenom=prenom_field.value,
                client_email=email_field.value,
                client_telephone=telephone_field.value,
                nom_defunt=nom_defunt_field.value,
                prenom_defunt=prenom_defunt_field.value,
                date_naissance=date_naissance_field.value,
                date_deces=date_deces_field.value,
            )
            if statut == 200:
                notifier("✅ Réservation envoyée avec succès")
                for champ in [nom_field, prenom_field, email_field, telephone_field,
                              nom_defunt_field, prenom_defunt_field,
                              date_naissance_field, date_deces_field]:
                    champ.value = ""
                caveau_dropdown.value = None
                charger_caveaux()
            else:
                notifier(f"❌ {resultat.get('error', 'Erreur lors de la réservation')}", succes=False)

        threading.Thread(target=faire_reservation, daemon=True).start()

    content = ft.Column([
        ft.Row([ft.Column([
            ft.Text("📋 Nouvelle Réservation", size=24, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ft.Text("Sélection du caveau et saisie des informations", size=14, color=ft.Colors.BLUE_GREY_600),
        ])]),
        ft.Divider(height=15),
        ft.Container(
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=20,
            content=ft.Column([
                ft.Text("🪦 Sélection du caveau", size=18, weight=ft.FontWeight.BOLD, color="#0f172a"),
                ft.Divider(height=10),
                caveau_dropdown,
                ft.Divider(height=15),
                ft.Text("👤 Informations du client", size=18, weight=ft.FontWeight.BOLD, color="#0f172a"),
                ft.Divider(height=10),
                ft.Row([nom_field, prenom_field], spacing=20),
                ft.Row([email_field, telephone_field], spacing=20),
                ft.Divider(height=15),
                ft.Text("👤 Informations du défunt", size=18, weight=ft.FontWeight.BOLD, color="#0f172a"),
                ft.Divider(height=10),
                ft.Row([nom_defunt_field, prenom_defunt_field], spacing=20),
                ft.Row([date_naissance_field, date_deces_field], spacing=20),
                ft.Divider(height=20),
                ft.ElevatedButton(
                    "📤 Envoyer la réservation",
                    on_click=envoyer_reservation,
                    bgcolor="#4f46e5", color=ft.Colors.WHITE, width=250,
                ),
            ]),
        ),
    ], spacing=5)

    build_layout(page, "reservations", naviguer, content)