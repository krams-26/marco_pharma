"""
Helper universel pour enregistrer les activités dans le journal d'audit
Permet de capturer automatiquement toutes les actions utilisateur
"""

from flask import request, session
from flask_login import current_user
from app.models import db, Audit
import json
from datetime import datetime


class ActivityLogger:
    """Logger universel pour le journal d'activités"""
    
    @staticmethod
    def log(action, module=None, action_type=None, entity_type=None, entity_id=None, 
            details=None, old_value=None, new_value=None, result='success', user_id=None):
        """
        Enregistrer une activité dans le journal d'audit
        
        Args:
            action: Action effectuée (ex: "create_product", "login", "export_sales")
            module: Module concerné (ex: "products", "sales", "users", "auth")
            action_type: Type d'action (create, update, delete, view, export, login, logout)
            entity_type: Type d'entité concernée (product, sale, user, etc.)
            entity_id: ID de l'entité concernée
            details: Détails textuels de l'action
            old_value: Dict des valeurs AVANT modification (sera converti en JSON)
            new_value: Dict des valeurs APRÈS modification (sera converti en JSON)
            result: Résultat (success, failed, denied)
            user_id: ID utilisateur (si None, utilise current_user)
        
        Returns:
            L'objet Audit créé ou None si erreur
        """
        try:
            # Récupérer l'utilisateur
            if user_id is None:
                if current_user and current_user.is_authenticated:
                    user_id = current_user.id
                else:
                    user_id = None
            
            # Récupérer les informations de la requête
            ip_address = ActivityLogger._get_ip_address()
            user_agent = ActivityLogger._get_user_agent()
            session_id = ActivityLogger._get_session_id()
            
            # Convertir les valeurs en JSON si nécessaire
            old_value_json = None
            if old_value:
                old_value_json = json.dumps(old_value, default=str, ensure_ascii=False)
            
            new_value_json = None
            if new_value:
                new_value_json = json.dumps(new_value, default=str, ensure_ascii=False)
            
            # Créer l'audit
            audit = Audit(
                user_id=user_id,
                action=action,
                module=module,
                action_type=action_type,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                old_value=old_value_json,
                new_value=new_value_json,
                result=result,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id
            )
            
            db.session.add(audit)
            db.session.commit()
            
            return audit
            
        except Exception as e:
            # Ne pas bloquer l'application si le logging échoue
            print(f"Erreur logging activité: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
            return None
    
    @staticmethod
    def log_create(module, entity_type, entity_id, entity_name, details=None, new_value=None):
        """Helper pour enregistrer une création"""
        return ActivityLogger.log(
            action=f"create_{entity_type}",
            module=module,
            action_type='create',
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or f"{entity_type.capitalize()} créé: {entity_name}",
            new_value=new_value
        )
    
    @staticmethod
    def log_update(module, entity_type, entity_id, entity_name, old_value=None, new_value=None, details=None):
        """Helper pour enregistrer une modification"""
        return ActivityLogger.log(
            action=f"update_{entity_type}",
            module=module,
            action_type='update',
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or f"{entity_type.capitalize()} modifié: {entity_name}",
            old_value=old_value,
            new_value=new_value
        )
    
    @staticmethod
    def log_delete(module, entity_type, entity_id, entity_name, details=None, old_value=None):
        """Helper pour enregistrer une suppression"""
        return ActivityLogger.log(
            action=f"delete_{entity_type}",
            module=module,
            action_type='delete',
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or f"{entity_type.capitalize()} supprimé: {entity_name}",
            old_value=old_value
        )
    
    @staticmethod
    def log_view(module, entity_type=None, entity_id=None, page_name=None):
        """Helper pour enregistrer une consultation de page"""
        details = f"Consultation page: {page_name or module}"
        if entity_id:
            details += f" (ID: {entity_id})"
        
        return ActivityLogger.log(
            action=f"view_{module}",
            module=module,
            action_type='view',
            entity_type=entity_type,
            entity_id=entity_id,
            details=details
        )
    
    @staticmethod
    def log_export(module, format_type, count=None, filters=None):
        """Helper pour enregistrer un export"""
        details = f"Export {format_type.upper()}"
        if count:
            details += f" ({count} enregistrements)"
        if filters:
            details += f" - Filtres: {filters}"
        
        return ActivityLogger.log(
            action=f"export_{module}",
            module=module,
            action_type='export',
            details=details,
            new_value={'format': format_type, 'count': count, 'filters': filters}
        )
    
    @staticmethod
    def log_login(user_id, username, result='success', details=None):
        """Helper pour enregistrer une tentative de connexion"""
        if result == 'success':
            details = details or f"Connexion réussie: {username}"
        else:
            details = details or f"Échec de connexion: {username}"
        
        return ActivityLogger.log(
            action='login',
            module='auth',
            action_type='login',
            entity_type='user',
            entity_id=user_id,
            details=details,
            result=result,
            user_id=user_id
        )
    
    @staticmethod
    def log_logout(user_id, username):
        """Helper pour enregistrer une déconnexion"""
        return ActivityLogger.log(
            action='logout',
            module='auth',
            action_type='logout',
            entity_type='user',
            entity_id=user_id,
            details=f"Déconnexion: {username}",
            user_id=user_id
        )
    
    @staticmethod
    def log_access_denied(module, resource, reason=None):
        """Helper pour enregistrer un accès refusé"""
        details = f"Accès refusé: {resource}"
        if reason:
            details += f" - Raison: {reason}"
        
        return ActivityLogger.log(
            action='access_denied',
            module=module,
            action_type='view',
            details=details,
            result='denied'
        )
    
    @staticmethod
    def log_validation(module, entity_type, entity_id, action_taken, decision):
        """Helper pour enregistrer une validation/approbation"""
        return ActivityLogger.log(
            action=f"validate_{entity_type}",
            module=module,
            action_type='update',
            entity_type=entity_type,
            entity_id=entity_id,
            details=f"Validation {entity_type}: {action_taken} - Décision: {decision}",
            new_value={'action': action_taken, 'decision': decision}
        )
    
    @staticmethod
    def _get_ip_address():
        """Récupérer l'adresse IP du client"""
        try:
            # Gérer les proxies
            if request.environ.get('HTTP_X_FORWARDED_FOR'):
                return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
            elif request.environ.get('HTTP_X_REAL_IP'):
                return request.environ['HTTP_X_REAL_IP']
            else:
                return request.environ.get('REMOTE_ADDR')
        except:
            return None
    
    @staticmethod
    def _get_user_agent():
        """Récupérer le user agent (navigateur/OS)"""
        try:
            return request.headers.get('User-Agent', '')[:255]
        except:
            return None
    
    @staticmethod
    def _get_session_id():
        """Récupérer l'ID de session"""
        try:
            return session.get('_id', '')[:100] if session else None
        except:
            return None
    
    @staticmethod
    def capture_before(entity):
        """
        Capturer l'état d'une entité AVANT modification
        Utile pour les updates
        
        Args:
            entity: Objet SQLAlchemy à capturer
        
        Returns:
            Dict avec les valeurs actuelles
        """
        if not entity:
            return {}
        
        try:
            # Récupérer toutes les colonnes
            mapper = entity.__mapper__
            data = {}
            
            for column in mapper.columns:
                # Ignorer les champs sensibles
                if column.name in ['password_hash', 'password']:
                    continue
                
                value = getattr(entity, column.name, None)
                
                # Convertir les dates en string
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                
                data[column.name] = value
            
            return data
        except Exception as e:
            print(f"Erreur capture_before: {str(e)}")
            return {}
    
    @staticmethod
    def capture_after(entity):
        """
        Capturer l'état d'une entité APRÈS modification
        Identique à capture_before mais pour clarté du code
        """
        return ActivityLogger.capture_before(entity)


# Alias pour compatibilité
log_activity = ActivityLogger.log
log_create = ActivityLogger.log_create
log_update = ActivityLogger.log_update
log_delete = ActivityLogger.log_delete
log_view = ActivityLogger.log_view
log_export = ActivityLogger.log_export
log_login = ActivityLogger.log_login
log_logout = ActivityLogger.log_logout
log_access_denied = ActivityLogger.log_access_denied

