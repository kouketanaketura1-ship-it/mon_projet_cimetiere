from ninja import NinjaAPI
from ninja import Schema
from typing import Optional
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import json
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from cimetiere.models import (
    Caveau, Reservation, Utilisateur, MFACode,
    Concession, Exhumation, Transaction, AuditLog, ConfigurationTerrain,
)
from django.conf import settings
import ssl
import logging
import time
from pathlib import Path
import os

api = NinjaAPI()

# ==================== SCHÉMAS ====================

class UtilisateurIn(Schema):
    nom: str
    prenom: str
    email: str
    mot_de_passe: str
    role: str = 'CLIENT'
    telephone: Optional[str] = None

class LoginIn(Schema):
    email: str
    mot_de_passe: str

class MFAIn(Schema):
    email: str
    code: str


class TestEmailIn(Schema):
    email: str

# ==================== SCHÉMAS DE RÉPONSE ====================

class RegisterOut(Schema):
    success: bool
    message: str
    email: str
    mfa_required: bool

class LoginOut(Schema):
    success: bool
    message: str
    email: str
    mfa_required: bool

class MFAOut(Schema):
    success: bool
    message: str
    email: str
    role: str

class ErrorOut(Schema):
    error: str

# ==================== CONFIGURATION EMAIL ====================

def envoyer_email(destinataire, sujet, message):
    """Envoie un email via SMTP en utilisant les settings Django.

    - Utilise `settings.EMAIL_*` si présents
    - Définit l'expéditeur à `settings.DEFAULT_FROM_EMAIL`
    - Utilise un contexte TLS sécurisé
    """
    smtp_host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
    smtp_port = getattr(settings, 'EMAIL_PORT', 587)
    smtp_user = getattr(settings, 'EMAIL_HOST_USER', None)
    smtp_password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
    from_header = getattr(settings, 'DEFAULT_FROM_EMAIL', smtp_user or '')

    msg = MIMEMultipart()
    msg['From'] = from_header
    msg['To'] = destinataire
    msg['Subject'] = sujet
    msg.attach(MIMEText(message, 'plain'))

    # Setup logger to file in project root (avoid duplicating handlers)
    log_path = Path(__file__).resolve().parent.parent / 'email_send.log'
    logger = logging.getLogger('email_sender')
    if not logger.handlers:
        fh = logging.FileHandler(log_path, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.setLevel(logging.INFO)

    context = ssl.create_default_context()
    retries = getattr(settings, 'EMAIL_SEND_RETRIES', 3)
    timeout = getattr(settings, 'EMAIL_TIMEOUT', 20)
    backoff = getattr(settings, 'EMAIL_BACKOFF_SECONDS', 1)

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=timeout) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                # ensure recipient list
                server.sendmail(from_header, [destinataire], msg.as_string())

            info_msg = f"📧 Email envoyé à {destinataire} (attempt {attempt})"
            print(info_msg)
            logger.info(info_msg)
            return True
        except Exception as e:
            last_exc = e
            err_msg = f"Attempt {attempt} failed sending email to {destinataire}: {e}"
            print(f"❌ {err_msg}")
            logger.exception(err_msg)
            if attempt < retries:
                time.sleep(backoff * attempt)

    # Après toutes les tentatives
    logger.error(f"Échec envoi email après {retries} tentatives: {last_exc}")
    return False

# ==================== FONCTIONS MFA ====================

def journaliser(email, action, details=""):
    """Enregistre une action dans l'audit trail (email peut être None ou l'email d'un utilisateur existant)."""
    try:
        utilisateur = None
        if email:
            utilisateur = Utilisateur.objects.filter(email=email).first()
        AuditLog.objects.create(utilisateur=utilisateur, action=action, details=details)
    except Exception as e:
        print(f"⚠️ Impossible d'enregistrer l'audit log: {e}")


def generer_code_mfa():
    return ''.join(random.choices(string.digits, k=6))

