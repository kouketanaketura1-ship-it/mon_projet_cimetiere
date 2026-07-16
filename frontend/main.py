# main.py
# EMPLACEMENT : frontend/main.py
# CORRECTION :
#   - APP_STATE passé en paramètre à chaque vue (plus de "from main import APP_STATE")
#   - ft.app() → ft.run() (Flet >= 0.80)
#   - view=WEB_BROWSER + port=8550
import flet as ft
from pages.login import build_login_page
from pages.dashboard import create_dashboard_view
from pages.cartographie import create_cartographie_view
from pages.reservations import create_reservations_view
from pages.paiement import create_paiement_view
from pages.profil import create_profil_view
from pages.exhumations import create_exhumations_view
from pages.admin import create_admin_view
from pages.audit import create_audit_view
from pages.concessions import create_concessions_view
from pages.rapports import create_rapports_view
from pages.terrain import create_terrain_view
from pages.mfa_verify import build_mfa_page

# ===== ÉTAT GLOBAL =====
APP_STATE = {
    "page": "dashboard",
    "email": None,
    "logged_in": False,
}

def main(page: ft.Page):
    page.title = "Gestion de Cimetière"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#f5f7fb"
    page.scroll = ft.ScrollMode.AUTO
    def go_to_login(page):
        build_login_page(page, go_to_register, go_to_mfa, go_to_dashboard)

    def go_to_register(page):
        from pages.register import build_register_page
        build_register_page(page, go_to_login, go_to_mfa)

    def go_to_mfa(page, email):
        APP_STATE["email"] = email
        build_mfa_page(page, email, go_to_dashboard, go_to_login)

    def go_to_dashboard(page, email, role=None):
        APP_STATE["logged_in"] = True
        APP_STATE["email"] = email
        if role:
            APP_STATE["role"] = role
        naviguer("dashboard")

    def naviguer(destination):
        APP_STATE["page"] = destination
        page.controls.clear()
        email = APP_STATE.get("email") or ""

        if destination == "dashboard":
            create_dashboard_view(page, naviguer, APP_STATE.get('role'))
        elif destination == "cartographie":
            create_cartographie_view(page, naviguer)
        elif destination == "reservations":
            create_reservations_view(page, naviguer)
        elif destination == "paiement":
            create_paiement_view(page, naviguer)
        elif destination == "profil":
            create_profil_view(page, naviguer, email)   # email passé en paramètre
        elif destination == "exhumations":
            create_exhumations_view(page, naviguer)
        elif destination == "admin":
            create_admin_view(page, naviguer)
        elif destination == "audit":
            create_audit_view(page, naviguer)
        elif destination == "concessions":
            create_concessions_view(page, naviguer)
        elif destination == "rapports":
            create_rapports_view(page, naviguer)
        elif destination == "terrain":
            create_terrain_view(page, naviguer)

        page.update()

    if APP_STATE["logged_in"]:
        naviguer("dashboard")
    else:
        go_to_login(page)

if __name__ == "__main__":
    import os
    # Si Railway fournit un port, on l'utilise. Sinon, on prend 8560 localement.
    port = int(os.getenv("PORT", 8560))
    ft.app(target=main, port=port, host="0.0.0.0",assets_dir="frontend/utils")