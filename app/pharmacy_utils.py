from flask_login import current_user

def is_admin():
    """Vérifier si l'utilisateur actuel est admin"""
    return current_user.role == 'admin'

def get_accessible_pharmacies():
    """Obtenir les pharmacies accessibles par l'utilisateur"""
    from app.models import Pharmacy
    
    if is_admin():
        return Pharmacy.query.all()
    else:
        return current_user.get_all_pharmacies()

def get_user_scope():
    """Déterminer le scope d'accès de l'utilisateur"""
    if current_user.role == 'admin':
        return 'all'
    elif current_user.role in ['manager', 'pharmacien']:
        return 'pharmacy'
    else:
        return 'personal'

def filter_by_pharmacy(query, model, pharmacy_filter='all'):
    """Filtrer une requête par pharmacie selon les droits de l'utilisateur"""
    scope = get_user_scope()
    
    # Admin : peut filtrer par pharmacie ou voir toutes
    if scope == 'all':
        if pharmacy_filter != 'all' and pharmacy_filter:
            query = query.filter(model.pharmacy_id == int(pharmacy_filter))
        return query
    
    primary_pharmacy = current_user.get_primary_pharmacy()
    
    # Manager/Pharmacien : voit toute sa pharmacie
    if scope == 'pharmacy' and primary_pharmacy:
        if hasattr(model, 'pharmacy_id'):
            query = query.filter(model.pharmacy_id == primary_pharmacy.id)
        return query
    
    # Autres utilisateurs : voient uniquement leurs données
    if scope == 'personal':
        if hasattr(model, 'user_id'):
            query = query.filter(model.user_id == current_user.id)
        elif hasattr(model, 'pharmacy_id') and primary_pharmacy:
            # Fallback sur la pharmacie si pas de user_id
            query = query.filter(model.pharmacy_id == primary_pharmacy.id)
    
    return query
