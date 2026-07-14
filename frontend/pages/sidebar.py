# pages/sidebar.py
import flet as ft

def build_sidebar(page, active_view, naviguer):
    """Menu latéral"""
    menu_items = [
        ("📊 Tableau de Bord", "dashboard"),
        ("🗺️ Cartographie SIG", "cartographie"),
        ("📋 Réservations", "reservations"),
        ("📜 Concessions", "concessions"),
        ("⚰️ Exhumations", "exhumations"),
        ("💰 Facturation", "paiement"),
        ("👤 Profil", "profil"),
        ("⚙️ Administration", "admin"),
        ("📜 Audit", "audit"),
    ]
    
    buttons = []
    for label, view_name in menu_items:
        is_active = view_name == active_view
        buttons.append(
            ft.Container(
                content=ft.TextButton(
                    label,
                    on_click=lambda e, v=view_name: naviguer(v),
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE if is_active else ft.Colors.WHITE70,
                        bgcolor="#4f46e5" if is_active else None,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    width=200,
                ),
                padding=4,
            )
        )
    
    return ft.Container(
        width=240,
        height=page.height,
        bgcolor="#1f2937",
        padding=20,
        content=ft.Column([
            ft.Text("🏛️ Cimetière", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text("Gestion moderne", size=13, color=ft.Colors.BLUE_GREY_200),
            ft.Divider(height=20, color=ft.Colors.WHITE24),
            ft.Column(buttons, spacing=2),
            ft.Container(expand=True),
            ft.Container(
                bgcolor=ft.Colors.RED_900,
                border_radius=8,
                padding=10,
                content=ft.Text("🔔 Alertes (3)", color=ft.Colors.WHITE, size=13, weight=ft.FontWeight.BOLD),
            ),
            ft.Divider(height=10, color=ft.Colors.WHITE24),
            ft.TextButton(
                "🔓 Déconnexion",
                on_click=lambda e: print("Déconnexion"),
                style=ft.ButtonStyle(color=ft.Colors.RED_400),
            ),
        ], alignment=ft.MainAxisAlignment.START),
    )