from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings
from pathlib import Path
import shutil
import os
from django.apps import apps


class Command(BaseCommand):
    help = 'Exporte les données via `dumpdata` et copie le sqlite (si présent). Génère un schema simplifié.'

    def handle(self, *args, **options):
        base = Path(settings.BASE_DIR)
        exports = base / 'exports'
        exports.mkdir(parents=True, exist_ok=True)

        # 1) dumpdata JSON
        try:
            from io import StringIO
            out = StringIO()
            management.call_command('dumpdata', '--indent', '2', stdout=out)
            data = out.getvalue()
            (exports / 'data_dump.json').write_text(data, encoding='utf-8')
            self.stdout.write(self.style.SUCCESS(f"Dump JSON écrit dans {exports / 'data_dump.json'}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur dumpdata: {e}"))

        # 2) copier sqlite si présent
        sqlite_path = base / 'db.sqlite3'
        if sqlite_path.exists():
            try:
                shutil.copy2(sqlite_path, exports / 'db.sqlite3')
                self.stdout.write(self.style.SUCCESS(f"Fichier sqlite copié: {exports / 'db.sqlite3'}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Impossible de copier sqlite: {e}"))
        else:
            self.stdout.write(self.style.WARNING("Aucun fichier db.sqlite3 trouvé à la racine du projet."))

        # 3) générer un schéma simplifié basé sur les modèles
        try:
            lines = []
            for model in apps.get_models():
                meta = model._meta
                table = meta.db_table
                lines.append(f"TABLE: {table}")
                for field in meta.get_fields():
                    # n'inclure que les champs concrets
                    if hasattr(field, 'column') and field.column:
                        fname = field.column
                        ftype = field.get_internal_type()
                        lines.append(f"  - {fname}: {ftype}")
                lines.append('')

            (exports / 'schema_simple.txt').write_text('\n'.join(lines), encoding='utf-8')
            self.stdout.write(self.style.SUCCESS(f"Schéma simplifié écrit dans {exports / 'schema_simple.txt'}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur génération schéma: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Export terminé dans {exports}"))
