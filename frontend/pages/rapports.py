# pages/rapports.py
import flet as ft
from pages.layout import build_layout
from utils.api import api_get_rapports, api_get_caveaux, api_get_transactions


def create_rapports_view(page, naviguer):
    """Page des rapports"""

    statut_r, rapport = api_get_rapports()
    if statut_r != 200 or not isinstance(rapport, dict):
        rapport = {"taux_occupation": 0, "reservations_total": 0, "revenus_total": 0}

    def afficher_rapport(titre, lignes):
        dialog = ft.AlertDialog(
            title=ft.Text(titre),
            content=ft.Column([ft.Text(l) for l in lignes], tight=True, spacing=8),
            actions=[ft.TextButton("Fermer", on_click=lambda e: page.pop_dialog())],
        )
        page.show_dialog(dialog)

    def rapport_occupation(e):
        statut, caveaux = api_get_caveaux()
        caveaux = caveaux if statut == 200 and isinstance(caveaux, list) else []
        total = len(caveaux)
        occupes = sum(1 for c in caveaux if c["statut"] == "OCCUPE")
        dispo = sum(1 for c in caveaux if c["statut"] == "DISPONIBLE")
        reserves = sum(1 for c in caveaux if c["statut"] == "RESERVE")
        afficher_rapport("📊 Rapport d'occupation", [
            f"Total de caveaux : {total}",
            f"Occupés : {occupes}",
            f"Disponibles : {dispo}",
            f"Réservés : {reserves}",
            f"Taux d'occupation : {rapport['taux_occupation']}%",
        ])

    def rapport_financier(e):
        statut, transactions = api_get_transactions()
        transactions = transactions if statut == 200 and isinstance(transactions, list) else []
        mtn = sum(t["montant"] for t in transactions if t["type_paiement"] == "MOBILE_MONEY")
        airtel = sum(t["montant"] for t in transactions if t["type_paiement"] == "AIRTEL_MONEY")
        afficher_rapport("💰 Rapport financier", [
            f"Revenus totaux : {rapport['revenus_total']:,.0f} XAF",
            f"Mobile Money (MTN) : {mtn:,.0f} XAF",
            f"Airtel Money : {airtel:,.0f} XAF",
            f"Nombre de transactions : {len(transactions)}",
        ])

    def rapport_reservations(e):
        afficher_rapport("📋 Rapport des réservations", [
            f"Nombre total de réservations : {rapport['reservations_total']}",
        ])

    def exporter_csv(e):
        afficher_rapport("📥 Export CSV", ["Fonctionnalité à venir."])

    content = ft.Column([
        ft.Row([ft.Column([
            ft.Text("📊 Rapports", size=24, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ft.Text("Génération et export de rapports", size=14, color=ft.Colors.BLUE_GREY_600),
        ])]),
        ft.Divider(height=15),
        ft.Row([
            ft.Container(
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                padding=20,
                expand=True,
                content=ft.Column([
                    ft.Text("📋 Rapports disponibles", size=18, weight=ft.FontWeight.BOLD, color="#0f172a"),
                    ft.Divider(height=10),
                    ft.ElevatedButton("📊 Rapport d'occupation", on_click=rapport_occupation, width=250, bgcolor="#4f46e5", color=ft.Colors.WHITE),
                    ft.ElevatedButton("💰 Rapport financier", on_click=rapport_financier, width=250, bgcolor="#4f46e5", color=ft.Colors.WHITE),
                    ft.ElevatedButton("📋 Rapport des réservations", on_click=rapport_reservations, width=250, bgcolor="#4f46e5", color=ft.Colors.WHITE),
                    ft.ElevatedButton("📥 Exporter en CSV", on_click=exporter_csv, width=250, bgcolor=ft.Colors.GREY_600, color=ft.Colors.WHITE),
                ]),
            ),
            ft.Container(
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                padding=20,
                expand=True,
                content=ft.Column([
                    ft.Text("📈 Analyses", size=18, weight=ft.FontWeight.BOLD, color="#0f172a"),
                    ft.Divider(height=10),
                    ft.Text(f"🔹 Taux d'occupation : {rapport['taux_occupation']}%"),
                    ft.ProgressBar(value=min(rapport['taux_occupation'] / 100, 1), color="#4f46e5"),
                    ft.Text(f"🔹 Réservations : {rapport['reservations_total']}"),
                    ft.Text(f"🔹 Revenus totaux : {rapport['revenus_total']:,.0f} XAF"),
                ]),
            ),
        ], spacing=20),
    ], spacing=5)

    build_layout(page, "rapports", naviguer, content)
