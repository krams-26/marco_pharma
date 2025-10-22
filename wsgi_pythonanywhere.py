# Fichier WSGI pour PythonAnywhere
# Copiez ce contenu dans le fichier WSGI de votre Web App sur PythonAnywhere

import sys
import os
from dotenv import load_dotenv

# REMPLACEZ 'votre_username' par votre nom d'utilisateur PythonAnywhere
USERNAME = 'votre_username'

# Ajouter le chemin de votre projet
path = f'/home/{USERNAME}/Marco-Pharma'
if path not in sys.path:
    sys.path.insert(0, path)

# Charger les variables d'environnement
load_dotenv(os.path.join(path, '.env'))

# Activer l'environnement virtuel
activate_this = f'/home/{USERNAME}/.virtualenvs/marco-pharma-env/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Importer l'application Flask
from run import app as application

