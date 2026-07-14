import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cimetiere_api.settings')
django.setup()

from cimetiere.models import Caveau

# Nouvelles coordonnées regroupées
nouvelles_coords = {
    "C-001": (-4.7692, 11.8664),
    "C-002": (-4.7691, 11.8666),
    "C-003": (-4.7690, 11.8668),
    "C-004": (-4.7689, 11.8670),
    "C-005": (-4.7688, 11.8672),
}

for numero, (lat, lon) in nouvelles_coords.items():
    try:
        caveau = Caveau.objects.get(numero=numero)
        caveau.latitude = lat
        caveau.longitude = lon
        caveau.save()
        print(f"✅ {numero} : ({lat}, {lon})")
    except Caveau.DoesNotExist:
        print(f"❌ {numero} non trouvé")