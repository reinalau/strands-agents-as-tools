"""
Pruebas unitarias para verificar la inicialización de herramientas y agentes.
"""
import pytest
from src.tools.billing_tools import check_invoice_status
from src.tools.technical_tools import check_system_status
from src.tools.security_tools import audit_ip_address

def test_billing_tools():
    result = check_invoice_status("INV-1001")
    assert "Pagada" in result

def test_technical_tools():
    result = check_system_status("email")
    assert "Operativo" in result

def test_security_tools():
    result = audit_ip_address("192.168.1.100")
    assert "ALERTA DE SEGURIDAD" in result
