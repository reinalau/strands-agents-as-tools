"""
Herramientas para el Agente de Facturación.
"""
from strands import tool

@tool
def check_invoice_status(invoice_id: str) -> str:
    """Consulta el estado de una factura dado su ID."""
    # Simulación de consulta a base de datos de facturación. Aqui se puede hacer la integracion via api
    mock_db = {
        "INV-1001": "Pagada - Monto: $150.00 - Fecha: 2026-07-01",
        "INV-1002": "Pendiente - Monto: $300.00 - Vence: 2026-08-01",
        "INV-1003": "Rechazada - Error de procesamiento en pasarela",
    }
    return mock_db.get(invoice_id.upper(), f"Factura {invoice_id} no encontrada.")

@tool
def process_refund_request(invoice_id: str, reason: str) -> str:
    """Procesa una solicitud de reembolso para una factura."""
    return f"Solicitud de reembolso enviada con éxito para la factura {invoice_id}. Razón: {reason}"