def envoyer_code_mfa(email, code):
    """Envoie le code MFA par email"""
    sujet = "🔐 Code de vérification - Gestion de Cimetière"
    message = f"""Bonjour,

Voici votre code de vérification à double facteur :

🔑 CODE : {code}

Ce code est valable pendant 5 minutes.

Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.

---
Gestion de Cimetière - Application de Gestion Funéraire
"""
    return envoyer_email(email, sujet, message)

def sauvegarder_code_mfa(utilisateur, code):
    MFACode.objects.filter(utilisateur=utilisateur, est_utilise=False).delete()
    date_expiration = timezone.now() + timedelta(minutes=5)
    return MFACode.objects.create(
        utilisateur=utilisateur,
        code=code,
        date_expiration=date_expiration
    )

def verifier_code_mfa(utilisateur, code):
    mfa = MFACode.objects.filter(
        utilisateur=utilisateur,
        code=code,
        est_utilise=False
    ).order_by('-date_creation').first()
    
    if not mfa:
        return False, "Code invalide"
    if not mfa.est_valide():
        return False, "Code expiré (5 minutes)"
    
    mfa.est_utilise = True
    mfa.save()
    return True, "Code valide"

# ==================== ENDPOINTS AUTH ====================

@api.post("/auth/register", response={200: RegisterOut, 400: ErrorOut})
def register(request, payload: UtilisateurIn):
    try:
        # ✅ AJOUT : Nettoyer et valider l'email
        email = payload.email.strip().lower()
        
        # ✅ AJOUT : Vérifier si l'email est valide
        if "@" not in email:
            return 400, {"error": "Email invalide. Il doit contenir '@'."}
        
        # ✅ AJOUT : Si le domaine n'a pas de point, ajouter .com par défaut
        domaine = email.split("@")[1]
        if "." not in domaine:
            email = email + ".com"
            print(f"📧 Email corrigé : {payload.email} → {email}")
        
        # ✅ AJOUT : Vérifier si l'email existe déjà
        if Utilisateur.objects.filter(email=email).exists():
            return 400, {"error": "Cet email est déjà utilisé"}
        
        utilisateur = Utilisateur.objects.create(
            nom=payload.nom,
            prenom=payload.prenom,
            email=email,  # ✅ Utiliser l'email corrigé
            mot_de_passe=make_password(payload.mot_de_passe),
            role=payload.role,
            telephone=payload.telephone,
            mfa_active=True
        )
        
        code = generer_code_mfa()
        sauvegarder_code_mfa(utilisateur, code)
        sent = envoyer_code_mfa(email, code)  # ✅ Utiliser l'email corrigé
        if not sent:
            return 400, {"error": "Impossible d'envoyer le code MFA — vérifiez la configuration d'email (FROM doit être validé)."}

        return 200, {
            "success": True,
            "message": "Compte créé. Code MFA envoyé par email.",
            "email": email,
            "mfa_required": True
        }
        
    except Exception as e:
        return 400, {"error": str(e)}

@api.post("/auth/login", response={200: LoginOut, 400: ErrorOut, 401: ErrorOut, 404: ErrorOut})
def login(request, payload: LoginIn):
    try:
        utilisateur = Utilisateur.objects.get(email=payload.email)
        
        if not check_password(payload.mot_de_passe, utilisateur.mot_de_passe):
            return 401, {"error": "Mot de passe incorrect"}
        
        code = generer_code_mfa()
        sauvegarder_code_mfa(utilisateur, code)
        sent = envoyer_code_mfa(payload.email, code)
        if not sent:
            return 400, {"error": "Impossible d'envoyer le code MFA — vérifiez la configuration d'email (FROM doit être validé)."}

        return 200, {
            "success": True,
            "message": "Code MFA envoyé par email",
            "email": utilisateur.email,
            "mfa_required": True
        }
        
    except Utilisateur.DoesNotExist:
        return 404, {"error": "Utilisateur non trouvé"}
    except Exception as e:
        return 400, {"error": str(e)}

