from importlib import reload
from unittest.mock import patch

from django.test import SimpleTestCase

import cimetiere_api.settings as settings_module


class EmailBackendSelectionTests(SimpleTestCase):
    def test_uses_smtp_backend_when_gmail_credentials_exist(self):
        with patch.dict(
            "os.environ",
            {
                "DEBUG": "True",
                "EMAIL_HOST_USER": "kouketanaketura1@gmail.com",
                "EMAIL_HOST_PASSWORD": "app-password-example",
            },
            clear=False,
        ):
            reloaded = reload(settings_module)
            self.assertEqual(
                reloaded.EMAIL_BACKEND,
                "django.core.mail.backends.smtp.EmailBackend",
            )
