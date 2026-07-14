# pages/composants.py
import flet as ft

def badge_statut(statut: str):
    """Badge de statut coloré"""
    libelles = {
        "DISPONIBLE": ("🟢 Disponible", ft.Colors.GREEN_400),
        "RESERVE": ("🟠 Réservé", ft.Colors.ORANGE_400),
        "OCCUPE": ("🔴 Occupé", ft.Colors.RED_400),
        "NON_EXPLOITABLE": ("⚪ Non exploitable", ft.Colors.GREY_400),
        "EN_ATTENTE": ("⏳ En attente", ft.Colors.ORANGE_400),
        "VALIDE": ("✅ Validé", ft.Colors.GREEN_400),
        "REFUSE": ("❌ Refusé", ft.Colors.RED_400),
    }
    label, color = libelles.get(statut, (statut, ft.Colors.BLUE_GREY_400))
    return ft.Container(
        content=ft.Text(label, color=ft.Colors.WHITE, size=11, weight=ft.FontWeight.BOLD),
        bgcolor=color,
        padding=ft.padding.all(6),
        border_radius=15,
    )

def carte_statistique(label: str, valeur, icone, couleur):
    """Carte de statistique"""
    return ft.Container(
        bgcolor=ft.Colors.WHITE,
        padding=20,
        border_radius=12,
        expand=True,
        content=ft.Column([
            ft.Icon(icone, color=couleur, size=24),
            ft.Text(str(valeur), size=28, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ft.Text(label, size=13, color=ft.Colors.BLUE_GREY_600),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
    )

def entete_page(titre: str, sous_titre: str):
    """En-tête de page"""
    return ft.Column([
        ft.Text(titre, size=24, weight=ft.FontWeight.BOLD, color="#0f172a"),
        ft.Text(sous_titre, size=14, color=ft.Colors.BLUE_GREY_600),
        ft.Divider(height=10),
    ], spacing=5)