# 🚀 GUIDE COMPLET - DÉPLOIEMENT SUR PYTHONANYWHERE

## 📋 PRÉREQUIS

1. ✅ Compte PythonAnywhere (gratuit ou payant)
2. ✅ Application Marco-Pharma prête
3. ✅ Fichiers `requirements.txt` et `runtime.txt` à jour

---

## ÉTAPE 1️⃣ : CRÉER UN COMPTE ET SE CONNECTER

1. Allez sur **https://www.pythonanywhere.com**
2. Créez un compte (gratuit ou payant selon vos besoins)
3. Connectez-vous à votre tableau de bord

---

## ÉTAPE 2️⃣ : CRÉER UNE BASE DE DONNÉES MYSQL

### 2.1 Accéder à l'onglet Databases

1. Dans le menu principal, cliquez sur **"Databases"**
2. Faites défiler jusqu'à la section **"MySQL"**

### 2.2 Initialiser MySQL

1. Si c'est votre première base de données, vous verrez un bouton **"Initialize MySQL"**
2. Cliquez dessus et définissez un **mot de passe MySQL** (NOTEZ-LE BIEN!)
3. Attendez que l'initialisation soit terminée

### 2.3 Créer la base de données

1. Dans la section **"Create a new database"**
2. Entrez le nom : **`marphar`**
3. Cliquez sur **"Create"**

### 2.4 Noter les informations de connexion

Notez ces informations (vous en aurez besoin) :
```
Host: votre_username.mysql.pythonanywhere-services.com
Username: votre_username
Password: [le mot de passe que vous avez défini]
Database: votre_username$marphar
```

---

## ÉTAPE 3️⃣ : UPLOADER VOTRE CODE

### Option A : Via GitHub (RECOMMANDÉ)

#### 3.1 Aller dans l'onglet Consoles

1. Cliquez sur **"Consoles"** dans le menu
2. Cliquez sur **"Bash"** pour ouvrir une nouvelle console

#### 3.2 Cloner votre dépôt

```bash
cd ~
git clone https://github.com/votre-username/Marco-Pharma.git
cd Marco-Pharma
```

### Option B : Upload manuel via Files

#### 3.1 Créer le dossier

1. Allez dans l'onglet **"Files"**
2. Créez un dossier nommé **`Marco-Pharma`** dans `/home/votre_username/`

#### 3.2 Uploader les fichiers

1. Naviguez dans le dossier `Marco-Pharma`
2. Utilisez le bouton **"Upload a file"** pour chaque fichier
3. Uploadez TOUS les fichiers et dossiers de votre projet

⚠️ **Important** : Assurez-vous d'uploader :
- Le dossier `app/` avec tous ses sous-dossiers
- `run.py`
- `requirements.txt`
- `runtime.txt`
- Tous les autres fichiers nécessaires

---

## ÉTAPE 4️⃣ : CRÉER UN ENVIRONNEMENT VIRTUEL

### 4.1 Ouvrir une console Bash

1. Onglet **"Consoles"** → **"Bash"**

### 4.2 Créer l'environnement virtuel

```bash
cd ~/Marco-Pharma
mkvirtualenv --python=/usr/bin/python3.11 marco-pharma-env
```

### 4.3 Activer l'environnement (si nécessaire)

```bash
workon marco-pharma-env
```

### 4.4 Installer les dépendances

```bash
pip install -r requirements.txt
```

⏱️ **Patience** : L'installation peut prendre 3-5 minutes.

---

## ÉTAPE 5️⃣ : CONFIGURER LES VARIABLES D'ENVIRONNEMENT

### 5.1 Créer le fichier .env

```bash
nano .env
```

### 5.2 Ajouter les variables

```env
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire-123456789
DATABASE_URL=mysql+pymysql://votre_username:votre_mot_de_passe@votre_username.mysql.pythonanywhere-services.com/votre_username$marphar
FLASK_ENV=production
```

**⚠️ IMPORTANT** : 
- Remplacez `votre_username` par votre nom d'utilisateur PythonAnywhere
- Remplacez `votre_mot_de_passe` par le mot de passe MySQL que vous avez défini
- Générez une clé secrète forte pour `SECRET_KEY`

### 5.3 Sauvegarder et quitter

1. Appuyez sur **Ctrl + X**
2. Appuyez sur **Y** (oui)
3. Appuyez sur **Entrée**

---

## ÉTAPE 6️⃣ : INITIALISER LA BASE DE DONNÉES

### 6.1 Vérifier la connexion

```bash
workon marco-pharma-env
cd ~/Marco-Pharma
python3
```

Dans l'interpréteur Python :

```python
from app import create_app
from app.models import db

app = create_app()
with app.app_context():
    db.create_all()
    print("Base de données initialisée avec succès!")

exit()
```

✅ Si vous voyez "Base de données initialisée avec succès!", c'est bon !

---

## ÉTAPE 7️⃣ : CRÉER UNE WEB APP

### 7.1 Accéder à Web

1. Cliquez sur l'onglet **"Web"** dans le menu principal
2. Cliquez sur **"Add a new web app"**

### 7.2 Configuration de la Web App

#### Écran 1 : Nom de domaine
- Cliquez sur **"Next"** (utilise votre sous-domaine gratuit : `votre_username.pythonanywhere.com`)

#### Écran 2 : Framework
- Sélectionnez **"Manual configuration"**
- Cliquez sur **"Next"**

#### Écran 3 : Version Python
- Sélectionnez **"Python 3.11"**
- Cliquez sur **"Next"**

✅ Votre Web App est créée !

---

