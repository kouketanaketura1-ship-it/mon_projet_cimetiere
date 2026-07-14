# pages/admin.py
# EMPLACEMENT : frontend/pages/admin.py
# CORRECTIONS :
#   - page.show_dialog() / page.pop_dialog() → dialog.open + page.overlay
#   - Dialog réutilisable (plus de création dynamique à chaque clic)
#   - charger_utilisateurs dans un thread pour éviter asyncio.run()
import flet as ft
import threading
from pages.layout import build_layout
from utils.api import api_get_users, api_update_user


def create_admin_view(page, naviguer):
    """Page d'administration"""

    def notifier(message, succes=True):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN_600 if succes else ft.Colors.RED_600,
        )
        page.snack_bar.open = True
        page.update()

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Email")),
            ft.DataColumn(ft.Text("Nom")),
            ft.DataColumn(ft.Text("Rôle")),
            ft.DataColumn(ft.Text("Action")),
        ],
        rows=[],
    )

    couleurs_role = {
        "ADMIN":      ft.Colors.PURPLE_400,
        "AGENT":      ft.Colors.BLUE_400,
        "SECRETAIRE": ft.Colors.TEAL_400,
        "CLIENT":     ft.Colors.GREY_600,
    }

    # ---- Dialog modification ----
    dialog_email_txt = ft.Text("", size=14, color=ft.Colors.BLUE_GREY_600)
    nom_field     = ft.TextField(label="Nom",    width=300)
    prenom_field  = ft.TextField(label="Prénom", width=300)
    role_dropdown = ft.Dropdown(
        label="Rôle",
        options=[
            ft.dropdown.Option("ADMIN",      "Administrateur"),
            ft.dropdown.Option("AGENT",      "Agent de terrain"),
            ft.dropdown.Option("SECRETAIRE", "Secrétariat"),
            ft.dropdown.Option("CLIENT",     "Client"),
        ],
        width=300,
    )
    utilisateur_courant = {"id": None, "email": ""}

    def fermer_dialog(e=None):
        dialog_modif.open = False
        page.update()

    def sauvegarder(e):
        statut, resultat = api_update_user(
            utilisateur_courant["id"],
            nom=nom_field.value,
            prenom=prenom_field.value,
            role=role_dropdown.value,
        )
        if statut == 200:
            fermer_dialog()
            notifier(f"✅ Utilisateur {utilisateur_courant['email']} mis à jour")
            threading.Thread(target=charger_utilisateurs, daemon=True).start()
        else:
            notifier(f"❌ {resultat.get('error', 'Erreur inconnue')}", succes=False)

    dialog_modif = ft.AlertDialog(
        modal=True,
        title=ft.Text("✏️ Modifier un utilisateur"),
        content=ft.Column([dialog_email_txt, nom_field, prenom_field, role_dropdown],
                          tight=True, spacing=10),
        actions=[
            ft.TextButton("Annuler", on_click=fermer_dialog),
            ft.ElevatedButton("Enregistrer", on_click=sauvegarder,
                              bgcolor="#4f46e5", color=ft.Colors.WHITE),
        ],
    )
    page.overlay.append(dialog_modif)

    def ouvrir_dialog_modif(u):
        utilisateur_courant["id"]    = u["id"]
        utilisateur_courant["email"] = u["email"]
        dialog_email_txt.value = f"📧 {u['email']}"
        nom_field.value        = u.get("nom", "")
        prenom_field.value     = u.get("prenom", "")
        role_dropdown.value    = u.get("role", "CLIENT")
        dialog_modif.open = True
        page.update()

    def charger_utilisateurs():
        statut, users = api_get_users()
        table.rows.clear()
        if statut != 200 or not isinstance(users, list):
            notifier("❌ Impossible de charger les utilisateurs (Django est-il lancé ?)", succes=False)
            page.update()
            return
        for u in users:
            couleur = couleurs_role.get(u.get("role", "CLIENT"), ft.Colors.GREY_600)
            table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(u["email"])),
                    ft.DataCell(ft.Text(f"{u.get('prenom','')} {u.get('nom','')}")),
                    ft.DataCell(ft.Container(content=ft.Text(u.get("role", "—"), color=couleur))),
                    ft.DataCell(ft.ElevatedButton(
                        "Modifier", bgcolor="#4f46e5", color=ft.Colors.WHITE,
                        on_click=lambda e, utilisateur=u: ouvrir_dialog_modif(utilisateur),
                    )),
                ])
            )
        page.update()

    content = ft.Column([
        ft.Row([ft.Column([
            ft.Text("⚙️ Administration", size=24, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ft.Text("Gestion des utilisateurs et rôles", size=14, color=ft.Colors.BLUE_GREY_600),
        ])]),
        ft.Divider(height=15),
        ft.Container(
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=20,
            content=ft.Column([
                ft.Text("👥 Gestion des utilisateurs", size=18, weight=ft.FontWeight.BOLD, color="#0f172a"),
                table,
            ]),
        ),
    ], spacing=5)

    build_layout(page, "admin", naviguer, content)
    threading.Thread(target=charger_utilisateurs, daemon=True).start()