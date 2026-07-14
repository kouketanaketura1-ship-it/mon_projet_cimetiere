# pages/mfa_verify.py
import flet as ft
from utils.api import api_verify_mfa

def build_mfa_page(page, email, go_to_dashboard, go_to_login):
    """Page de vérification MFA"""
    page.controls.clear()
    page.bgcolor = "#0f172a"
    page.padding = 20
    
    email_display = ft.Text(f"📧 {email}", size=16, color=ft.Colors.WHITE70)
    mfa_field = ft.TextField(
        label="🔐 Code MFA",
        width=340,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.BLUE_GREY_900,
        border_radius=10,
        hint_text="Entrez le code reçu par email",
    )
    message = ft.Text("", size=14, color=ft.Colors.WHITE70)
    
    def do_verify(e):
        if not mfa_field.value:
            message.value = "❌ Entrez le code MFA"
            message.color = ft.Colors.RED_400
            page.update()
            return
        
        status, data = api_verify_mfa(email, mfa_field.value)

        if status == 200:
            message.value = "✅ Code validé ! Accès autorisé."
            message.color = ft.Colors.GREEN_400
            page.update()
            # Récupère le rôle renvoyé par l'API et le passe à la dashboard
            role = data.get('role') if isinstance(data, dict) else None
            go_to_dashboard(page, email, role)
            return
        
        message.value = f"❌ {data.get('error', 'Code invalide')}"
        message.color = ft.Colors.RED_400
        page.update()
    
    def do_resend(e):
        message.value = "📧 Nouveau code envoyé par email (voir terminal)"
        message.color = ft.Colors.AMBER_300
        page.update()
    
    page.add(
        ft.Row(
            [
                ft.Container(
                    width=400,
                    bgcolor=ft.Colors.BLUE_GREY_900,
                    border_radius=20,
                    padding=35,
                    content=ft.Column(
                        [
                            ft.Text("🔐", size=45),
                            ft.Text("Vérification MFA", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text("Un code de vérification a été envoyé par email", size=14, color=ft.Colors.WHITE54),
                            ft.Divider(height=25, color=ft.Colors.WHITE12),
                            email_display,
                            mfa_field,
                            ft.ElevatedButton(
                                "✅ Accéder",
                                on_click=do_verify,
                                bgcolor="#f59e0b",
                                color=ft.Colors.WHITE,
                                width=340,
                            ),
                            ft.TextButton(
                                "📧 Renvoyer le code",
                                on_click=do_resend,
                                style=ft.ButtonStyle(color=ft.Colors.WHITE54),
                            ),
                            ft.Row(
                                [
                                    ft.TextButton(
                                        "🔙 Retour à la connexion",
                                        on_click=lambda e: go_to_login(page),
                                        style=ft.ButtonStyle(color=ft.Colors.WHITE38),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            message,
                            ft.Divider(height=20, color=ft.Colors.WHITE12),
                            ft.Text("© 2026 - Gestion Funéraire", size=11, color=ft.Colors.WHITE38),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
    )
    page.update()