## ÉTAPE 8️⃣ : CONFIGURER LE FICHIER WSGI

### 8.1 Localiser le fichier WSGI

Sur la page Web, trouvez la section **"Code"**
Cliquez sur le lien du fichier WSGI (exemple : `/var/www/votre_username_pythonanywhere_com_wsgi.py`)

### 8.2 Remplacer le contenu

Supprimez TOUT le contenu et remplacez-le par :

```python
import sys
import os
from dotenv import load_dotenv

# Ajouter le chemin de votre projet
path = '/home/votre_username/Marco-Pharma'
if path not in sys.path:
    sys.path.insert(0, path)

# Charger les variables d'environnement
load_dotenv(os.path.join(path, '.env'))

# Activer l'environnement virtuel
activate_this = '/home/votre_username/.virtualenvs/marco-pharma-env/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Importer l'application Flask
from run import app as application
```

**⚠️ IMPORTANT** : Remplacez `votre_username` par votre nom d'utilisateur PythonAnywhere (3 fois dans le code)

### 8.3 Sauvegarder

Cliquez sur le bouton **"Save"** en haut de la page

---

## ÉTAPE 9️⃣ : CONFIGURER LE VIRTUALENV

### 9.1 Dans la section "Virtualenv"

1. Trouvez la section **"Virtualenv"** sur la page Web
2. Dans le champ **"Enter path to a virtualenv"**, entrez :
   ```
   /home/votre_username/.virtualenvs/marco-pharma-env
   ```
3. Cliquez sur le bouton bleu ✓ pour valider

---

## ÉTAPE 🔟 : CONFIGURER LES FICHIERS STATIQUES

### 10.1 Ajouter les fichiers statiques

Dans la section **"Static files"**, ajoutez :

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/votre_username/Marco-Pharma/app/static` |

1. Entrez `/static/` dans le champ URL
2. Entrez `/home/votre_username/Marco-Pharma/app/static` dans le champ Directory
3. Cliquez sur le ✓ pour valider

---

## ÉTAPE 1️⃣1️⃣ : INSTALLER PYTHON-DOTENV

### 11.1 Ouvrir une console Bash

```bash
workon marco-pharma-env
pip install python-dotenv
```

---

## ÉTAPE 1️⃣2️⃣ : RECHARGER L'APPLICATION

### 12.1 Sur la page Web

1. Faites défiler vers le haut
2. Trouvez le gros bouton vert **"Reload votre_username.pythonanywhere.com"**
3. Cliquez dessus

⏱️ Attendez quelques secondes...

---

## ÉTAPE 1️⃣3️⃣ : TESTER L'APPLICATION

### 13.1 Accéder à votre site

1. Cliquez sur le lien de votre application : **`https://votre_username.pythonanywhere.com`**
2. Vous devriez voir la page de connexion de Marco-Pharma !

### 13.2 Se connecter

Utilisez les identifiants par défaut :
- **Username** : `admin`
- **Password** : `admin123`

✅ **FÉLICITATIONS !** Votre application est en ligne ! 🎉

---

## 🔧 DÉPANNAGE

### Problème : Erreur 500

1. Allez dans l'onglet **"Web"**
2. Consultez les **"Error log"** et **"Server log"**
3. Lisez les erreurs pour identifier le problème

### Problème : ImportError

```bash
workon marco-pharma-env
pip install --upgrade -r requirements.txt
```

Puis rechargez l'application.

### Problème : Base de données non trouvée

Vérifiez le fichier `.env` :
- Le nom d'utilisateur est correct
- Le mot de passe est correct
- Le nom de la base inclut bien le préfixe `votre_username$`

### Problème : Fichiers statiques ne chargent pas

Vérifiez dans **"Static files"** que le chemin est correct :
```
/home/votre_username/Marco-Pharma/app/static
```

---

## 📊 MAINTENANCE

### Mettre à jour le code

```bash
cd ~/Marco-Pharma
git pull origin main  # Si vous utilisez Git
# OU uploadez manuellement les nouveaux fichiers
```

Puis rechargez l'application via le bouton **"Reload"** dans l'onglet Web.

### Mettre à jour les dépendances

```bash
workon marco-pharma-env
pip install --upgrade -r requirements.txt
```

### Consulter les logs

1. Onglet **"Web"**
2. Cliquez sur **"Error log"** ou **"Server log"**

---

## 🔐 SÉCURITÉ

### ⚠️ ACTIONS IMPORTANTES APRÈS DÉPLOIEMENT

1. **Changez le mot de passe admin** immédiatement après la première connexion
2. **Utilisez une SECRET_KEY forte** (pas celle par défaut)
3. **Ne partagez JAMAIS** votre fichier `.env`
4. **Activez HTTPS** (PythonAnywhere l'active par défaut)

---

## 📞 SUPPORT

- **Documentation PythonAnywhere** : https://help.pythonanywhere.com/
- **Forum** : https://www.pythonanywhere.com/forums/

---

## ✅ CHECKLIST FINALE

- [ ] Base de données MySQL créée
- [ ] Code uploadé sur PythonAnywhere
- [ ] Environnement virtuel créé
- [ ] Dépendances installées
- [ ] Fichier .env configuré
- [ ] Base de données initialisée
- [ ] Web App créée
- [ ] Fichier WSGI configuré
- [ ] Virtualenv configuré
- [ ] Fichiers statiques configurés
- [ ] Application rechargée
- [ ] Site accessible et fonctionnel
- [ ] Connexion admin testée
- [ ] Mot de passe admin changé

---

**BON DÉPLOIEMENT ! 🚀**

