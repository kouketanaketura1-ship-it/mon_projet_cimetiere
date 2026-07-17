# -*- coding: utf-8 -*-
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

# ==================== CONFIGURATION DES LOGS ====================
LOG_DIR = Path(__file__).resolve().parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger('gestion_cimetiere')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(LOG_DIR / 'app.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

email_logger = logging.getLogger('email_sender')
email_logger.setLevel(logging.DEBUG)
email_handler = logging.FileHandler(LOG_DIR / 'email.log', encoding='utf-8')
email_handler.setFormatter(formatter)
email_logger.addHandler(email_handler)

error_handler = logging.FileHandler(LOG_DIR / 'errors.log', encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
logger.addHandler(error_handler)

# ==================== SCHEMAS ====================

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
    smtp_host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
    smtp_port = getattr(settings, 'EMAIL_PORT', 587)
    smtp_user = getattr(settings, 'EMAIL_HOST_USER', None)
    smtp_password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
    from_header = getattr(settings, 'DEFAULT_FROM_EMAIL', smtp_user or '')
    
    email_logger.info(f"Tentative d'envoi a {destinataire}")
    email_logger.info(f"Hote: {smtp_host}, Port: {smtp_port}")
    email_logger.info(f"Utilisateur: {smtp_user}")
    email_logger.info(f"Expediteur: {from_header}")
    
    if not smtp_user or not smtp_password:
        email_logger.error("EMAIL_HOST_USER ou EMAIL_HOST_PASSWORD non configures!")
        print("ERREUR: Les identifiants email ne sont pas configures dans settings.py")
        return False
    
    if not from_header:
        email_logger.error("DEFAULT_FROM_EMAIL non configure!")
        print("ERREUR: DEFAULT_FROM_EMAIL non configure dans settings.py")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = from_header
    msg['To'] = destinataire
    msg['Subject'] = sujet
    msg.attach(MIMEText(message, 'plain'))
    
    context = ssl.create_default_context()
    retries = getattr(settings, 'EMAIL_SEND_RETRIES', 3)
    timeout = getattr(settings, 'EMAIL_TIMEOUT', 20)
    backoff = getattr(settings, 'EMAIL_BACKOFF_SECONDS', 1)
    
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            email_logger.info(f"Tentative {attempt}/{retries}")
            
            with smtplib.SMTP(smtp_host, smtp_port, timeout=timeout) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                
                server.sendmail(from_header, [destinataire], msg.as_string())
                email_logger.info(f"Email envoyer avec succes a {destinataire}")
                
                print(f"Email envoyer a {destinataire} (attempt {attempt})")
                return True
                
        except smtplib.SMTPAuthenticationError as e:
            email_logger.error(f"ERREUR AUTHENTIFICATION SMTP: {e}")
            last_exc = e
            break
            
        except Exception as e:
            email_logger.error(f"ERREUR SMTP: {e}")
            last_exc = e
        
        if attempt < retries:
            wait_time = backoff * attempt
            email_logger.info(f"Attente de {wait_time}s avant reessai...")
            time.sleep(wait_time)
    
    email_logger.error(f"Echec envoi email apres {retries} tentatives: {last_exc}")
    return False

# ==================== FONCTIONS MFA ====================

def journaliser(email, action, details=""):
    try:
        utilisateur = None
        if email:
            utilisateur = Utilisateur.objects.filter(email=email).first()
            if utilisateur:
                logger.info(f"AUDIT - {action} par {email}: {details}")
            else:
                logger.warning(f"AUDIT - {action} par utilisateur inconnu ({email}): {details}")
        else:
            logger.info(f"AUDIT - {action} par Systeme: {details}")
        
        AuditLog.objects.create(utilisateur=utilisateur, action=action, details=details)
    except Exception as e:
        logger.error(f"Impossible d'enregistrer l'audit log: {e}")

def generer_code_mfa():
    code = ''.join(random.choices(string.digits, k=6))
    logger.debug(f"Code MFA genere: {code}")
    return code

def envoyer_code_mfa(email, code):
    sujet = "Code de verification - Gestion de Cimetiere"
    message = f"""Bonjour,

Voici votre code de verification a double facteur :

CODE : {code}

Ce code est valable pendant 5 minutes.

Si vous n'etes pas a l'origine de cette demande, ignorez cet email.

---
Gestion de Cimetiere - Application de Gestion Funeraire
"""
    logger.info(f"Envoi du code MFA a {email}")
    result = envoyer_email(email, sujet, message)
    if result:
        logger.info(f"Code MFA envoyer avec succes a {email}")
    else:
        logger.error(f"Echec envoi du code MFA a {email}")
    return result

def sauvegarder_code_mfa(utilisateur, code):
    try:
        anciens = MFACode.objects.filter(utilisateur=utilisateur, est_utilise=False).delete()
        if anciens[0] > 0:
            logger.debug(f"{anciens[0]} ancien(s) code(s) MFA supprimes pour {utilisateur.email}")
        
        date_expiration = timezone.now() + timedelta(minutes=5)
        mfa = MFACode.objects.create(
            utilisateur=utilisateur,
            code=code,
            date_expiration=date_expiration
        )
        logger.info(f"Code MFA sauvegarde pour {utilisateur.email} (expire a {date_expiration})")
        return mfa
    except Exception as e:
        logger.error(f"Erreur sauvegarde code MFA: {e}")
        raise

def verifier_code_mfa(utilisateur, code):
    try:
        logger.info(f"Verification du code MFA pour {utilisateur.email}")
        
        mfa = MFACode.objects.filter(
            utilisateur=utilisateur,
            code=code,
            est_utilise=False
        ).order_by('-date_creation').first()
        
        if not mfa:
            logger.warning(f"Code MFA invalide pour {utilisateur.email}: {code}")
            return False, "Code invalide"
        
        if not mfa.est_valide():
            logger.warning(f"Code MFA expire pour {utilisateur.email} (cree a {mfa.date_creation})")
            return False, "Code expire (5 minutes)"
        
        mfa.est_utilise = True
        mfa.save()
        logger.info(f"Code MFA valide avec succes pour {utilisateur.email}")
        return True, "Code valide"
        
    except Exception as e:
        logger.error(f"Erreur lors de la verification MFA: {e}")
        return False, f"Erreur systeme: {str(e)}"

# ==================== ENDPOINTS AUTH ====================

@api.post("/auth/register", response={200: RegisterOut, 400: ErrorOut})
def register(request, payload: UtilisateurIn):
    try:
        logger.info(f"Tentative d'inscription: {payload.email}")
        
        email = payload.email.strip().lower()
        logger.debug(f"Email original: {payload.email} -> nettoye: {email}")
        
        if "@" not in email:
            logger.warning(f"Email invalide (sans @): {email}")
            return 400, {"error": "Email invalide. Il doit contenir '@'."}
        
        domaine = email.split("@")[1]
        if "." not in domaine:
            email_corrige = email + ".com"
            logger.info(f"Email corrige: {email} -> {email_corrige}")
            email = email_corrige
        
        if Utilisateur.objects.filter(email=email).exists():
            logger.warning(f"Tentative d'inscription avec email existant: {email}")
            return 400, {"error": "Cet email est deja utilise"}
        
        logger.info(f"Creation de l'utilisateur: {email}")
        utilisateur = Utilisateur.objects.create(
            nom=payload.nom.strip(),
            prenom=payload.prenom.strip(),
            email=email,
            mot_de_passe=make_password(payload.mot_de_passe),
            role=payload.role,
            telephone=payload.telephone.strip() if payload.telephone else None,
            mfa_active=True
        )
        logger.info(f"Utilisateur cree avec succes: ID={utilisateur.id}")
        
        code = generer_code_mfa()
        sauvegarder_code_mfa(utilisateur, code)
        sent = envoyer_code_mfa(email, code)
        
        if not sent:
            logger.error(f"Echec envoi code MFA pour {email}")
            utilisateur.delete()
            logger.warning(f"Utilisateur supprime car code MFA non envoyer: {email}")
            return 400, {"error": "Impossible d'envoyer le code MFA - verifiez la configuration d'email."}
        
        journaliser(email, "Inscription reussie", f"Role: {payload.role}")
        logger.info(f"Inscription terminee avec succes pour {email}")
        
        return 200, {
            "success": True,
            "message": "Compte cree. Code MFA envoyer par email.",
            "email": email,
            "mfa_required": True
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'inscription: {str(e)}", exc_info=True)
        return 400, {"error": f"Erreur: {str(e)}"}

@api.post("/auth/login", response={200: LoginOut, 400: ErrorOut, 401: ErrorOut, 404: ErrorOut})
def login(request, payload: LoginIn):
    try:
        logger.info(f"Tentative de connexion: {payload.email}")
        
        utilisateur = Utilisateur.objects.get(email=payload.email)
        logger.debug(f"Utilisateur trouve: ID={utilisateur.id}")
        
        if not check_password(payload.mot_de_passe, utilisateur.mot_de_passe):
            logger.warning(f"Mot de passe incorrect pour {payload.email}")
            journaliser(payload.email, "Echec connexion - mot de passe incorrect")
            return 401, {"error": "Mot de passe incorrect"}
        
        logger.info(f"Mot de passe valide pour {payload.email}")
        
        code = generer_code_mfa()
        sauvegarder_code_mfa(utilisateur, code)
        sent = envoyer_code_mfa(payload.email, code)
        
        if not sent:
            logger.error(f"Echec envoi code MFA pour {payload.email}")
            return 400, {"error": "Impossible d'envoyer le code MFA - verifiez la configuration d'email."}
        
        logger.info(f"Code MFA envoyer a {payload.email}")
        journaliser(payload.email, "Connexion - code MFA envoyer")
        
        return 200, {
            "success": True,
            "message": "Code MFA envoyer par email",
            "email": utilisateur.email,
            "mfa_required": True
        }
        
    except Utilisateur.DoesNotExist:
        logger.warning(f"Utilisateur non trouve: {payload.email}")
        return 404, {"error": "Utilisateur non trouve"}
    except Exception as e:
        logger.error(f"Erreur lors de la connexion: {str(e)}", exc_info=True)
        return 400, {"error": str(e)}

@api.post("/auth/mfa/verify", response={200: MFAOut, 400: ErrorOut})
def verify_mfa(request, payload: MFAIn):
    try:
        logger.info(f"Verification MFA for {payload.email}")
        
        utilisateur = get_object_or_404(Utilisateur, email=payload.email)
        
        valide, message = verifier_code_mfa(utilisateur, payload.code)
        
        if not valide:
            logger.warning(f"{message} pour {payload.email}")
            journaliser(payload.email, "Echec verification MFA", message)
            return 400, {"error": message}
        
        utilisateur.mfa_active = True
        utilisateur.save()
        
        logger.info(f"MFA valide avec succes pour {payload.email}")
        journaliser(utilisateur.email, "Connexion (MFA verifie)", utilisateur.role)
        
        return 200, {
            "success": True,
            "message": "Connexion validee",
            "email": utilisateur.email,
            "role": utilisateur.role
        }
        
    except Exception as e:
        logger.error(f"Erreur verification MFA: {str(e)}", exc_info=True)
        return 400, {"error": str(e)}

@api.post("/auth/mfa/resend")
def resend_mfa(request, payload: MFAIn):
    try:
        logger.info(f"Demande de renvoi code MFA pour {payload.email}")
        
        utilisateur = get_object_or_404(Utilisateur, email=payload.email)
        
        code = generer_code_mfa()
        sauvegarder_code_mfa(utilisateur, code)
        sent = envoyer_code_mfa(payload.email, code)
        
        if not sent:
            logger.error(f"Echec renvoi code MFA pour {payload.email}")
            return {"error": "Impossible d'envoyer le code MFA - verifiez la configuration d'email."}, 400
        
        logger.info(f"Code MFA renvoye a {payload.email}")
        return {
            "success": True,
            "message": "Nouveau code MFA envoyer par email"
        }
        
    except Exception as e:
        logger.error(f"Erreur renvoi MFA: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

@api.get("/hello")
def hello(request):
    logger.info("Ping API")
    return {"message": "API OK"}

@api.post("/auth/test-email")
def test_email_endpoint(request, payload: TestEmailIn):
    logger.info(f"Test email vers {payload.email}")
    
    sujet = "[TEST] Envoi email - Gestion de Cimetiere"
    message = f"Test d'envoi vers {payload.email} depuis l'API. Si tu recois cet email, c'est OK."
    sent = envoyer_email(payload.email, sujet, message)
    
    log_dir = LOG_DIR / 'email.log'
    log_tail = ""
    try:
        if log_dir.exists():
            with open(log_dir, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                tail = lines[-200:] if len(lines) > 200 else lines
                log_tail = ''.join(tail)
    except Exception as e:
        log_tail = f"Erreur lecture log: {e}"
        logger.error(f"Erreur lecture log: {e}")
    
    return {
        "success": sent,
        "sent": sent,
        "log_tail": log_tail,
        "config": {
            "host": getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com'),
            "port": getattr(settings, 'EMAIL_PORT', 587),
            "user": getattr(settings, 'EMAIL_HOST_USER', None),
            "from": getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        }
    }

# ==================== CAVEAUX ENDPOINTS ====================

@api.get("/caveaux")
def liste_caveaux(request):
    try:
        logger.info("Liste des caveaux demandee")
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
        logger.info(f"{len(resultat)} caveaux charges")
        return resultat
    except Exception as e:
        logger.error(f"Erreur liste caveaux: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

@api.get("/statistiques")
def statistiques(request):
    try:
        total = Caveau.objects.count()
        disponibles = Caveau.objects.filter(statut='DISPONIBLE').count()
        reserves = Caveau.objects.filter(statut='RESERVE').count()
        occupes = Caveau.objects.filter(statut='OCCUPE').count()
        taux_occupation = round((occupes / total * 100), 1) if total > 0 else 0
        
        logger.info(f"Statistiques: Total={total}, Occupe={occupes} ({taux_occupation}%)")
        
        return {
            "total": total,
            "disponibles": disponibles,
            "reserves": reserves,
            "occupes": occupes,
            "taux_occupation": taux_occupation,
        }
    except Exception as e:
        logger.error(f"Erreur statistiques: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

@api.get("/reservations")
def liste_reservations(request):
    try:
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
        logger.info(f"{len(resultat)} reservations chargees")
        return resultat
    except Exception as e:
        logger.error(f"Erreur liste reservations: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

@api.post("/reservations")
def creer_reservation(request):
    try:
        body = json.loads(request.body)
        caveau_id = body.get("caveau_id")
        client_email = body.get("client_email", "test@test.com")
        
        logger.info(f"Nouvelle reservation pour caveau {caveau_id} par {client_email}")
        
        caveau = get_object_or_404(Caveau, id=caveau_id)
        
        reservation = Reservation.objects.create(
            caveau=caveau,
            client_nom=body.get("client_nom", "Inconnu"),
            client_prenom=body.get("client_prenom", "Inconnu"),
            client_email=client_email,
            client_telephone=body.get("client_telephone", "00000000"),
            nom_defunt=body.get("nom_defunt", "Inconnu"),
            prenom_defunt=body.get("prenom_defunt", "Inconnu"),
            date_naissance=datetime.strptime(body.get("date_naissance", "2000-01-01"), "%Y-%m-%d").date(),
            date_deces=datetime.strptime(body.get("date_deces", "2000-01-01"), "%Y-%m-%d").date(),
            statut='EN_ATTENTE'
        )
        
        caveau.statut = 'RESERVE'
        caveau.save()
        
        logger.info(f"Reservation creee: ID={reservation.id}")
        journaliser(client_email, "Nouvelle reservation", f"Caveau {caveau.numero}")
        
        return {"success": True, "id": reservation.id}
    except Exception as e:
        logger.error(f"Erreur creation reservation: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

# ==================== SCHEMAS ADDITIONNELS ====================

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

# ==================== PROFIL ENDPOINTS ====================

@api.get("/profil/{email}")
def get_profil(request, email: str):
    try:
        logger.info(f"Consultation profil: {email}")
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
    except Exception as e:
        logger.error(f"Erreur consultation profil {email}: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

@api.put("/profil/{email}")
def update_profil(request, email: str, payload: ProfilUpdateIn):
    try:
        logger.info(f"Mise a jour profil: {email}")
        u = get_object_or_404(Utilisateur, email=email)
        u.nom = payload.nom
        u.prenom = payload.prenom
        u.telephone = payload.telephone
        u.save()
        
        logger.info(f"Profil mis a jour: {email}")
        journaliser(email, "Modification du profil")
        return {"success": True, "message": "Profil mis a jour"}
    except Exception as e:
        logger.error(f"Erreur mise a jour profil {email}: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

@api.post("/auth/change-password")
def change_password(request, payload: ChangePasswordIn):
    try:
        logger.info(f"Changement de mot de passe pour {payload.email}")
        u = get_object_or_404(Utilisateur, email=payload.email)
        
        if not check_password(payload.ancien_mot_de_passe, u.mot_de_passe):
            logger.warning(f"Ancien mot de passe incorrect pour {payload.email}")
            return 400, {"error": "Ancien mot de passe incorrect"}
        
        u.mot_de_passe = make_password(payload.nouveau_mot_de_passe)
        u.save()
        
        logger.info(f"Mot de passe change pour {payload.email}")
        journaliser(payload.email, "Changement de mot de passe")
        return {"success": True, "message": "Mot de passe modifie"}
    except Exception as e:
        logger.error(f"Erreur changement mot de passe: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

# ==================== ADMIN ENDPOINTS ====================

@api.get("/users")
def liste_users(request):
    try:
        logger.info("Liste des utilisateurs demandee")
        users = [
            {
                "id": u.id, "nom": u.nom, "prenom": u.prenom, "email": u.email,
                "role": u.role, "telephone": u.telephone,
            }
            for u in Utilisateur.objects.all().order_by('id')
        ]
        logger.info(f"{len(users)} utilisateurs charges")
        return users
    except Exception as e:
        logger.error(f"Erreur liste utilisateurs: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

@api.put("/users/{user_id}")
def update_user(request, user_id: int, payload: UserUpdateIn):
    try:
        logger.info(f"Mise a jour utilisateur ID {user_id}")
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
        logger.info(f"Utilisateur {u.email} mis a jour")
        journaliser(u.email, "Modification utilisateur (admin)", f"role={u.role}")
        return {"success": True, "message": "Utilisateur mis a jour"}
    except Exception as e:
        logger.error(f"Erreur mise a jour utilisateur {user_id}: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

# ==================== CONCESSIONS ENDPOINTS ====================

@api.get("/concessions")
def liste_concessions(request):
    try:
        logger.info("Liste des concessions demandee")
        resultat = []
        for c in Concession.objects.select_related('caveau').all().order_by('-date_debut'):
            resultat.append({
                "id": c.id,
                "caveau": c.caveau.numero if c.caveau else "-",
                "proprietaire_nom": c.proprietaire_nom,
                "proprietaire_telephone": c.proprietaire_telephone,
                "type_concession": c.type_concession,
                "date_debut": c.date_debut.strftime("%d/%m/%Y"),
                "date_fin": c.date_fin.strftime("%d/%m/%Y") if c.date_fin else None,
                "statut": "ACTIVE" if c.est_active else "EXPIREE",
            })
        logger.info(f"{len(resultat)} concessions chargees")
        return resultat
    except Exception as e:
        logger.error(f"Erreur liste concessions: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

@api.post("/concessions")
def creer_concession(request, payload: ConcessionIn):
    try:
        logger.info(f"Creation concession pour caveau {payload.caveau_id}")
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
        
        logger.info(f"Concession creee: ID={c.id}")
        journaliser(None, "Nouvelle concession", f"Caveau {caveau.numero}")
        return {"success": True, "id": c.id}
    except Exception as e:
        logger.error(f"Erreur creation concession: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

# ==================== EXHUMATIONS ENDPOINTS ====================

@api.get("/exhumations")
def liste_exhumations(request):
    try:
        logger.info("Liste des exhumations demandee")
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
        logger.info(f"{len(resultat)} exhumations chargees")
        return resultat
    except Exception as e:
        logger.error(f"Erreur liste exhumations: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

@api.post("/exhumations")
def creer_exhumation(request, payload: ExhumationIn):
    try:
        logger.info(f"Nouvelle demande d'exhumation pour {payload.defunt_nom}")
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
        
        logger.info(f"Demande d'exhumation creee: ID={e.id}")
        journaliser(None, "Nouvelle demande d'exhumation", payload.defunt_nom)
        return {"success": True, "id": e.id}
    except Exception as e:
        logger.error(f"Erreur creation exhumation: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

@api.put("/exhumations/{exhumation_id}")
def update_exhumation(request, exhumation_id: int, payload: ExhumationStatutIn):
    try:
        logger.info(f"Mise a jour exhumation {exhumation_id}")
        e = get_object_or_404(Exhumation, id=exhumation_id)
        e.statut = payload.statut
        e.save()
        
        logger.info(f"Exhumation {exhumation_id} mise a jour: {payload.statut}")
        journaliser(None, "Mise a jour exhumation", f"{e.defunt_nom} -> {payload.statut}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Erreur mise a jour exhumation {exhumation_id}: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

# ==================== TRANSACTIONS ENDPOINTS ====================

@api.get("/transactions")
def liste_transactions(request):
    try:
        logger.info("Liste des transactions demandee")
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
        logger.info(f"{len(resultat)} transactions chargees")
        return resultat
    except Exception as e:
        logger.error(f"Erreur liste transactions: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

@api.post("/transactions")
def creer_transaction(request, payload: TransactionIn):
    try:
        logger.info(f"Nouvelle transaction: {payload.type_paiement} - {payload.montant} XAF")
        reference = f"TRX-{int(time.time())}-{random.randint(100, 999)}"
        
        t = Transaction.objects.create(
            montant=payload.montant,
            type_paiement=payload.type_paiement,
            numero_telephone=payload.numero_telephone,
            reference=reference,
            statut='VALIDE',
        )
        
        logger.info(f"Transaction creee: {reference}")
        journaliser(None, "Paiement enregistre", f"{payload.type_paiement} - {payload.montant} XAF")
        return {"success": True, "id": t.id, "reference": reference}
    except Exception as e:
        logger.error(f"Erreur creation transaction: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

# ==================== AUDIT ENDPOINT ====================

@api.get("/audit")
def liste_audit(request):
    try:
        logger.info("Liste des logs audit demandee")
        logs = AuditLog.objects.select_related('utilisateur').all().order_by('-date_action')[:100]
        resultat = [
            {
                "date": log.date_action.strftime("%d/%m/%Y %H:%M"),
                "utilisateur": log.utilisateur.email if log.utilisateur else "Systeme",
                "action": log.action,
                "details": log.details or "",
            }
            for log in logs
        ]
        logger.info(f"{len(resultat)} logs audit charges")
        return resultat
    except Exception as e:
        logger.error(f"Erreur liste audit: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

# ==================== TERRAIN ENDPOINT ====================

@api.get("/terrain")
def get_terrain(request):
    try:
        logger.info("Configuration terrain demandee")
        config, _ = ConfigurationTerrain.objects.get_or_create(id=1)
        resultat = {
            "superficie_totale": config.superficie_totale,
            "zones": config.zones,
            "longueur_tombeau": config.longueur_tombeau,
            "largeur_tombeau": config.largeur_tombeau,
            "zones_non_exploitables": config.zones_non_exploitables,
            "chemins_m2": config.chemins_m2,
        }
        logger.info("Configuration terrain chargee")
        return resultat
    except Exception as e:
        logger.error(f"Erreur recuperation terrain: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

@api.put("/terrain")
def update_terrain(request, payload: TerrainIn):
    try:
        logger.info("Mise a jour configuration terrain")
        config, _ = ConfigurationTerrain.objects.get_or_create(id=1)
        config.superficie_totale = payload.superficie_totale
        config.zones = payload.zones
        config.longueur_tombeau = payload.longueur_tombeau
        config.largeur_tombeau = payload.largeur_tombeau
        config.zones_non_exploitables = payload.zones_non_exploitables
        config.chemins_m2 = payload.chemins_m2
        config.save()
        
        logger.info("Configuration terrain mise a jour")
        journaliser(None, "Mise a jour configuration terrain")
        return {"success": True, "message": "Configuration enregistree"}
    except Exception as e:
        logger.error(f"Erreur mise a jour terrain: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

# ==================== RAPPORT ENDPOINT ====================

@api.get("/rapports")
def get_rapports(request):
    try:
        logger.info("Generation des rapports")
        total = Caveau.objects.count()
        occupes = Caveau.objects.filter(statut='OCCUPE').count()
        taux_occupation = round((occupes / total) * 100, 1) if total else 0
        reservations_mois = Reservation.objects.count()
        revenus_total = sum(float(t.montant) for t in Transaction.objects.filter(statut='VALIDE'))
        
        resultat = {
            "taux_occupation": taux_occupation,
            "reservations_total": reservations_mois,
            "revenus_total": revenus_total,
        }
        logger.info(f"Rapports generes: {resultat}")
        return resultat
    except Exception as e:
        logger.error(f"Erreur generation rapports: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400

# ==================== ADMIN LOGIN ENDPOINT ====================

@api.post("/admin/login")
def admin_login(request, payload: LoginIn):
    try:
        logger.info(f"Tentative de connexion admin: {payload.email}")
        from django.contrib.auth import authenticate
        
        user = authenticate(username=payload.email, password=payload.mot_de_passe)
        if user is not None and user.is_superuser:
            logger.info(f"Admin connecte: {payload.email}")
            return {
                "success": True,
                "message": "Admin connecte",
                "email": payload.email,
                "role": "SUPER_ADMIN"
            }
        logger.warning(f"Echec connexion admin: {payload.email}")
        return {"error": "Identifiants admin incorrects"}, 401
    except Exception as e:
        logger.error(f"Erreur connexion admin: {str(e)}", exc_info=True)
        return {"error": str(e)}, 400