"""
Agente Orquestador Central (Hub-and-Spoke).
Cada especialista se expone como una tool (función @tool) que internamente
invoca a su propio Agent con contexto aislado. El orquestador nunca ve el
historial/tools internas de cada especialista, solo el resultado final.

El orquestador usa SlidingWindowConversationManager para mantener historial
de la sesión actual (memoria de corto plazo entre tickets consecutivos),
mientras que cada sub-agente especialista se instancia "fresco" por llamada,
demostrando el aislamiento de contexto del patrón Agents-as-Tools.
"""
from strands import Agent, tool
from strands.agent.conversation_manager import SlidingWindowConversationManager

from src.agents.billing_agent import create_billing_agent
from src.agents.technical_agent import create_technical_agent
from src.agents.security_agent import create_security_agent
from src.hooks.security_verification_hook import SecurityVerificationHook


@tool
def billing_agent(query: str) -> str:
    """Delega en el especialista de facturación: consulta estado de facturas,
    procesa solicitudes de reembolso, resuelve dudas de pagos y cobros."""
    # Se crea una instancia fresca → contexto completamente aislado del orquestador
    print("[ORCHESTRATOR] Instanciando BillingAgent con contexto aislado...")
    agent = create_billing_agent(model=_MODEL)
    return str(agent(query))


@tool
def technical_agent(query: str) -> str:
    """Delega en el especialista técnico: diagnostica estado de servicios
    (email, vpn, crm, database) y restablece contraseñas de usuarios."""
    # Se crea una instancia fresca → contexto completamente aislado del orquestador
    print("[ORCHESTRATOR] Instanciando TechnicalAgent con contexto aislado...")
    agent = create_technical_agent(model=_MODEL)
    return str(agent(query))


@tool
def security_agent(query: str) -> str:
    """Delega en el especialista de seguridad: audita direcciones IP
    sospechosas y revoca tokens/sesiones de usuarios comprometidos.
    Las tools del agente están protegidas por SecurityVerificationHook,
    que fuerza el orden: audit_ip_address → revoke_access_token."""
    # Se crea una instancia fresca → contexto completamente aislado del orquestador
    print("[ORCHESTRATOR] Instanciando SecurityAgent con contexto aislado...")
    agent = create_security_agent(model=_MODEL)
    return str(agent(query))


def create_orchestrator_agent(model=None) -> Agent:
    # Se guarda en módulo para que las tools @tool (sin acceso a closures de
    # función) puedan instanciar cada especialista con el mismo modelo.
    global _MODEL
    _MODEL = model

    # SlidingWindowConversationManager: el orquestador recuerda los últimos
    # 10 mensajes de la sesión (memoria entre tickets consecutivos).
    # Los sub-agentes especialistas NO tienen este manager → son stateless.
    conv_manager = SlidingWindowConversationManager(window_size=10)

    return Agent(
        name="ITSupportOrchestrator",
        description="Orquestador central de soporte técnico de TI.",
        system_prompt=(
            "Eres el agente orquestador principal de soporte TI. "
            "Tu responsabilidad es clasificar los tickets entrantes de los usuarios "
            "y delegar su resolución llamando a la tool del especialista correspondiente "
            "(billing_agent, technical_agent o security_agent) según el tema del ticket. "
            "No respondas tú mismo el contenido técnico: delega siempre. "
            "Sintetiza la respuesta del especialista y proporciónala al usuario de forma clara."
        ),
        tools=[billing_agent, technical_agent, security_agent],
        hooks=[SecurityVerificationHook()],  # guardrail de dominio: enforce audit → revoke
        conversation_manager=conv_manager,   # memoria de sesión del orquestador
        model=model,
    )