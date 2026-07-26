"""
Agente Especialista en Facturación y Pagos.
"""
from strands import Agent
from src.tools.billing_tools import check_invoice_status, process_refund_request

def create_billing_agent(model=None) -> Agent:
    return Agent(
        name="BillingAgent",
        description="Agente especializado en resolver consultas de facturación, estado de facturas y solicitudes de reembolso.",
        system_prompt=(
            "Eres un agente especialista en soporte de facturación. "
            "Utiliza las herramientas disponibles para consultar facturas y procesar reembolsos. "
            "Sé preciso, amable y profesional."
        ),
        tools=[check_invoice_status, process_refund_request],
        model=model
    )
