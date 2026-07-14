# pages/paiement.py
# EMPLACEMENT : frontend/pages/paiement.py
# CORRECTIONS :
#   - page.show_dialog() supprimé → page.snack_bar (compatible mode web)
import flet as ft
from pages.layout import build_layout
from utils.api import api_get_transactions, api_creer_transaction


def create_paiement_view(page, naviguer):
    """Page de paiement"""

    def notifier(message, succes=True):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN_600 if succes else ft.Colors.RED_600,
        )
        page.snack_bar.open = True
        page.update()

    statut_tx, transactions = api_get_transactions()
    if statut_tx != 200 or not isinstance(transactions, list):
        transactions = []

    total_encaisse = sum(t["montant"] for t in transactions if t["statut"] == "VALIDE")
    total_mtn      = sum(t["montant"] for t in transactions if t["type_paiement"] == "MOBILE_MONEY")
    total_airtel   = sum(t["montant"] for t in transactions if t["type_paiement"] == "AIRTEL_MONEY")
    nb_transactions = len(transactions)

    total_encaisse_text = ft.Text(f"{total_encaisse:,.0f} XAF", size=24, weight=ft.FontWeight.BOLD, color="#0f172a")
    nb_transactions_text = ft.Text(str(nb_transactions), size=24, weight=ft.FontWeight.BOLD, color="#0f172a")
    mtn_total_text   = ft.Text(f"{total_mtn:,.0f} XAF", color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD)
    airtel_total_text = ft.Text(f"{total_airtel:,.0f} XAF", color=ft.Colors.ORANGE_400, weight=ft.FontWeight.BOLD)

    numero_mtn    = ft.TextField(label="Numéro MTN",   width=250, hint_text="06XXXXXXXX")
    montant_mtn   = ft.TextField(label="Montant",       width=250, hint_text="0 XAF")
    numero_airtel = ft.TextField(label="Numéro Airtel", width=250, hint_text="07XXXXXXXX")
    montant_airtel = ft.TextField(label="Montant",      width=250, hint_text="0 XAF")

    def rafraichir_totaux():
        nonlocal transactions, total_encaisse, total_mtn, total_airtel, nb_transactions
        _, transactions = api_get_transactions()
        if not isinstance(transactions, list):
            transactions = []
        total_encaisse  = sum(t["montant"] for t in transactions if t["statut"] == "VALIDE")
        total_mtn       = sum(t["montant"] for t in transactions if t["type_paiement"] == "MOBILE_MONEY")
        total_airtel    = sum(t["montant"] for t in transactions if t["type_paiement"] == "AIRTEL_MONEY")
        nb_transactions = len(transactions)
        total_encaisse_text.value  = f"{total_encaisse:,.0f} XAF"
        nb_transactions_text.value = str(nb_transactions)
        mtn_total_text.value       = f"{total_mtn:,.0f} XAF"
        airtel_total_text.value    = f"{total_airtel:,.0f} XAF"
        page.update()

    def payer(type_paiement, numero_field, montant_field):
        if not numero_field.value or not montant_field.value:
            notifier("❌ Numéro et montant obligatoires", succes=False)
            return
        try:
            montant = float(montant_field.value)
        except ValueError:
            notifier("❌ Montant invalide", succes=False)
            return
        statut, resultat = api_creer_transaction(montant, type_paiement, numero_field.value)
        if statut == 200:
            notifier(f"✅ Paiement enregistré (réf. {resultat.get('reference')})")
            numero_field.value  = ""
            montant_field.value = ""
            rafraichir_totaux()
        else:
            notifier(f"❌ {resultat.get('error', 'Erreur lors du paiement')}", succes=False)

    content = ft.Column([
        ft.Row([ft.Column([
            ft.Text("💰 Facturation & Paiements", size=24, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ft.Text("Gestion des paiements et factures", size=14, color=ft.Colors.BLUE_GREY_600),
        ])]),
        ft.Divider(height=15),
        ft.Row([
            ft.Container(bgcolor=ft.Colors.WHITE, border_radius=12, padding=15, expand=True,
                content=ft.Column([
                    ft.Text("💰 Total encaissé", color=ft.Colors.BLUE_GREY_600, size=14),
                    total_encaisse_text,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)),
            ft.Container(bgcolor=ft.Colors.WHITE, border_radius=12, padding=15, expand=True,
                content=ft.Column([
                    ft.Text("📊 Transactions", color=ft.Colors.BLUE_GREY_600, size=14),
                    nb_transactions_text,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)),
        ], spacing=10),
        ft.Divider(height=15),
        ft.Text("💳 Moyens de paiement", size=18, weight=ft.FontWeight.BOLD, color="#0f172a"),
        ft.Row([
            ft.Container(bgcolor=ft.Colors.WHITE, border_radius=12, padding=15, expand=True,
                content=ft.Column([
                    ft.Text("📱 Mobile Money (MTN)", size=16, weight=ft.FontWeight.BOLD, color="#0f172a"),
                    ft.Row([ft.Text("Total :", color=ft.Colors.BLUE_GREY_600), mtn_total_text]),
                    numero_mtn,
                    montant_mtn,
                    ft.ElevatedButton("💳 Payer par MTN", bgcolor="#4f46e5", color=ft.Colors.WHITE, width=250,
                                      on_click=lambda e: payer("MOBILE_MONEY", numero_mtn, montant_mtn)),
                ])),
            ft.Container(bgcolor=ft.Colors.WHITE, border_radius=12, padding=15, expand=True,
                content=ft.Column([
                    ft.Text("📱 Airtel Money", size=16, weight=ft.FontWeight.BOLD, color="#0f172a"),
                    ft.Row([ft.Text("Total :", color=ft.Colors.BLUE_GREY_600), airtel_total_text]),
                    numero_airtel,
                    montant_airtel,
                    ft.ElevatedButton("💳 Payer par Airtel", bgcolor="#4f46e5", color=ft.Colors.WHITE, width=250,
                                      on_click=lambda e: payer("AIRTEL_MONEY", numero_airtel, montant_airtel)),
                ])),
        ], spacing=10),
    ], spacing=5)

    build_layout(page, "paiement", naviguer, content)