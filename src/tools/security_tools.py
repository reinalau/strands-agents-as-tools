"""
Herramientas para el Agente de Seguridad.
"""
from strands import tool

@tool
def audit_ip_address(ip_address: str) -> str:
    """Audita una dirección IP en busca de actividad sospechosa o bloqueos."""
    suspicious_ips = ["192.168.1.100", "10.0.0.99", "45.33.32.156"]
    if ip_address in suspicious_ips:
        return f"ALERTA DE SEGURIDAD: La IP {ip_address} está marcada como sospechosa por múltiple intento fallido."
    return f"IP {ip_address} sin reportes de riesgo activos."

@tool
def revoke_access_token(user_id: str) -> str:
    """Revoca inmediatamente todas las sesiones y tokens activos de un usuario."""
    return f"Todos los tokens y sesiones del usuario {user_id} han sido revocados exitosamente."
