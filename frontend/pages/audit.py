# pages/audit.py
import flet as ft
from pages.layout import build_layout
from utils.api import api_get_audit


def create_audit_view(page, naviguer):
    """Page d'audit"""

    statut, logs = api_get_audit()
    if statut != 200 or not isinstance(logs, list):
        logs = []

    rows = [
        ft.DataRow(cells=[
            ft.DataCell(ft.Text(log["date"])),
            ft.DataCell(ft.Text(log["utilisateur"])),
            ft.DataCell(ft.Text(log["action"])),
            ft.DataCell(ft.Text(log["details"])),
        ])
        for log in logs
    ] or [
        ft.DataRow(cells=[
            ft.DataCell(ft.Text("—")), ft.DataCell(ft.Text("—")),
            ft.DataCell(ft.Text("Aucune action enregistrée")), ft.DataCell(ft.Text("—")),
        ])
    ]

    content = ft.Column([
        ft.Row([ft.Column([
            ft.Text("📜 Audit Trail", size=24, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ft.Text("Historique des actions", size=14, color=ft.Colors.BLUE_GREY_600),
        ])]),
        ft.Divider(height=15),
        ft.Container(
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=20,
            content=ft.Column([
                ft.Text("📋 Dernières actions", size=18, weight=ft.FontWeight.BOLD, color="#0f172a"),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Date")),
                        ft.DataColumn(ft.Text("Utilisateur")),
                        ft.DataColumn(ft.Text("Action")),
                        ft.DataColumn(ft.Text("Détails")),
                    ],
                    rows=rows,
                ),
            ]),
        ),
    ], spacing=5)

    build_layout(page, "audit", naviguer, content)