@api.post("/auth/mfa/verify", response={200: MFAOut, 400: ErrorOut})
def verify_mfa(request, payload: MFAIn):
    try:
        utilisateur = get_object_or_404(Utilisateur, email=payload.email)
        
        valide, message = verifier_code_mfa(utilisateur, payload.code)
        
        if not valide:
            return 400, {"error": message}
        
        utilisateur.mfa_active = True
        utilisateur.save()

        journaliser(utilisateur.email, "Connexion (MFA vérifié)", utilisateur.role)

        return 200, {
            "success": True,
            "message": "Connexion validée",
            "email": utilisateur.email,
            "role": utilisateur.role
        }
        
    except Exception as e:
        return 400, {"error": str(e)}

@api.post("/auth/mfa/resend")
def resend_mfa(request, payload: MFAIn):
    try:
        utilisateur = get_object_or_404(Utilisateur, email=payload.email)
        
        code = generer_code_mfa()
        sauvegarder_code_mfa(utilisateur, code)
        sent = envoyer_code_mfa(payload.email, code)
        if not sent:
            return {"error": "Impossible d'envoyer le code MFA — vérifiez la configuration d'email (FROM doit être validé)."}, 400

        return {
            "success": True,
            "message": "Nouveau code MFA envoyé par email"
        }
        
    except Exception as e:
        return {"error": str(e)}, 400

# ==================== ENDPOINTS CAVEAUX ====================

@api.get("/caveaux")
def liste_caveaux(request):
    caveaux = Caveau.objects.all()
    resultat = []
    for c in caveaux:
        resultat.append({
            "id": c.id,
            "numero": c.numero,
            "section": c.section,
            "statut": c.statut,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "proprietaire_nom": c.proprietaire_nom,
            "nom_defunt": c.nom_defunt,
        })
    return resultat


@api.get("/hello")
def hello(request):
    return {"message": "API OK"}


@api.post("/auth/test-email")
def test_email_endpoint(request, payload: TestEmailIn):
    """Endpoint de test : envoie un email de test et renvoie les dernières lignes du log.

    Utiliser en dev pour diagnostiquer les erreurs d'envoi SMTP.
    """
    # envoyer un message simple
    sujet = "[TEST] Envoi email - Gestion de Cimetière"
    message = f"Test d'envoi vers {payload.email} depuis l'API. Si tu reçois cet email, c'est OK."
    sent = envoyer_email(payload.email, sujet, message)

    # lire les dernières lignes du fichier de log
    from pathlib import Path
    log_path = Path(__file__).resolve().parent.parent / 'email_send.log'
    log_tail = ""
    try:
        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                tail = lines[-200:] if len(lines) > 200 else lines
                log_tail = ''.join(tail)
    except Exception as e:
        log_tail = f"Erreur lecture log: {e}"

    return {
        "success": sent,
        "sent": sent,
        "log_tail": log_tail
    }

@api.get("/statistiques")
def statistiques(request):
    total = Caveau.objects.count()
    disponibles = Caveau.objects.filter(statut='DISPONIBLE').count()
    reserves = Caveau.objects.filter(statut='RESERVE').count()
    occupes = Caveau.objects.filter(statut='OCCUPE').count()
    # ✅ AJOUT : Taux d'occupation
    taux_occupation = round((occupes / total * 100), 1) if total > 0 else 0
    return {
        "total": total,
        "disponibles": disponibles,
        "reserves": reserves,
        "occupes": occupes,
        "taux_occupation": taux_occupation,
    }

@api.get("/reservations")
def liste_reservations(request):
    reservations = Reservation.objects.all().order_by('-date_reservation')
    resultat = []
    for r in reservations:
        resultat.append({
            "id": r.id,
            "caveau_id": r.caveau.id,
            "client_nom": r.client_nom,
            "client_prenom": r.client_prenom,
            "statut": r.statut,
            "date_reservation": r.date_reservation.strftime("%Y-%m-%d %H:%M"),
        })
    return resultat

