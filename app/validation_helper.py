import random
import string
from datetime import datetime, timedelta
from app.models import db, ValidationCode, User, Notification

def generate_validation_code(generated_by, generated_for, reference_type, reference_id, 
                             code_type='status_change', expiry_minutes=30):
    """
    Générer un code de validation unique
    
    Args:
        generated_by: ID de l'utilisateur qui génère le code
        generated_for: ID de l'utilisateur destinataire (admin)
        reference_type: Type d'entité (sale, product, user, etc.)
        reference_id: ID de l'entité
        code_type: Type de code (status_change, delete, archive)
        expiry_minutes: Durée de validité en minutes
    
    Returns:
        ValidationCode object ou None si erreur
    """
    try:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        while ValidationCode.query.filter_by(code=code).first():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
        
        validation_code = ValidationCode(
            code=code,
            type=code_type,
            status='active',
            reference_id=reference_id,
            reference_type=reference_type,
            generated_by=generated_by,
            generated_for=generated_for,
            expires_at=expires_at
        )
        
        db.session.add(validation_code)
        
        admin = User.query.get(generated_for)
        requester = User.query.get(generated_by)
        
        if admin:
            notification = Notification(
                type='code_request',
                title=f'Code de validation demandé',
                message=f'{requester.full_name or requester.username} demande un code de validation pour {reference_type} #{reference_id}',
                requester_id=generated_by,
                target_admin_id=generated_for,
                priority='high',
                reference_type=reference_type,
                reference_id=reference_id
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return validation_code
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur génération code: {e}")
        return None

def validate_code(code, reference_type, reference_id, used_by):
    """
    Valider un code de validation
    
    Args:
        code: Le code à valider
        reference_type: Type d'entité
        reference_id: ID de l'entité
        used_by: ID de l'utilisateur qui utilise le code
    
    Returns:
        True si valide, False sinon
    """
    try:
        validation_code = ValidationCode.query.filter_by(
            code=code,
            reference_type=reference_type,
            reference_id=reference_id,
            status='active',
            is_used=False
        ).first()
        
        if not validation_code:
            return False
        
        if validation_code.is_expired:
            validation_code.status = 'expired'
            db.session.commit()
            return False
        
        validation_code.is_used = True
        validation_code.used_by = used_by
        validation_code.used_at = datetime.utcnow()
        validation_code.status = 'used'
        
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Erreur validation code: {e}")
        return False

def clean_expired_codes():
    """Nettoyer les codes expirés (à appeler périodiquement)"""
    try:
        ValidationCode.query.filter(
            ValidationCode.expires_at < datetime.utcnow(),
            ValidationCode.status == 'active'
        ).update({'status': 'expired'})
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Erreur nettoyage codes: {e}")
        return False

