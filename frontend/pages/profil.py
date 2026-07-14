# pages/profil.py
# EMPLACEMENT : frontend/pages/profil.py
# CORRECTION :
#   - Plus de "from main import APP_STATE" (causait asyncio.run() en boucle)
#   - email reçu en paramètre depuis main.py
#   - api_get_profil dans un thread séparé
import flet as ft
import threading
from pages.layout import build_layout
from utils.api import api_get_profil, api_update_profil, api_change_password


def create_profil_view(page, naviguer, email=""):
    """Profil utilisateur — email reçu depuis main.py"""

    nom_text    = ft.Text("👤 Chargement...", size=20, weight=ft.FontWeight.BOLD)
    email_text  = ft.Text(f"📧 {email}", color=ft.Colors.BLUE_GREY_600)
    role_text   = ft.Text("🔑 Rôle : ...", color=ft.Colors.BLUE_600)
    stat_res    = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color="#4f46e5")
    stat_val    = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color="#16a34a")
    stat_att    = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color="#f59e0b")
    nom_field       = ft.TextField(label="Nom",       width=320)
    prenom_field    = ft.TextField(label="Prénom",    width=320)
    telephone_field = ft.TextField(label="Téléphone", width=320)

    def notifier(message, succes=True):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN_600 if succes else ft.Colors.RED_600,
        )
        page.snack_bar.open = True
        page.update()

    def charger_profil():
        if not email:
            return
        statut, data = api_get_profil(email)
        if statut == 200 and data:
            nom_text.value   = f"👤 {data.get('prenom', '')} {data.get('nom', '')}"
            email_text.value = f"📧 {data.get('email', email)}"
            role_text.value  = f"🔑 Rôle : {data.get('role', '—')}"
            stat_res.value   = str(data.get("reservations", 0))
            stat_val.value   = str(data.get("validees", 0))
            stat_att.value   = str(data.get("en_attente", 0))
            nom_field.value       = data.get("nom", "")
            prenom_field.value    = data.get("prenom", "")
            telephone_field.value = data.get("telephone") or ""
            page.update()

    threading.Thread(target=charger_profil, daemon=True).start()

    # ---- Dialog modifier profil ----
    def fermer_dialog_profil(e=None):
        dialog_profil.open = False
        page.update()

    def sauvegarder_profil(e):
        if not nom_field.value or not prenom_field.value:
            notifier("❌ Nom et prénom obligatoires", succes=False)
            return
        s, r = api_update_profil(email, nom_field.value, prenom_field.value, telephone_field.value)
        if s == 200:
            nom_text.value = f"👤 {prenom_field.value} {nom_field.value}"
            fermer_dialog_profil()
            notifier("✅ Profil mis à jour")
            page.update()
        else:
            notifier(f"❌ {r.get('error', 'Erreur inconnue')}", succes=False)

    dialog_profil = ft.AlertDialog(
        modal=True,
        title=ft.Text("✏️ Modifier le profil"),
        content=ft.Column([nom_field, prenom_field, telephone_field], tight=True, spacing=10),
        actions=[
            ft.TextButton("Annuler", on_click=fermer_dialog_profil),
            ft.ElevatedButton("Enregistrer", on_click=sauvegarder_profil,
                              bgcolor="#4f46e5", color=ft.Colors.WHITE),
        ],
    )

    def ouvrir_dialog_profil(e):
        dialog_profil.open = True
        page.update()

    # ---- Dialog changer mot de passe ----
    ancien_mdp    = ft.TextField(label="Ancien mot de passe",              password=True, can_reveal_password=True, width=320)
    nouveau_mdp   = ft.TextField(label="Nouveau mot de passe",             password=True, can_reveal_password=True, width=320)
    confirmer_mdp = ft.TextField(label="Confirmer le nouveau mot de passe", password=True, can_reveal_password=True, width=320)

    def fermer_dialog_mdp(e=None):
        dialog_mdp.open = False
        page.update()

    def sauvegarder_mdp(e):
        if not ancien_mdp.value or not nouveau_mdp.value:
            notifier("❌ Remplissez tous les champs", succes=False)
            return
        if nouveau_mdp.value != confirmer_mdp.value:
            notifier("❌ Les mots de passe ne correspondent pas", succes=False)
            return
        s, r = api_change_password(email, ancien_mdp.value, nouveau_mdp.value)
        if s == 200:
            ancien_mdp.value = nouveau_mdp.value = confirmer_mdp.value = ""
            fermer_dialog_mdp()
            notifier("✅ Mot de passe modifié")
        else:
            notifier(f"❌ {r.get('error', 'Erreur inconnue')}", succes=False)

    dialog_mdp = ft.AlertDialog(
        modal=True,
        title=ft.Text("🔑 Changer le mot de passe"),
        content=ft.Column([ancien_mdp, nouveau_mdp, confirmer_mdp], tight=True, spacing=10),
        actions=[
            ft.TextButton("Annuler", on_click=fermer_dialog_mdp),
            ft.ElevatedButton("Valider", on_click=sauvegarder_mdp,
                              bgcolor=ft.Colors.ORANGE_400, color=ft.Colors.WHITE),
        ],
    )

    def ouvrir_dialog_mdp(e):
        dialog_mdp.open = True
        page.update()

    page.overlay.extend([dialog_profil, dialog_mdp])

    content = ft.Column([
        ft.Row([ft.Column([
            ft.Text("👤 Mon Profil", size=24, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ft.Text("Informations et statistiques", size=14, color=ft.Colors.BLUE_GREY_600),
        ])]),
        ft.Divider(height=15),
        ft.Row([
            ft.Container(
                bgcolor=ft.Colors.WHITE, border_radius=12, padding=20, width=350,
                content=ft.Column([
                    ft.Text("📋 Informations", size=18, weight=ft.FontWeight.BOLD, color="#0f172a"),
                    ft.Divider(height=10),
                    nom_text, email_text, role_text,
                    ft.Divider(height=10),
                    ft.ElevatedButton("✏️ Modifier le profil", on_click=ouvrir_dialog_profil,
                                      bgcolor="#4f46e5", color=ft.Colors.WHITE, width=300),
                    ft.ElevatedButton("🔑 Changer le mot de passe", on_click=ouvrir_dialog_mdp,
                                      bgcolor=ft.Colors.ORANGE_400, color=ft.Colors.WHITE, width=300),
                ]),
            ),
            ft.Container(
                bgcolor=ft.Colors.WHITE, border_radius=12, padding=20, expand=True,
                content=ft.Column([
                    ft.Text("📊 Statistiques", size=18, weight=ft.FontWeight.BOLD, color="#0f172a"),
                    ft.Divider(height=10),
                    ft.Row([
                        ft.Container(bgcolor=ft.Colors.BLUE_50, border_radius=8, padding=12, expand=True,
                            content=ft.Column([ft.Text("📋 Réservations", color=ft.Colors.BLUE_GREY_700, size=12), stat_res],
                                             horizontal_alignment=ft.CrossAxisAlignment.CENTER)),
                        ft.Container(bgcolor=ft.Colors.GREEN_50, border_radius=8, padding=12, expand=True,
                            content=ft.Column([ft.Text("✅ Validées", color=ft.Colors.BLUE_GREY_700, size=12), stat_val],
                                             horizontal_alignment=ft.CrossAxisAlignment.CENTER)),
                        ft.Container(bgcolor=ft.Colors.ORANGE_50, border_radius=8, padding=12, expand=True,
                            content=ft.Column([ft.Text("⏳ En attente", color=ft.Colors.BLUE_GREY_700, size=12), stat_att],
                                             horizontal_alignment=ft.CrossAxisAlignment.CENTER)),
                    ], spacing=10),
                ]),
            ),
        ], spacing=20),
    ], spacing=5)

    build_layout(page, "profil", naviguer, content)