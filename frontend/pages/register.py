# pages/register.py
import flet as ft
from utils.api import api_register

def build_register_page(page, go_to_login, go_to_mfa):
    """Page d'inscription"""
    page.controls.clear()
    page.bgcolor = "#0f172a"
    page.padding = 20
    
    nom_field = ft.TextField(
        label="📝 Nom",
        width=340,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.BLUE_GREY_900,
        border_radius=10,
    )
    prenom_field = ft.TextField(
        label="📝 Prénom",
        width=340,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.BLUE_GREY_900,
        border_radius=10,
    )
    email_field = ft.TextField(
        label="📧 Email",
        width=340,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.BLUE_GREY_900,
        border_radius=10,
    )
    password_field = ft.TextField(
        label="🔒 Mot de passe",
        password=True,
        width=340,
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.BLUE_GREY_900,
        border_radius=10,
        can_reveal_password=True,
    )
    message = ft.Text("", size=14, color=ft.Colors.WHITE70)
    
    def do_register(e):
        if not all([nom_field.value, prenom_field.value, email_field.value, password_field.value]):
            message.value = "❌ Remplissez tous les champs"
            message.color = ft.Colors.RED_400
            page.update()
            return
        
        status, data = api_register(
            email_field.value,
            password_field.value,
            nom_field.value,
            prenom_field.value
        )
        
        if status == 200:
            message.value = "✅ Compte créé ! Vérifiez vos emails pour le code MFA."
            message.color = ft.Colors.GREEN_400
            page.update()
            go_to_mfa(page, email_field.value)  # ✅ Correction : page ajouté
            return
        
        message.value = f"❌ {data.get('error', 'Erreur')}"
        message.color = ft.Colors.RED_400
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
                            ft.Text("📝", size=45),
                            ft.Text("Créer un compte", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Divider(height=25, color=ft.Colors.WHITE12),
                            nom_field,
                            prenom_field,
                            email_field,
                            password_field,
                            ft.ElevatedButton(
                                "📝 S'inscrire",
                                on_click=do_register,
                                bgcolor="#16a34a",
                                color=ft.Colors.WHITE,
                                width=340,
                            ),
                            ft.Row(
                                [
                                    ft.Text("Déjà un compte ?", color=ft.Colors.WHITE54),
                                    ft.TextButton(
                                        "Se connecter",
                                        on_click=lambda e: go_to_login(page),  # ✅ Correction : page ajouté
                                        style=ft.ButtonStyle(color="#4f46e5"),
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