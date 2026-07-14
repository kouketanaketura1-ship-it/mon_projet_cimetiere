# pages/exhumations.py
import flet as ft
from pages.layout import build_layout
from utils.api import api_get_exhumations, api_creer_exhumation, api_update_exhumation

COULEURS_STATUT = {
    "EN_ATTENTE": ("⏳ En attente", ft.Colors.ORANGE_400),
    "APPROUVEE": ("✅ Approuvée", ft.Colors.GREEN_400),
    "REFUSEE": ("❌ Refusée", ft.Colors.RED_400),
}


def create_exhumations_view(page, naviguer):
    """Page des exhumations"""

    snack = ft.SnackBar(content=ft.Text(""))

    def notifier(message, succes=True):
        snack.content = ft.Text(message)
        snack.bgcolor = ft.Colors.GREEN_600 if succes else ft.Colors.RED_600
        page.show_dialog(snack)

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Défunt")),
            ft.DataColumn(ft.Text("Date demande")),
            ft.DataColumn(ft.Text("Statut")),
            ft.DataColumn(ft.Text("Action")),
        ],
        rows=[],
    )

    def charger_exhumations():
        statut, exhumations = api_get_exhumations()
        table.rows.clear()
        if statut != 200 or not isinstance(exhumations, list):
            notifier("❌ Impossible de charger les exhumations", succes=False)
            page.update()
            return
        for ex in exhumations:
            libelle, couleur = COULEURS_STATUT.get(ex["statut"], (ex["statut"], ft.Colors.GREY_400))
            table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(f"E-{ex['id']:03d}")),
                ft.DataCell(ft.Text(ex["nom_defunt"])),
                ft.DataCell(ft.Text(ex["date_demande"])),
                ft.DataCell(ft.Container(content=ft.Text(libelle, color=couleur))),
                ft.DataCell(ft.ElevatedButton("Voir", width=80, bgcolor="#4f46e5", color=ft.Colors.WHITE,
                                              on_click=lambda e, ex=ex: voir_details(ex))),
            ]))
        page.update()

    def changer_statut(exhumation_id, nouveau_statut):
        statut, resultat = api_update_exhumation(exhumation_id, nouveau_statut)
        if statut == 200:
            page.pop_dialog()
            notifier("✅ Statut mis à jour")
            charger_exhumations()
        else:
            notifier(f"❌ {resultat.get('error', 'Erreur')}", succes=False)

    def voir_details(ex):
        actions = [ft.TextButton("Fermer", on_click=lambda e: page.pop_dialog())]
        if ex["statut"] == "EN_ATTENTE":
            actions = [
                ft.TextButton("Fermer", on_click=lambda e: page.pop_dialog()),
                ft.ElevatedButton("❌ Refuser", bgcolor=ft.Colors.RED_400, color=ft.Colors.WHITE,
                                  on_click=lambda e: changer_statut(ex["id"], "REFUSEE")),
                ft.ElevatedButton("✅ Approuver", bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE,
                                  on_click=lambda e: changer_statut(ex["id"], "APPROUVEE")),
            ]
        dialog = ft.AlertDialog(
            title=ft.Text(f"⚰️ Demande E-{ex['id']:03d}"),
            content=ft.Column([
                ft.Text(f"Défunt : {ex['nom_defunt']}"),
                ft.Text(f"Demandeur : {ex['demandeur_nom']}"),
                ft.Text(f"Téléphone : {ex.get('demandeur_telephone') or '—'}"),
                ft.Text(f"Motif : {ex.get('motif') or '—'}"),
                ft.Text(f"Date de la demande : {ex['date_demande']}"),
            ], tight=True, spacing=8),
            actions=actions,
        )
        page.show_dialog(dialog)

    def ouvrir_dialog_nouvelle(e):
        nom_defunt = ft.TextField(label="Nom du défunt", width=320)
        demandeur_nom = ft.TextField(label="Nom du demandeur", width=320)
        demandeur_tel = ft.TextField(label="Téléphone du demandeur", width=320)
        motif = ft.TextField(label="Motif", width=320, multiline=True)

        def creer(e):
            if not nom_defunt.value or not demandeur_nom.value:
                notifier("❌ Nom du défunt et du demandeur obligatoires", succes=False)
                return
            statut, resultat = api_creer_exhumation(
                defunt_nom=nom_defunt.value,
                demandeur_nom=demandeur_nom.value,
                demandeur_telephone=demandeur_tel.value,
                raison=motif.value,
            )
            if statut == 200:
                page.pop_dialog()
                notifier("✅ Demande d'exhumation créée")
                charger_exhumations()
            else:
                notifier(f"❌ {resultat.get('error', 'Erreur')}", succes=False)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("➕ Nouvelle demande d'exhumation"),
            content=ft.Column([nom_defunt, demandeur_nom, demandeur_tel, motif], tight=True, spacing=10),
            actions=[
                ft.TextButton("Annuler", on_click=lambda e: page.pop_dialog()),
                ft.ElevatedButton("Créer", on_click=creer, bgcolor="#4f46e5", color=ft.Colors.WHITE),
            ],
        )
        page.show_dialog(dialog)

    def exporter(e):
        notifier("📥 Export CSV : fonctionnalité à venir", succes=True)

    content = ft.Column([
        ft.Row([ft.Column([
            ft.Text("⚰️ Gestion des Exhumations", size=24, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ft.Text("Suivi des procédures d'exhumation", size=14, color=ft.Colors.BLUE_GREY_600),
        ])]),
        ft.Divider(height=15),
        ft.Row([
            ft.ElevatedButton("➕ Nouvelle demande d'exhumation", on_click=ouvrir_dialog_nouvelle, bgcolor="#4f46e5", color=ft.Colors.WHITE),
            ft.ElevatedButton("📥 Exporter les données", on_click=exporter, bgcolor=ft.Colors.GREY_600, color=ft.Colors.WHITE),
        ], spacing=10),
        ft.Divider(height=15),
        ft.Container(
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=15,
            content=ft.Column([
                ft.Text("📋 Demandes en cours", size=16, weight=ft.FontWeight.BOLD, color="#0f172a"),
                table,
            ]),
        ),
    ], spacing=5)

    build_layout(page, "exhumations", naviguer, content)
    charger_exhumations()
