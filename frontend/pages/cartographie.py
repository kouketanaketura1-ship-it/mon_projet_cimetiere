# pages/cartographie.py
# EMPLACEMENT : frontend/pages/cartographie.py
# CORRECTION : api_get_caveaux et api_get_transactions dans un thread
import flet as ft
import threading
from pages.layout import build_layout
from utils.api import api_get_caveaux, api_get_transactions

COULEURS_STATUT = {
    "DISPONIBLE":      ft.Colors.GREEN_400,
    "RESERVE":         ft.Colors.ORANGE_400,
    "OCCUPE":          ft.Colors.RED_400,
    "NON_EXPLOITABLE": ft.Colors.GREY_400,
}
LIBELLES_STATUT = {
    "DISPONIBLE":      "Disponible",
    "RESERVE":         "Réservé",
    "OCCUPE":          "Occupé",
    "NON_EXPLOITABLE": "Non exploitable",
}


def create_cartographie_view(page, naviguer):
    """Page Cartographie SIG"""

    # Widgets dynamiques (mis à jour après chargement)
    liste_zones_widgets = ft.Column(
        [ft.Text("⏳ Chargement des caveaux...", color=ft.Colors.BLUE_GREY_400)],
        scroll=ft.ScrollMode.AUTO,
    )
    resultats_recherche = ft.Column([])

    txt_total   = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color="#0f172a")
    txt_occupes = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color="#0f172a")
    txt_dispo   = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color="#0f172a")
    txt_reserves = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color="#0f172a")
    txt_non_exp = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color="#0f172a")
    txt_mtn     = ft.Text("0 XAF", color=ft.Colors.GREEN_400, size=18, weight=ft.FontWeight.BOLD)
    txt_airtel  = ft.Text("0 XAF", color=ft.Colors.ORANGE_400, size=18, weight=ft.FontWeight.BOLD)

    caveaux_data = []   # partagé pour la recherche

    def carte_zone(nom_zone, liste_caveaux, couleur_fond):
        return ft.Container(
            bgcolor=couleur_fond,
            border_radius=8,
            padding=10,
            content=ft.Column([
                ft.Row([
                    ft.Text(f"🏛️ Zone {nom_zone}", size=16,
                            weight=ft.FontWeight.BOLD, color="#0f172a"),
                    ft.Text(f"{len(liste_caveaux)} caveaux", size=12,
                            color=ft.Colors.BLUE_GREY_600),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Column([
                    ft.Row([
                        ft.Container(width=10, height=10,
                                     bgcolor=COULEURS_STATUT.get(c["statut"], ft.Colors.GREY_400),
                                     border_radius=2),
                        ft.Text(f"{c['numero']} - {LIBELLES_STATUT.get(c['statut'], c['statut'])}",
                                size=13),
                        ft.Text(f"👤 {c['proprietaire_nom']}"
                                if c.get('proprietaire_nom') else "", size=11,
                                color=ft.Colors.BLUE_GREY_600),
                    ], spacing=5)
                    for c in liste_caveaux
                ]),
            ]),
        )

    def charger_donnees():
        nonlocal caveaux_data
        statut_api, caveaux = api_get_caveaux()
        if statut_api != 200 or not isinstance(caveaux, list):
            caveaux = []
        caveaux_data = caveaux

        statut_tx, transactions = api_get_transactions()
        if statut_tx != 200 or not isinstance(transactions, list):
            transactions = []

        zones = {}
        for c in caveaux:
            zones.setdefault(c.get("section", "?"), []).append(c)

        couleurs_fond_cycle = [
            ft.Colors.BLUE_50, ft.Colors.GREEN_50,
            ft.Colors.ORANGE_50, ft.Colors.PURPLE_50,
        ]
        liste_zones_widgets.controls.clear()
        if not zones:
            liste_zones_widgets.controls.append(
                ft.Text(
                    "Aucun caveau trouvé — vérifiez que Django tourne\n"
                    "et que la base contient des données.",
                    size=13, color=ft.Colors.RED_400,
                )
            )
        else:
            for i, (nom_zone, liste) in enumerate(sorted(zones.items())):
                liste_zones_widgets.controls.append(
                    carte_zone(nom_zone, liste,
                               couleurs_fond_cycle[i % len(couleurs_fond_cycle)])
                )
                liste_zones_widgets.controls.append(ft.Divider(height=5))

        # Stats
        txt_total.value    = str(len(caveaux))
        txt_occupes.value  = str(sum(1 for c in caveaux if c.get("statut") == "OCCUPE"))
        txt_dispo.value    = str(sum(1 for c in caveaux if c.get("statut") == "DISPONIBLE"))
        txt_reserves.value = str(sum(1 for c in caveaux if c.get("statut") == "RESERVE"))
        txt_non_exp.value  = str(sum(1 for c in caveaux if c.get("statut") == "NON_EXPLOITABLE"))

        total_mtn    = sum(t.get("montant", 0) for t in transactions
                          if t.get("type_paiement") == "MOBILE_MONEY")
        total_airtel = sum(t.get("montant", 0) for t in transactions
                          if t.get("type_paiement") == "AIRTEL_MONEY")
        txt_mtn.value    = f"{total_mtn:,.0f} XAF"
        txt_airtel.value = f"{total_airtel:,.0f} XAF"
        page.update()

    threading.Thread(target=charger_donnees, daemon=True).start()

    def rechercher(e):
        terme = (champ_recherche.value or "").strip().lower()
        resultats_recherche.controls.clear()
        if not terme:
            page.update()
            return
        trouves = [
            c for c in caveaux_data
            if terme in c.get("numero", "").lower()
            or terme in (c.get("proprietaire_nom") or "").lower()
        ]
        if not trouves:
            resultats_recherche.controls.append(
                ft.Text("Aucun résultat", color=ft.Colors.RED_400))
        else:
            for c in trouves:
                resultats_recherche.controls.append(
                    ft.Text(
                        f"🔎 {c['numero']} - {LIBELLES_STATUT.get(c['statut'], c['statut'])}"
                        + (f" - 👤 {c['proprietaire_nom']}" if c.get('proprietaire_nom') else ""),
                        size=13,
                    )
                )
        page.update()

    champ_recherche = ft.TextField(
        label="Rechercher défunt ou caveau",
        width=400,
        border_color=ft.Colors.GREY_300,
        border_radius=8,
        on_submit=rechercher,
    )

    contenu = ft.Column([
        ft.Row([ft.Column([
            ft.Text("🗺️ Cartographie Interactive - Cimetière de la Paix",
                    size=24, weight=ft.FontWeight.BOLD, color="#0f172a"),
            ft.Text("Géolocalisation et gestion des caveaux",
                    size=14, color=ft.Colors.BLUE_GREY_600),
        ])]),
        ft.Divider(height=15),
        ft.Container(
            bgcolor=ft.Colors.WHITE, border_radius=12, padding=15,
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SEARCH, color=ft.Colors.GREY_600),
                    champ_recherche,
                    ft.ElevatedButton("🔍 Rechercher", on_click=rechercher,
                                      bgcolor="#4f46e5", color=ft.Colors.WHITE),
                ], spacing=10),
                resultats_recherche,
            ]),
        ),
        ft.Divider(height=15),
        ft.Row([
            # ── Zones ──
            ft.Container(
                width=380,
                bgcolor=ft.Colors.WHITE, border_radius=12, padding=15,
                content=ft.Column([
                    ft.Text("📍 Zones", size=18, weight=ft.FontWeight.BOLD, color="#0f172a"),
                    ft.Divider(height=10),
                    ft.Container(content=liste_zones_widgets, height=400,
                                 clip_behavior=ft.ClipBehavior.HARD_EDGE),
                    ft.Divider(height=10),
                    ft.Text("📊 Légende", size=16, weight=ft.FontWeight.BOLD, color="#0f172a"),
                    ft.Row([
                        ft.Row([ft.Container(width=15, height=15, bgcolor=ft.Colors.GREEN_400,  border_radius=3), ft.Text("Disponible",       size=12)], spacing=4),
                        ft.Row([ft.Container(width=15, height=15, bgcolor=ft.Colors.ORANGE_400, border_radius=3), ft.Text("Réservé",           size=12)], spacing=4),
                        ft.Row([ft.Container(width=15, height=15, bgcolor=ft.Colors.RED_400,    border_radius=3), ft.Text("Occupé",            size=12)], spacing=4),
                        ft.Row([ft.Container(width=15, height=15, bgcolor=ft.Colors.GREY_400,   border_radius=3), ft.Text("Non exploitable",   size=12)], spacing=4),
                    ], spacing=8, wrap=True),
                ]),
            ),
            # ── Stats + Revenus ──
            ft.Container(
                expand=True,
                content=ft.Column([
                    ft.Container(
                        bgcolor=ft.Colors.WHITE, border_radius=12, padding=15,
                        content=ft.Column([
                            ft.Text("📍 Résumé du Terrain", size=18,
                                    weight=ft.FontWeight.BOLD, color="#0f172a"),
                            ft.Divider(height=10),
                            ft.Row([
                                ft.Container(border_radius=8, padding=8, expand=True,
                                    content=ft.Column([ft.Text("🏛️ Total",          color=ft.Colors.BLUE_400,   size=12), txt_total],   horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)),
                                ft.Container(border_radius=8, padding=8, expand=True,
                                    content=ft.Column([ft.Text("🔴 Occupés",        color=ft.Colors.RED_400,    size=12), txt_occupes], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)),
                                ft.Container(border_radius=8, padding=8, expand=True,
                                    content=ft.Column([ft.Text("🟢 Disponibles",    color=ft.Colors.GREEN_400,  size=12), txt_dispo],   horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)),
                                ft.Container(border_radius=8, padding=8, expand=True,
                                    content=ft.Column([ft.Text("🟠 Réservés",       color=ft.Colors.ORANGE_400, size=12), txt_reserves],horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)),
                                ft.Container(border_radius=8, padding=8, expand=True,
                                    content=ft.Column([ft.Text("⚪ Non exploit.",   color=ft.Colors.GREY_600,   size=12), txt_non_exp], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)),
                            ], spacing=5, wrap=True),
                        ]),
                    ),
                    ft.Divider(height=10),
                    ft.Container(
                        bgcolor=ft.Colors.WHITE, border_radius=12, padding=15,
                        content=ft.Column([
                            ft.Text("💰 Revenus", size=18,
                                    weight=ft.FontWeight.BOLD, color="#0f172a"),
                            ft.Divider(height=10),
                            ft.Row([
                                ft.Text("📱 Mobile Money (MTN)",
                                        color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD),
                                txt_mtn,
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([
                                ft.Text("📱 Airtel Money",
                                        color=ft.Colors.ORANGE_400, weight=ft.FontWeight.BOLD),
                                txt_airtel,
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ]),
                    ),
                ], spacing=0),
            ),
        ], spacing=15),
    ], spacing=5)

    build_layout(page, "cartographie", naviguer, contenu)