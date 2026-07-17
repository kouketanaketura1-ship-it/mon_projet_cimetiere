import os
import ssl
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Lecture des identifiants depuis les variables d'environnement si définies
SMTP_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("EMAIL_PORT", 587))
SMTP_USER = os.getenv("EMAIL_HOST_USER", "kouketanaketura1@gmail.com")
SMTP_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", SMTP_USER)


def generate_mfa_code(length: int = 6) -> str:
    """Génère un code numérique MFA de `length` chiffres."""
    range_start = 10**(length - 1)
    range_end = (10**length) - 1
    return str(random.randint(range_start, range_end))


def envoyer_email(destinataire: str, sujet: str, message_plain: str, message_html: str = None, timeout: int = 10) -> bool:
    """Envoie un email via SMTP Gmail. Retourne True si OK, False sinon.

    - Utilise TLS avec contexte sécurisé
    - Lit les credentials depuis variables d'env (sécurité)
    - Fournit un message texte + optionnel HTML
    - Le mot de passe doit être un App Password Gmail
    """
    if not SMTP_PASSWORD:
        print("❌ EMAIL_HOST_PASSWORD est vide. Ajoutez un App Password Gmail dans Railway.")
        return False

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
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, destinataire, msg.as_string())

        print(f"✅ Email envoyé à {destinataire}")
        return True
    except Exception as e:
        print(f"❌ Échec envoi email: {e}")
        return False

# ===== TEST =====
if __name__ == "__main__":
    mon_email = os.getenv("TEST_EMAIL_TO", "kouketanaketura1@gmail.com")
    code_test = generate_mfa_code()

    sujet = "🔐 Test MFA - Gestion de Cimetière"
    message = f"""Bonjour,

Ceci est un test d'envoi d'email avec Gmail.

🔑 CODE DE TEST : {code_test}

Si tu reçois cet email, la configuration fonctionne !

---
Gestion de Cimetière
"""

    envoyer_email(mon_email, sujet, message)