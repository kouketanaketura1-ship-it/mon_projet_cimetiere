# pages/mfa.py
import flet as ft
from pages.dashboard import create_sidebar

def create_mfa_view(page, naviguer):
    page.controls.clear()
    page.bgcolor = "#f5f7fb"
    page.padding = 0
    
    contenu = ft.Container(
        expand=True,
        padding=20,
        content=ft.Column([
            ft.Row([ft.Column([ft.Text("🔐 Sécurité MFA", size=24, weight=ft.FontWeight.BOLD, color="#0f172a"), ft.Text("Gestion de l'authentification à double facteur", size=14, color=ft.Colors.BLUE_GREY_600)])]),
            ft.Divider(height=15),
            ft.Container(
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                padding=20,
                content=ft.Column([
                    ft.Row([ft.Text("✅", size=40), ft.Text("MFA activé", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400)], spacing=10),
                    ft.Text("Votre compte est protégé par l'authentification à double facteur.", color=ft.Colors.BLUE_GREY_600),
                    ft.Divider(height=15),
                    ft.ElevatedButton("📧 Tester l'envoi de code MFA", bgcolor="#4f46e5", color=ft.Colors.WHITE, width=250),
                ]),
            ),
        ], spacing=5),
    )
    
    page.add(ft.Row([create_sidebar(page, "mfa", naviguer), contenu],
                    vertical_alignment=ft.CrossAxisAlignment.START, expand=True))
    page.update()