"""
Herramientas para el Agente de Soporte Técnico.
"""
from strands import tool

@tool
def check_system_status(service_name: str) -> str:
    """Verifica el estado operativo de un servicio informático."""
    services = {
        "email": "Operativo - Latencia: 12ms",
        "vpn": "Degradado - Alta carga de conexiones",
        "crm": "Operativo - Sin incidencias",
        "database": "Operativo - Backups al día"
    }
    return services.get(service_name.lower(), f"Servicio '{service_name}' no registrado en el monitoreo.")

@tool
def reset_user_password(user_email: str) -> str:
    """Genera un enlace de restablecimiento de contraseña para un usuario."""
    return f"Enlace temporario de restablecimiento enviado a {user_email}."
