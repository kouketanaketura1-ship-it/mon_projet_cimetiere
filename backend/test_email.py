import os
import ssl
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Lecture des identifiants depuis les variables d'environnement si définies
SMTP_HOST = os.getenv("SMTP_HOST", "smtp-relay.brevo.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "b029ee001@smtp-brevo.com")

# ⚠️ IMPORTANT: Cette adresse DOIT être authentifiée/validée dans Brevo
FROM_EMAIL = os.getenv("FROM_EMAIL", "kouketanaketura1@gmail.com")


def generate_mfa_code(length: int = 6) -> str:
    """Génère un code numérique MFA de `length` chiffres."""
    range_start = 10**(length - 1)
    range_end = (10**length) - 1
    return str(random.randint(range_start, range_end))


def envoyer_email(destinataire: str, sujet: str, message_plain: str, message_html: str = None, timeout: int = 10) -> bool:
    """Envoie un email via SMTP (Brevo). Retourne True si OK, False sinon.

    - Utilise TLS avec contexte sécurisé
    - Lit les credentials depuis variables d'env (sécurité)
    - Fournit un message texte + optionnel HTML
    """
    msg = MIMEMultipart("alternative")
    msg['From'] = FROM_EMAIL
    msg['To'] = destinataire
    msg['Subject'] = sujet

    # Partie texte
    part1 = MIMEText(message_plain, 'plain')
    msg.attach(part1)

    # Partie HTML optionnelle
    if message_html:
        part2 = MIMEText(message_html, 'html')
        msg.attach(part2)

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=timeout) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(SMTP_USER)
            server.sendmail(FROM_EMAIL, destinataire, msg.as_string())

        print(f"✅ Email envoyé à {destinataire}")
        return True
    except Exception as e:
        # Ne pas exposer les credentials dans le log
        print(f"❌ Échec envoi email: {e}")
        return False

# ===== TEST =====
if __name__ == "__main__":
    mon_email = "kouketanaketura1@gmail.com"
    code_test = "123456"
    
    sujet = "🔐 Test MFA - Gestion de Cimetière"
    message = f"""Bonjour,

Ceci est un test d'envoi d'email avec Brevo.

🔑 CODE DE TEST : {code_test}

Si tu reçois cet email, la configuration fonctionne !

---
Gestion de Cimetière
"""
    
    envoyer_email(mon_email, sujet, message)