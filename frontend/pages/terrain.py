# pages/terrain.py
import flet as ft
from pages.layout import build_layout
from utils.api import api_get_terrain, api_update_terrain


def create_terrain_view(page, naviguer):
    """Page du terrain"""

    snack = ft.SnackBar(content=ft.Text(""))

    def notifier(message, succes=True):
        snack.content = ft.Text(message)
        snack.bgcolor = ft.Colors.GREEN_600 if succes else ft.Colors.RED_600
        page.show_dialog(snack)

    statut_api, config = api_get_terrain()
    if statut_api != 200 or not isinstance(config, dict):
        config = {
            "superficie_totale": 50000, "zones": "Zone A, Zone B, Zone C",
            "longueur_tombeau": 2.5, "largeur_tombeau": 1.0,
            "zones_non_exploitables": 0, "chemins_m2": 0,
        }
        notifier("⚠️ Impossible de charger la configuration existante, valeurs par défaut affichées", succes=False)

    superficie_field = ft.TextField(label="Superficie totale (m²)", value=str(config["superficie_totale"]), width=300)
    zones_field = ft.TextField(label="Zones", value=config["zones"], width=300)
    longueur_field = ft.TextField(label="Longueur tombeau (m)", value=str(config["longueur_tombeau"]), width=300)
    largeur_field = ft.TextField(label="Largeur tombeau (m)", value=str(config["largeur_tombeau"]), width=300)
    non_exploitables_field = ft.TextField(label="Zones non exploitables", value=str(config["zones_non_exploitables"]), width=300)
    chemins_field = ft.TextField(label="Chemins (m²)", value=str(config["chemins_m2"]), width=300)

    def enregistrer(e):
        try:
            superficie = float(superficie_field.value)
            longueur = float(longueur_field.value)
            largeur = float(largeur_field.value)
            non_exploitables = float(non_exploitables_field.value)
            chemins = float(chemins_field.value)
        except ValueError:
            notifier("❌ Merci d'entrer des nombres valides", succes=False)
            return

        statut, resultat = api_update_terrain(
            superficie_totale=superficie,
            zones=zones_field.value,
            longueur_tombeau=longueur,
            largeur_tombeau=largeur,
            zones_non_exploitables=non_exploitables,
            chemins_m2=chemins,
        )
        if statut == 200:
            notifier("✅ Configuration enregistrée")
        else:
            notifier(f"❌ {resultat.get('error', 'Erreur lors de l’enregistrement')}", succes=False)

    content = ft.Column([
        ft.Row([ft.Column([
            ft.Text("🗺️ Configuration du Terrain", size=24, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ft.Text("Superficie, zones et dimensions", size=14, color=ft.Colors.BLUE_GREY_600),
        ])]),
        ft.Divider(height=15),
        ft.Container(
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=20,
            content=ft.Column([
                ft.Row([superficie_field, zones_field], spacing=20),
                ft.Row([longueur_field, largeur_field], spacing=20),
                ft.Row([non_exploitables_field, chemins_field], spacing=20),
                ft.ElevatedButton("💾 Enregistrer", on_click=enregistrer, bgcolor="#4f46e5", color=ft.Colors.WHITE),
            ]),
        ),
    ], spacing=5)

    build_layout(page, "terrain", naviguer, content)
