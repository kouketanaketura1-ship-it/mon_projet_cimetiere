# pages/login.py
# EMPLACEMENT : frontend/pages/login.py
# CORRECTIONS :
#   - Champ MFA et bouton "Valider MFA" supprimés du formulaire de connexion
#   - Après login réussi → redirige directement vers mfa_verify.py (page dédiée)
#   - go_to_dashboard_func conservé pour compatibilité avec main.py
import flet as ft
import requests

API_URL = "https://monprojetcimetiere-production.up.railway.app/api"


def build_login_page(page, go_to_register_func, go_to_mfa_func, go_to_dashboard_func=None):
    """Page de connexion — sans champ MFA (géré dans mfa_verify.py)"""
    page.controls.clear()
    page.bgcolor = "#0f172a"
    page.padding = 20

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

    def do_login(e):
        if not email_field.value or not password_field.value:
            message.value = "❌ Remplissez tous les champs"
            message.color = ft.Colors.RED_400
            page.update()
            return

        message.value = "⏳ Connexion en cours..."
        message.color = ft.Colors.AMBER_300
        page.update()

        try:
            response = requests.post(
                f"{API_URL}/auth/login",
                json={"email": email_field.value, "mot_de_passe": password_field.value},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("mfa_required"):
                    # Code MFA envoyé → aller sur la page MFA dédiée
                    go_to_mfa_func(page, email_field.value)
                    return

                go_to_mfa_func(page, email_field.value)
                return

            message.value = f"❌ {response.json().get('error', 'Identifiants incorrects')}"
            message.color = ft.Colors.RED_400
            page.update()

        except requests.exceptions.ConnectionError:
            message.value = "⚠️ Django ne tourne pas ! Lancez 'python manage.py runserver'"
            message.color = ft.Colors.RED_400
            page.update()
        except requests.exceptions.Timeout:
            message.value = "⏱️ Le serveur met trop de temps à répondre."
            message.color = ft.Colors.RED_400
            page.update()
        except Exception as exc:
            message.value = f"❌ {str(exc)}"
            message.color = ft.Colors.RED_400
            page.update()

    def do_register(e):
        go_to_register_func(page)

    page.add(
        ft.Row(
            [
                ft.Container(
                    width=400,
                    bgcolor=ft.Colors.BLUE_GREY_900,
                    border_radius=20,
                    padding=35,
                    content=ft.Column([
                        ft.Text("🏛️", size=45),
                        ft.Text("🔐 Connexion", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text("Système de Gestion Funéraire", size=14, color=ft.Colors.WHITE54),
                        ft.Divider(height=25, color=ft.Colors.WHITE12),
                        email_field,
                        password_field,
                        ft.Row([
                            ft.ElevatedButton(
                                "🔑 Se connecter",
                                on_click=do_login,
                                bgcolor="#4f46e5",
                                color=ft.Colors.WHITE,
                                width=150,
                            ),
                            ft.ElevatedButton(
                                "📝 Créer",
                                on_click=do_register,
                                bgcolor="#16a34a",
                                color=ft.Colors.WHITE,
                                width=150,
                            ),
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                        message,
                        ft.Divider(height=20, color=ft.Colors.WHITE12),
                        ft.Text("© 2026 - Gestion Funéraire", size=11, color=ft.Colors.WHITE38),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
    )
    page.update()