@api.post("/reservations")
def creer_reservation(request):
    try:
        body = json.loads(request.body)
        caveau = get_object_or_404(Caveau, id=body.get("caveau_id"))
        
        reservation = Reservation.objects.create(
            caveau=caveau,
            client_nom=body.get("client_nom", "Inconnu"),
            client_prenom=body.get("client_prenom", "Inconnu"),
            client_email=body.get("client_email", "test@test.com"),
            client_telephone=body.get("client_telephone", "00000000"),
            nom_defunt=body.get("nom_defunt", "Inconnu"),
            prenom_defunt=body.get("prenom_defunt", "Inconnu"),
            date_naissance=datetime.strptime(body.get("date_naissance", "2000-01-01"), "%Y-%m-%d").date(),
            date_deces=datetime.strptime(body.get("date_deces", "2000-01-01"), "%Y-%m-%d").date(),
            statut='EN_ATTENTE'
        )
        
        caveau.statut = 'RESERVE'
        caveau.save()

        journaliser(body.get("client_email"), "Nouvelle réservation", f"Caveau {caveau.numero}")

        return {"success": True, "id": reservation.id}
    except Exception as e:
        return {"error": str(e)}, 400


# ==================== SCHÉMAS PROFIL / UTILISATEURS ====================

class ProfilUpdateIn(Schema):
    nom: str
    prenom: str
    telephone: Optional[str] = None

class ChangePasswordIn(Schema):
    email: str
    ancien_mot_de_passe: str
    nouveau_mot_de_passe: str

class UserUpdateIn(Schema):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    role: Optional[str] = None

class ConcessionIn(Schema):
    caveau_id: int
    proprietaire_nom: str
    proprietaire_telephone: Optional[str] = None
    proprietaire_email: Optional[str] = None
    type_concession: str = 'TEMPORAIRE'
    date_debut: str
    date_fin: Optional[str] = None

class ExhumationIn(Schema):
    concession_id: Optional[int] = None
    defunt_nom: str
    defunt_prenom: Optional[str] = ""
    demandeur_nom: str
    demandeur_telephone: Optional[str] = None
    raison: Optional[str] = ""

class ExhumationStatutIn(Schema):
    statut: str

class TransactionIn(Schema):
    montant: float
    type_paiement: str
    numero_telephone: Optional[str] = None

class TerrainIn(Schema):
    superficie_totale: float
    zones: str
    longueur_tombeau: float
    largeur_tombeau: float
    zones_non_exploitables: float = 0
    chemins_m2: float = 0


# ==================== ENDPOINTS PROFIL ====================

@api.get("/profil/{email}")
def get_profil(request, email: str):
    u = get_object_or_404(Utilisateur, email=email)
    reservations_count = Reservation.objects.count()
    validees = Reservation.objects.filter(statut='VALIDE').count()
    en_attente = Reservation.objects.filter(statut='EN_ATTENTE').count()
    return {
        "nom": u.nom,
        "prenom": u.prenom,
        "email": u.email,
        "role": u.role,
        "telephone": u.telephone,
        "reservations": reservations_count,
        "validees": validees,
        "en_attente": en_attente,
    }

@api.put("/profil/{email}")
def update_profil(request, email: str, payload: ProfilUpdateIn):
    u = get_object_or_404(Utilisateur, email=email)
    u.nom = payload.nom
    u.prenom = payload.prenom
    u.telephone = payload.telephone
    u.save()
    journaliser(email, "Modification du profil")
    return {"success": True, "message": "Profil mis à jour"}

@api.post("/auth/change-password")
def change_password(request, payload: ChangePasswordIn):
    u = get_object_or_404(Utilisateur, email=payload.email)
    if not check_password(payload.ancien_mot_de_passe, u.mot_de_passe):
        return 400, {"error": "Ancien mot de passe incorrect"}
    u.mot_de_passe = make_password(payload.nouveau_mot_de_passe)
    u.save()
    journaliser(payload.email, "Changement de mot de passe")
    return {"success": True, "message": "Mot de passe modifié"}


# ==================== ENDPOINTS ADMINISTRATION UTILISATEURS ====================

