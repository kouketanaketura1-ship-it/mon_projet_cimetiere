import json
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from cimetiere.models import AuditLog, Caveau, ConfigurationCimetiere, Reservation, Utilisateur


class ReservationWorkflowTests(TestCase):
    def setUp(self):
        self.caveau = Caveau.objects.create(
            numero="A-001",
            section="Section A",
            bloc="Bloc 1",
            latitude=-4.7692,
            longitude=11.8664,
        )

    def test_reservation_creation_and_validation_create_audit_logs(self):
        payload = {
            "caveau_id": self.caveau.id,
            "client_nom": "Dupont",
            "client_prenom": "Jean",
            "client_email": "jean@example.com",
            "client_telephone": "+243999999999",
            "nom_defunt": "Dupont",
            "prenom_defunt": "Marie",
            "date_naissance": "1950-01-01",
            "date_deces": "2024-02-02",
        }

        response = self.client.post(
            "/api/reservations",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_USER_ROLE="CLIENT",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservation.objects.count(), 1)
        self.caveau.refresh_from_db()
        self.assertEqual(self.caveau.statut, "RESERVE")
        self.assertTrue(AuditLog.objects.filter(action="create_reservation").exists())

        reservation = Reservation.objects.get()
        validation_response = self.client.post(
            f"/api/reservations/{reservation.id}/valider",
            HTTP_X_USER_ROLE="ADMIN",
        )

        self.assertEqual(validation_response.status_code, 200)
        reservation.refresh_from_db()
        self.assertEqual(reservation.statut, "VALIDE")
        self.caveau.refresh_from_db()
        self.assertEqual(self.caveau.statut, "OCCUPE")
        self.assertTrue(AuditLog.objects.filter(action="validate_reservation").exists())


class TerrainConfigurationTests(TestCase):
    def test_terrain_configuration_can_be_saved(self):
        payload = {
            "superficie_totale": 4500.0,
            "zones": ["Section A", "Section B"],
            "taille_tombeau_longueur": 2.5,
            "taille_tombeau_largeur": 1.2,
            "zones_non_exploitables": 2,
            "chemins": 180.0,
        }

        response = self.client.post(
            "/api/terrain/configuration",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ConfigurationCimetiere.objects.count(), 1)


class MfaAuthenticationTests(TestCase):
    def test_register_requires_mfa_verification(self):
        payload = {
            "nom": "Musa",
            "prenom": "Jean",
            "email": "musa@example.com",
            "mot_de_passe": "secret123",
            "role": "CLIENT",
        }

        response = self.client.post(
            "/api/auth/register",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["requires_mfa"])
        user = Utilisateur.objects.get(email="musa@example.com")
        self.assertTrue(user.mfa_code)

    def test_login_and_verification_succeeds(self):
        user = Utilisateur.objects.create(
            nom="Doe",
            prenom="Jane",
            email="jane@example.com",
            mot_de_passe=make_password("secret123"),
            role="CLIENT",
        )

        login_response = self.client.post(
            "/api/auth/login",
            data=json.dumps({"email": "jane@example.com", "mot_de_passe": "secret123"}),
            content_type="application/json",
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(login_response.json()["requires_mfa"])
        user.refresh_from_db()

        verify_response = self.client.post(
            "/api/auth/mfa/verify",
            data=json.dumps({"email": "jane@example.com", "code": user.mfa_code}),
            content_type="application/json",
        )

        self.assertEqual(verify_response.status_code, 200)
        self.assertTrue(verify_response.json()["success"])
