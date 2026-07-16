# utils/api.py
import requests

API_URL = "https://monprojectemietiere-production.up.railway.app/api"


def _get(path, params=None, timeout=10):
    try:
        response = requests.get(f"{API_URL}{path}", params=params, timeout=timeout)
        try:
            data = response.json()
        except Exception:
            data = {}
        return response.status_code, data
    except Exception as e:
        return 500, {"error": str(e)}


def _post(path, payload=None, timeout=10):
    try:
        response = requests.post(f"{API_URL}{path}", json=payload or {}, timeout=timeout)
        try:
            data = response.json()
        except Exception:
            data = {}
        return response.status_code, data
    except Exception as e:
        return 500, {"error": str(e)}


def _put(path, payload=None, timeout=10):
    try:
        response = requests.put(f"{API_URL}{path}", json=payload or {}, timeout=timeout)
        try:
            data = response.json()
        except Exception:
            data = {}
        return response.status_code, data
    except Exception as e:
        return 500, {"error": str(e)}


# ==================== AUTH ====================

def api_register(email, password, nom="User", prenom="Test"):
    return _post("/auth/register", {
        "nom": nom, "prenom": prenom, "email": email,
        "mot_de_passe": password, "role": "CLIENT"
    })

def api_login(email, password):
    return _post("/auth/login", {"email": email, "mot_de_passe": password})

def api_verify_mfa(email, code):
    return _post("/auth/mfa/verify", {"email": email, "code": code})

def api_change_password(email, ancien_mot_de_passe, nouveau_mot_de_passe):
    return _post("/auth/change-password", {
        "email": email,
        "ancien_mot_de_passe": ancien_mot_de_passe,
        "nouveau_mot_de_passe": nouveau_mot_de_passe,
    })


# ==================== STATISTIQUES ====================

def api_get_stats():
    status, data = _get("/statistiques", timeout=5)
    return status, data if status == 200 else {}


# ==================== PROFIL ====================

def api_get_profil(email):
    return _get(f"/profil/{email}")

def api_update_profil(email, nom, prenom, telephone):
    return _put(f"/profil/{email}", {"nom": nom, "prenom": prenom, "telephone": telephone})


# ==================== UTILISATEURS (ADMIN) ====================

def api_get_users():
    return _get("/users")

def api_update_user(user_id, nom=None, prenom=None, telephone=None, role=None):
    payload = {}
    if nom is not None: payload["nom"] = nom
    if prenom is not None: payload["prenom"] = prenom
    if telephone is not None: payload["telephone"] = telephone
    if role is not None: payload["role"] = role
    return _put(f"/users/{user_id}", payload)


# ==================== CAVEAUX ====================

def api_get_caveaux():
    return _get("/caveaux")


# ==================== RÉSERVATIONS ====================

def api_creer_reservation(caveau_id, client_nom, client_prenom, client_email, client_telephone,
                           nom_defunt, prenom_defunt, date_naissance, date_deces):
    return _post("/reservations", {
        "caveau_id": caveau_id,
        "client_nom": client_nom,
        "client_prenom": client_prenom,
        "client_email": client_email,
        "client_telephone": client_telephone,
        "nom_defunt": nom_defunt,
        "prenom_defunt": prenom_defunt,
        "date_naissance": date_naissance,
        "date_deces": date_deces,
    })


# ==================== CONCESSIONS ====================

def api_get_concessions():
    return _get("/concessions")

def api_creer_concession(caveau_id, proprietaire_nom, proprietaire_telephone, proprietaire_email,
                          type_concession, date_debut, date_fin=None):
    return _post("/concessions", {
        "caveau_id": caveau_id,
        "proprietaire_nom": proprietaire_nom,
        "proprietaire_telephone": proprietaire_telephone,
        "proprietaire_email": proprietaire_email,
        "type_concession": type_concession,
        "date_debut": date_debut,
        "date_fin": date_fin,
    })


# ==================== EXHUMATIONS ====================

def api_get_exhumations():
    return _get("/exhumations")

def api_creer_exhumation(defunt_nom, demandeur_nom, demandeur_telephone, raison, defunt_prenom="", concession_id=None):
    return _post("/exhumations", {
        "concession_id": concession_id,
        "defunt_nom": defunt_nom,
        "defunt_prenom": defunt_prenom,
        "demandeur_nom": demandeur_nom,
        "demandeur_telephone": demandeur_telephone,
        "raison": raison,
    })

def api_update_exhumation(exhumation_id, statut):
    return _put(f"/exhumations/{exhumation_id}", {"statut": statut})


# ==================== TRANSACTIONS / PAIEMENTS ====================

def api_get_transactions():
    return _get("/transactions")

def api_creer_transaction(montant, type_paiement, numero_telephone):
    return _post("/transactions", {
        "montant": montant,
        "type_paiement": type_paiement,
        "numero_telephone": numero_telephone,
    })


# ==================== AUDIT ====================

def api_get_audit():
    return _get("/audit")


# ==================== TERRAIN ====================

def api_get_terrain():
    return _get("/terrain")

def api_update_terrain(superficie_totale, zones, longueur_tombeau, largeur_tombeau,
                        zones_non_exploitables, chemins_m2):
    return _put("/terrain", {
        "superficie_totale": superficie_totale,
        "zones": zones,
        "longueur_tombeau": longueur_tombeau,
        "largeur_tombeau": largeur_tombeau,
        "zones_non_exploitables": zones_non_exploitables,
        "chemins_m2": chemins_m2,
    })


# ==================== RAPPORTS ====================

def api_get_rapports():
    return _get("/rapports")
