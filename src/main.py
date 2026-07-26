"""
Punto de entrada principal para procesar tickets de soporte TI usando el patrón Agents-as-Tools.
"""
from strands.models import OllamaModel
from src.config import OLLAMA_HOST, MODEL_NAME
from src.agents.orchestrator import create_orchestrator_agent
from examples.sample_tickets import SAMPLE_TICKETS

def main():
    print("=== Iniciando Sistema de Soporte TI (Strands Agents - Agents as Tools) ===")
    print(f"Conectando a Ollama ({OLLAMA_HOST}) usando modelo: {MODEL_NAME}...\n")

    # Inicializar modelo Ollama local
    ollama_model = OllamaModel(
        model_id=MODEL_NAME,
        host=OLLAMA_HOST
    )

    # Crear orquestador central
    orchestrator = create_orchestrator_agent(model=ollama_model)

    # Procesar tickets de ejemplo
    for ticket in SAMPLE_TICKETS:
        print(f"--------------------------------------------------")
        print(f"Ticket ID: {ticket['id']} | Categoría: {ticket['category']}")
        print(f"Usuario: {ticket['user']}")
        print(f"Consulta: {ticket['query']}")
        print(f"--------------------------------------------------")
        
        response = orchestrator(
            f"Procesa el siguiente ticket de soporte:\n"
            f"ID: {ticket['id']}\n"
            f"Usuario: {ticket['user']}\n"
            f"Detalle: {ticket['query']}"
        )

        print(f"\nRespuesta del Orquestador:\n{response}\n")

if __name__ == "__main__":
    main()
