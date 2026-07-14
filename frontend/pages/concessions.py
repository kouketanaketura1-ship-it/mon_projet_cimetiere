# pages/concessions.py
# EMPLACEMENT : frontend/pages/concessions.py
# CORRECTION :
#   - api_get_caveaux dans un thread dans ouvrir_dialog_nouvelle
#   - api_get_concessions dans un thread
#   - api_creer_concession dans un thread
import flet as ft
import threading
from pages.layout import build_layout
from utils.api import api_get_concessions, api_creer_concession, api_get_caveaux

COULEURS_STATUT = {
    "ACTIVE":         ("🟢 Active",         ft.Colors.GREEN_400),
    "EXPIRE_BIENTOT": ("🟡 Expire bientôt", ft.Colors.ORANGE_400),
    "EXPIREE":        ("🔴 Expirée",         ft.Colors.RED_400),
}


def create_concessions_view(page, naviguer):
    """Page des concessions"""

    def notifier(message, succes=True):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN_600 if succes else ft.Colors.RED_600,
        )
        page.snack_bar.open = True
        page.update()

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Caveau")),
            ft.DataColumn(ft.Text("Propriétaire")),
            ft.DataColumn(ft.Text("Date début")),
            ft.DataColumn(ft.Text("Statut")),
            ft.DataColumn(ft.Text("Action")),
        ],
        rows=[],
    )

    # ---- Dialog détails ----
    detail_content = ft.Column([], tight=True, spacing=8)
    dialog_detail  = ft.AlertDialog(
        title=ft.Text("📜 Détails concession"),
        content=detail_content,
        actions=[ft.TextButton("Fermer", on_click=lambda e: _fermer_detail())],
    )

    def _fermer_detail():
        dialog_detail.open = False
        page.update()

    def voir_details(c):
        dialog_detail.title = ft.Text(f"📜 Concession - Caveau {c['caveau']}")
        detail_content.controls = [
            ft.Text(f"Propriétaire : {c['proprietaire_nom']}"),
            ft.Text(f"Téléphone : {c.get('proprietaire_telephone') or '—'}"),
            ft.Text(f"Type : {c['type_concession']}"),
            ft.Text(f"Date de début : {c['date_debut']}"),
            ft.Text(f"Date de fin : {c.get('date_fin') or '—'}"),
            ft.Text(f"Statut : {COULEURS_STATUT.get(c['statut'], (c['statut'], None))[0]}"),
        ]
        dialog_detail.open = True
        page.update()

    def charger_concessions():
        statut, concessions = api_get_concessions()
        table.rows.clear()
        if statut != 200 or not isinstance(concessions, list):
            notifier("❌ Impossible de charger les concessions", succes=False)
            page.update()
            return
        for c in concessions:
            libelle, couleur = COULEURS_STATUT.get(
                c["statut"], (c["statut"], ft.Colors.GREY_400))
            table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(c["caveau"])),
                ft.DataCell(ft.Text(c["proprietaire_nom"])),
                ft.DataCell(ft.Text(c["date_debut"])),
                ft.DataCell(ft.Container(content=ft.Text(libelle, color=couleur))),
                ft.DataCell(ft.ElevatedButton(
                    "Voir", bgcolor="#4f46e5", color=ft.Colors.WHITE,
                    on_click=lambda e, c=c: voir_details(c),
                )),
            ]))
        page.update()

    # ---- Dialog nouvelle concession ----
    caveau_dd    = ft.Dropdown(label="Caveau (chargement...)", options=[], width=320)
    proprietaire = ft.TextField(label="Nom du propriétaire", width=320)
    telephone    = ft.TextField(label="Téléphone",           width=320)
    email_field  = ft.TextField(label="Email",               width=320)
    type_dd      = ft.Dropdown(
        label="Type de concession", value="TEMPORAIRE",
        options=[
            ft.dropdown.Option("TEMPORAIRE",  "Temporaire"),
            ft.dropdown.Option("PERPETUELLE", "Perpétuelle"),
        ], width=320,
    )
    date_debut = ft.TextField(
        label="Date de début (AAAA-MM-JJ)", width=320, hint_text="2026-07-09")

    dialog_nouvelle = ft.AlertDialog(
        modal=True,
        title=ft.Text("➕ Nouvelle concession"),
        content=ft.Column(
            [caveau_dd, proprietaire, telephone, email_field, type_dd, date_debut],
            tight=True, spacing=10,
        ),
        actions=[],
    )

    def _fermer_nouvelle():
        dialog_nouvelle.open = False
        page.update()

    def creer(e):
        if not caveau_dd.value or not proprietaire.value or not date_debut.value:
            notifier("❌ Champs obligatoires manquants", succes=False)
            return

        def faire():
            statut, resultat = api_creer_concession(
                caveau_id=int(caveau_dd.value),
                proprietaire_nom=proprietaire.value,
                proprietaire_telephone=telephone.value,
                proprietaire_email=email_field.value,
                type_concession=type_dd.value,
                date_debut=date_debut.value,
            )
            if statut == 200:
                _fermer_nouvelle()
                notifier("✅ Concession créée")
                charger_concessions()
            else:
                notifier(f"❌ {resultat.get('error', 'Erreur')}", succes=False)

        threading.Thread(target=faire, daemon=True).start()

    dialog_nouvelle.actions = [
        ft.TextButton("Annuler", on_click=lambda e: _fermer_nouvelle()),
        ft.ElevatedButton("Créer", on_click=creer,
                          bgcolor="#4f46e5", color=ft.Colors.WHITE),
    ]

    def ouvrir_dialog_nouvelle(e):
        # Réinitialiser les champs
        caveau_dd.options    = [ft.dropdown.Option("", "⏳ Chargement...")]
        caveau_dd.value      = None
        proprietaire.value   = ""
        telephone.value      = ""
        email_field.value    = ""
        date_debut.value     = ""
        dialog_nouvelle.open = True
        page.update()

        # Charger les caveaux disponibles dans un thread
        def charger_caveaux():
            statut_c, caveaux = api_get_caveaux()
            dispo = (
                [c for c in caveaux if c.get("statut") == "DISPONIBLE"]
                if statut_c == 200 and isinstance(caveaux, list)
                else []
            )
            caveau_dd.options = [
                ft.dropdown.Option(str(c["id"]), f"{c['numero']} — Section {c['section']}")
                for c in dispo
            ]
            if not dispo:
                caveau_dd.hint_text = "Aucun caveau disponible"
            page.update()

        threading.Thread(target=charger_caveaux, daemon=True).start()

    # Enregistrer les dialogs dans page.overlay
    page.overlay.extend([dialog_detail, dialog_nouvelle])

    content = ft.Column([
        ft.Row([
            ft.Column([
                ft.Text("📜 Concessions", size=24,
                        weight=ft.FontWeight.BOLD, color="#0f172a"),
                ft.Text("Gestion des concessions funéraires", size=14,
                        color=ft.Colors.BLUE_GREY_600),
            ]),
            ft.Container(expand=True),
            ft.ElevatedButton("➕ Nouvelle concession",
                              on_click=ouvrir_dialog_nouvelle,
                              bgcolor="#4f46e5", color=ft.Colors.WHITE),
        ]),
        ft.Divider(height=15),
        ft.Container(
            bgcolor=ft.Colors.WHITE, border_radius=12, padding=20,
            content=ft.Column([
                ft.Text("📋 Liste des concessions", size=18,
                        weight=ft.FontWeight.BOLD, color="#0f172a"),
                table,
            ]),
        ),
    ], spacing=5)

    build_layout(page, "concessions", naviguer, content)
    threading.Thread(target=charger_concessions, daemon=True).start()