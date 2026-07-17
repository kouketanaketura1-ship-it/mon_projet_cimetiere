# pages/layout.py
# EMPLACEMENT : frontend/pages/layout.py
# CORRECTIONS :
#   - from main import APP_STATE supprimé (causait asyncio.run() en boucle)
#   - do_logout redirige vers login proprement sans importer APP_STATE
#   - Sidebar hauteur fixée pour le mode web (expand=True sur le Row principal)
import flet as ft

SIDEBAR_COLOR = "#1f2937"
CONTENT_COLOR = "#f5f7fb"
ACCENT        = "#4f46e5"


def build_sidebar(page, active_view, naviguer):
    menu_items = [
        {"label": "📊 Tableau de Bord",   "view": "dashboard"},
        {"label": "🗺️ Cartographie SIG",  "view": "cartographie"},
        {"label": "📋 Réservations",       "view": "reservations"},
        {"label": "📜 Concessions",        "view": "concessions"},
        {"label": "⚰️ Exhumations",        "view": "exhumations"},
        {"label": "💰 Facturation",        "view": "paiement"},
        {"label": "👤 Profil",             "view": "profil"},
        {"label": "⚙️ Administration",     "view": "admin"},
        {"label": "📜 Audit",              "view": "audit"},
        {"label": "📊 Rapports",           "view": "rapports"},
        {"label": "🗺️ Terrain",            "view": "terrain"},
    ]

    buttons = []
    for item in menu_items:
        is_active = item["view"] == active_view
        buttons.append(
            ft.Container(
                content=ft.TextButton(
                    item["label"],
                    on_click=lambda e, v=item["view"]: naviguer(v),
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE if is_active else ft.Colors.WHITE70,
                        bgcolor=ACCENT if is_active else None,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    width=200,
                ),
                padding=4,
            )
        )

    def do_logout(e):
        from pages.login import build_login_page
        # Réinitialiser la page sans importer APP_STATE
        page.controls.clear()
        build_login_page(page, None, None, None)

    # Affiche le logo du projet si présent, sinon un texte
    import os
    logo_candidates = [
        os.path.join(os.path.dirname(__file__), '..', 'pages', 'logo.jpg'),
        os.path.join(os.path.dirname(__file__), '..', 'utils', 'icone.jpg'),
        os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.png'),
    ]
    logo_widget = ft.Text("🏛️ Cimetière", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
    for logo_path in logo_candidates:
        try:
            if os.path.exists(logo_path):
                logo_widget = ft.Image(src=logo_path, width=48, height=48)
                break
        except Exception:
            continue

    return ft.Container(
        width=240,
        bgcolor=SIDEBAR_COLOR,
        padding=20,
        expand_loose=True,
        content=ft.Column([
            logo_widget,
            ft.Text("Gestion moderne", size=13, color=ft.Colors.BLUE_GREY_200),
            ft.Divider(height=20, color=ft.Colors.WHITE24),
            ft.Column(buttons, spacing=2, scroll=ft.ScrollMode.AUTO),
            ft.Container(expand=True),
            ft.Container(
                bgcolor=ft.Colors.RED_900,
                border_radius=8,
                padding=10,
                content=ft.Text("🔔 Alertes (3)", color=ft.Colors.WHITE, size=13,
                                weight=ft.FontWeight.BOLD),
            ),
            ft.Divider(height=10, color=ft.Colors.WHITE24),
            ft.TextButton(
                "🔓 Déconnexion",
                on_click=do_logout,
                style=ft.ButtonStyle(color=ft.Colors.RED_400),
            ),
        ], alignment=ft.MainAxisAlignment.START),
    )


def build_layout(page, active_view, naviguer, content):
    page.controls.clear()
    page.bgcolor = CONTENT_COLOR
    page.padding = 0

    page.add(
        ft.Row(
            [
                build_sidebar(page, active_view, naviguer),
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Column(
                        [content],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        )
    )
    page.update()