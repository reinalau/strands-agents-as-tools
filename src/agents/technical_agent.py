"""
Agente Especialista en Soporte Técnico.
"""
from strands import Agent
from src.tools.technical_tools import check_system_status, reset_user_password

def create_technical_agent(model=None) -> Agent:
    return Agent(
        name="TechnicalAgent",
        description="Agente especializado en diagnóstico técnico, estado de servicios y reinicio de contraseñas.",
        system_prompt=(
            "Eres un agente especialista en soporte técnico de TI. "
            "Utiliza las herramientas para verificar el estado de los servicios del sistema y restablecer credenciales. "
            "Responde con claridad técnica y recomendaciones concretas."
        ),
        tools=[check_system_status, reset_user_password],
        model=model
    )
