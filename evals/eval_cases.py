"""
Definición de casos de prueba y evaluación para el orquestador y los especialistas.
"""
from dataclasses import dataclass
from typing import List

@dataclass
class EvalCase:
    name: str
    input_query: str
    expected_keywords: List[str]
    expected_agent: str

EVAL_CASES = [
    EvalCase(
        name="Clasificación y delegación de Facturación",
        input_query="Quiero verificar el estado de la factura INV-1002.",
        expected_keywords=["INV-1002", "Pendiente"],
        expected_agent="BillingAgent"
    ),
    EvalCase(
        name="Clasificación y delegación Técnica",
        input_query="Necesito resetear mi contraseña para el usuario juan.perez@empresa.com.",
        expected_keywords=["restablecimiento", "juan.perez@empresa.com"],
        expected_agent="TechnicalAgent"
    ),
    EvalCase(
        name="Clasificación y delegación de Seguridad",
        input_query="Revocar tokens inmediatamente para el usuario USR-884.",
        expected_keywords=["ip", "USR-884"],
        expected_agent="SecurityAgent"
    )
]