@api.get("/users")
def liste_users(request):
    return [
        {
            "id": u.id, "nom": u.nom, "prenom": u.prenom, "email": u.email,
            "role": u.role, "telephone": u.telephone,
        }
        for u in Utilisateur.objects.all().order_by('id')
    ]

@api.put("/users/{user_id}")
def update_user(request, user_id: int, payload: UserUpdateIn):
    u = get_object_or_404(Utilisateur, id=user_id)
    if payload.nom is not None:
        u.nom = payload.nom
    if payload.prenom is not None:
        u.prenom = payload.prenom
    if payload.telephone is not None:
        u.telephone = payload.telephone
    if payload.role is not None:
        u.role = payload.role
    u.save()
    journaliser(u.email, "Modification utilisateur (admin)", f"role={u.role}")
    return {"success": True, "message": "Utilisateur mis à jour"}


# ==================== ENDPOINTS CONCESSIONS ====================

@api.get("/concessions")
def liste_concessions(request):
    resultat = []
    for c in Concession.objects.select_related('caveau').all().order_by('-date_debut'):
        resultat.append({
            "id": c.id,
            "caveau": c.caveau.numero if c.caveau else "—",
            "proprietaire_nom": c.proprietaire_nom,
            "proprietaire_telephone": c.proprietaire_telephone,
            "type_concession": c.type_concession,
            "date_debut": c.date_debut.strftime("%d/%m/%Y"),
            "date_fin": c.date_fin.strftime("%d/%m/%Y") if c.date_fin else None,
            "statut": "ACTIVE" if c.est_active else "EXPIREE",
        })
    return resultat

@api.post("/concessions")
def creer_concession(request, payload: ConcessionIn):
    caveau = get_object_or_404(Caveau, id=payload.caveau_id)
    c = Concession.objects.create(
        caveau=caveau,
        proprietaire_nom=payload.proprietaire_nom,
        proprietaire_telephone=payload.proprietaire_telephone,
        proprietaire_email=payload.proprietaire_email,
        type_concession=payload.type_concession,
        date_debut=datetime.strptime(payload.date_debut, "%Y-%m-%d").date(),
        date_fin=datetime.strptime(payload.date_fin, "%Y-%m-%d").date() if payload.date_fin else None,
        est_active=True,
    )
    caveau.statut = 'OCCUPE'
    caveau.save()
    journaliser(None, "Nouvelle concession", f"Caveau {caveau.numero}")
    return {"success": True, "id": c.id}


# ==================== ENDPOINTS EXHUMATIONS ====================

@api.get("/exhumations")
def liste_exhumations(request):
    resultat = []
    for e in Exhumation.objects.all().order_by('-date_demande'):
        resultat.append({
            "id": e.id,
            "nom_defunt": f"{e.defunt_nom} {e.defunt_prenom}".strip(),
            "demandeur_nom": e.demandeur_nom,
            "demandeur_telephone": e.demandeur_telephone,
            "motif": e.raison,
            "date_demande": e.date_demande.strftime("%d/%m/%Y"),
            "statut": e.statut,
        })
    return resultat

@api.post("/exhumations")
def creer_exhumation(request, payload: ExhumationIn):
    concession = None
    if payload.concession_id:
        concession = get_object_or_404(Concession, id=payload.concession_id)
    e = Exhumation.objects.create(
        concession=concession,
        defunt_nom=payload.defunt_nom,
        defunt_prenom=payload.defunt_prenom or "",
        demandeur_nom=payload.demandeur_nom,
        demandeur_telephone=payload.demandeur_telephone,
        raison=payload.raison or "",
    )
    journaliser(None, "Nouvelle demande d'exhumation", payload.defunt_nom)
    return {"success": True, "id": e.id}

@api.put("/exhumations/{exhumation_id}")
def update_exhumation(request, exhumation_id: int, payload: ExhumationStatutIn):
    e = get_object_or_404(Exhumation, id=exhumation_id)
    e.statut = payload.statut
    e.save()
    journaliser(None, "Mise à jour exhumation", f"{e.defunt_nom} -> {payload.statut}")
    return {"success": True}


