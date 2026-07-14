from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from .api import api

# Une vue simple pour la page d'accueil
def home(request):
    return HttpResponse("""
        <h1>Bienvenue sur l'API de Gestion de Cimetière</h1>
        <p>L'API fonctionne correctement !</p>
        <p>Va sur <a href='/api/hello'>/api/hello</a> pour tester.</p>
        <p>La documentation de l'API est disponible sur <a href='/api/docs'>/api/docs</a></p>
    """)

urlpatterns = [
    path('', home),  # Page d'accueil
    path('admin/', admin.site.urls),
    path('api/', api.urls),  # L'API Ninja
]