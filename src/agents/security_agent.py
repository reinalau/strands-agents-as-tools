"""
Agente Especialista en Seguridad de la Información.

El hook SecurityVerificationHook se registra en plugins/hooks para aplicar
steering determinista antes de cada llamada a una tool sensible.
"""
from strands import Agent
from src.tools.security_tools import audit_ip_address, revoke_access_token
from src.hooks.security_verification_hook import SecurityVerificationHook


def create_security_agent(model=None) -> Agent:
    return Agent(
        name="SecurityAgent",
        description=(
            "Agente especializado en análisis de incidentes de seguridad, "
            "auditoría de IPs y revocación de accesos."
        ),
        system_prompt=(
            "Eres un agente de seguridad de la información. "
            "Evalúa riesgos de seguridad, audita direcciones IP y revoca accesos "
            "en casos de posible compromiso. "
            "Actúa con máxima cautela y prioridad de contención."
        ),
        tools=[audit_ip_address, revoke_access_token],
        hooks=[SecurityVerificationHook()],  # SteeringHandler real registrado aquí
        model=model,
    )