# ==================== ENDPOINTS TRANSACTIONS / PAIEMENTS ====================

@api.get("/transactions")
def liste_transactions(request):
    resultat = []
    for t in Transaction.objects.all().order_by('-date_transaction'):
        resultat.append({
            "id": t.id,
            "montant": float(t.montant),
            "type_paiement": t.type_paiement,
            "numero_telephone": t.numero_telephone,
            "reference": t.reference,
            "statut": t.statut,
            "date_transaction": t.date_transaction.strftime("%d/%m/%Y %H:%M"),
        })
    return resultat

@api.post("/transactions")
def creer_transaction(request, payload: TransactionIn):
    reference = f"TRX-{int(time.time())}-{random.randint(100, 999)}"
    t = Transaction.objects.create(
        montant=payload.montant,
        type_paiement=payload.type_paiement,
        numero_telephone=payload.numero_telephone,
        reference=reference,
        statut='VALIDE',
    )
    journaliser(None, "Paiement enregistré", f"{payload.type_paiement} - {payload.montant} XAF")
    return {"success": True, "id": t.id, "reference": reference}


# ==================== ENDPOINT AUDIT ====================

@api.get("/audit")
def liste_audit(request):
    logs = AuditLog.objects.select_related('utilisateur').all().order_by('-date_action')[:100]
    return [
        {
            "date": log.date_action.strftime("%d/%m/%Y %H:%M"),
            "utilisateur": log.utilisateur.email if log.utilisateur else "Système",
            "action": log.action,
            "details": log.details or "",
        }
        for log in logs
    ]


# ==================== ENDPOINT TERRAIN ====================

@api.get("/terrain")
def get_terrain(request):
    config, _ = ConfigurationTerrain.objects.get_or_create(id=1)
    return {
        "superficie_totale": config.superficie_totale,
        "zones": config.zones,
        "longueur_tombeau": config.longueur_tombeau,
        "largeur_tombeau": config.largeur_tombeau,
        "zones_non_exploitables": config.zones_non_exploitables,
        "chemins_m2": config.chemins_m2,
    }

@api.put("/terrain")
def update_terrain(request, payload: TerrainIn):
    config, _ = ConfigurationTerrain.objects.get_or_create(id=1)
    config.superficie_totale = payload.superficie_totale
    config.zones = payload.zones
    config.longueur_tombeau = payload.longueur_tombeau
    config.largeur_tombeau = payload.largeur_tombeau
    config.zones_non_exploitables = payload.zones_non_exploitables
    config.chemins_m2 = payload.chemins_m2
    config.save()
    journaliser(None, "Mise à jour configuration terrain")
    return {"success": True, "message": "Configuration enregistrée"}


# ==================== ENDPOINT RAPPORTS ====================

@api.get("/rapports")
def get_rapports(request):
    total = Caveau.objects.count()
    occupes = Caveau.objects.filter(statut='OCCUPE').count()
    taux_occupation = round((occupes / total) * 100, 1) if total else 0
    reservations_mois = Reservation.objects.count()
    revenus_total = sum(float(t.montant) for t in Transaction.objects.filter(statut='VALIDE'))
    return {
        "taux_occupation": taux_occupation,
        "reservations_total": reservations_mois,
        "revenus_total": revenus_total,
    }

# ==================== ENDPOINT ADMIN ====================

@api.post("/admin/login")
def admin_login(request, payload: LoginIn):
    """Endpoint pour la connexion admin"""
    try:
        from django.contrib.auth import authenticate
        
        user = authenticate(username=payload.email, password=payload.mot_de_passe)
        if user is not None and user.is_superuser:
            return {
                "success": True,
                "message": "Admin connecté",
                "email": payload.email,
                "role": "SUPER_ADMIN"
            }
        return {"error": "Identifiants admin incorrects"}, 401
    except Exception as e:
        return {"error": str(e)}, 400