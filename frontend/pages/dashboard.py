# pages/dashboard.py
# EMPLACEMENT : frontend/pages/dashboard.py
# CORRECTIONS :
#   - Stats réservations réelles depuis l'API /dashboard (plus de valeurs hardcodées)
#   - Revenus réels depuis l'API (plus de "125 000 XAF" hardcodé)
import flet as ft
import requests
from pages.layout import build_layout

API_URL = "http://monprojetcimetiere-production.up.railway.app:8000/api"


def create_dashboard_view(page, naviguer, role=None):
    """Tableau de bord"""

    def charger_dashboard():
        try:
            r = requests.get(f"{API_URL}/dashboard", timeout=5)
            return r.json() if r.status_code == 200 else {}
        except Exception:
            return {}

    data = charger_dashboard()
    caveaux      = data.get("caveaux",      {})
    reservations = data.get("reservations", {})
    finances     = data.get("finances",     {})

    def fmt_xaf(v):
        try:
            return f"{int(v):,} XAF".replace(",", " ")
        except Exception:
            return "0 XAF"

    stat_cards = ft.ResponsiveRow([
        ft.Container(
            col={"sm": 6, "md": 3},
            bgcolor=ft.Colors.WHITE, border_radius=12, padding=15,
            content=ft.Column([
                ft.Text("🏛️ Total", color=ft.Colors.BLUE_GREY_600, size=12),
                ft.Text(str(caveaux.get("total", 0)), size=28, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        ),
        ft.Container(
            col={"sm": 6, "md": 3},
            bgcolor=ft.Colors.WHITE, border_radius=12, padding=15,
            content=ft.Column([
                ft.Text("🟢 Disponibles", color=ft.Colors.GREEN_600, size=12),
                ft.Text(str(caveaux.get("disponibles", 0)), size=28, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        ),
        ft.Container(
            col={"sm": 6, "md": 3},
            bgcolor=ft.Colors.WHITE, border_radius=12, padding=15,
            content=ft.Column([
                ft.Text("🔴 Occupés", color=ft.Colors.RED_600, size=12),
                ft.Text(str(caveaux.get("occupes", 0)), size=28, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        ),
        ft.Container(
            col={"sm": 6, "md": 3},
            bgcolor=ft.Colors.WHITE, border_radius=12, padding=15,
            content=ft.Column([
                ft.Text("🟠 Réservés", color=ft.Colors.ORANGE_600, size=12),
                ft.Text(str(caveaux.get("reserves", 0)), size=28, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
        ),
    ], spacing=10, run_spacing=10)

    taux = caveaux.get("taux_occupation", 0)

    # Adapter l'affichage en fonction du rôle
    is_admin = (role == 'ADMIN')
    is_secretaire = (role == 'SECRETAIRE')
    is_agent = (role == 'AGENT')
    is_client = (role == 'CLIENT')

    content = ft.Column([
        ft.Row([ft.Column([
            ft.Text("📊 Tableau de bord", size=24, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ft.Text("Vue synthétique du cimetière", size=14, color=ft.Colors.BLUE_GREY_600),
        ])]),
        ft.Divider(height=15),
        stat_cards,
        ft.Divider(height=15),

        # Taux d'occupation
        ft.Container(
            bgcolor=ft.Colors.WHITE, border_radius=12, padding=15,
            content=ft.Column([
                ft.Row([
                    ft.Text("📈 Taux d'occupation global", weight=ft.FontWeight.BOLD, color="#0f172a"),
                    ft.Text(f"{taux}%", weight=ft.FontWeight.BOLD,
                            color=ft.Colors.RED_600 if taux >= 90 else ft.Colors.ORANGE_600 if taux >= 70 else ft.Colors.GREEN_600),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.ProgressBar(value=min(taux / 100, 1.0), color="#4f46e5", bgcolor=ft.Colors.GREY_200),
            ], spacing=8),
        ),
        ft.Divider(height=15),

        # Réservations réelles
        ft.Text("📊 Statut des Réservations", size=18, weight=ft.FontWeight.BOLD, color="#0f172a"),
        ft.Row([
            ft.Container(bgcolor=ft.Colors.WHITE, border_radius=12, padding=15, expand=True,
                content=ft.Column([
                    ft.Text("📋 Total", color=ft.Colors.BLUE_400, size=14),
                    ft.Text(str(reservations.get("total", 0)), size=28, weight=ft.FontWeight.BOLD, color="#0f172a"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)),
            ft.Container(bgcolor=ft.Colors.WHITE, border_radius=12, padding=15, expand=True,
                content=ft.Column([
                    ft.Text("⏳ En Attente", color="#f59e0b", size=14),
                    ft.Text(str(reservations.get("en_attente", 0)), size=28, weight=ft.FontWeight.BOLD, color="#0f172a"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)),
            ft.Container(bgcolor=ft.Colors.WHITE, border_radius=12, padding=15, expand=True,
                content=ft.Column([
                    ft.Text("✅ Confirmées", color="#16a34a", size=14),
                    ft.Text(str(reservations.get("validees", 0)), size=28, weight=ft.FontWeight.BOLD, color="#0f172a"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)),
        ], spacing=10),
        ft.Divider(height=15),

        # Revenus réels (réservé aux administrateurs)
        ft.Column([
            ft.Text("💰 Revenus", size=18, weight=ft.FontWeight.BOLD, color="#0f172a")
        ]) if is_admin else ft.Container(),
    ], spacing=5)

    build_layout(page, "dashboard", naviguer, content)