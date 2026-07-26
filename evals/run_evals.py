"""
Evaluaciones del patrón Agents-as-Tools: combinación de Evaluación por Trayectoria 
(Tool-Call Trajectory) y Evaluación por Salida (Output / Keywords).
"""
from strands_evals.types.evaluation import EvaluationOutput
from strands.models.ollama import OllamaModel

from evals.eval_cases import EVAL_CASES
from src.config import OLLAMA_HOST, MODEL_NAME
from src.agents.orchestrator import create_orchestrator_agent


def extract_called_tools(orchestrator_agent) -> list[str]:
    """Extrae la lista de herramientas/sub-agentes llamados durante la ejecución."""
    called_tools = []
    messages = getattr(orchestrator_agent, "messages", [])
    for msg in messages:
        content = getattr(msg, "content", None)
        if content is None and isinstance(msg, dict):
            content = msg.get("content", [])

        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if "toolUse" in block and isinstance(block["toolUse"], dict):
                        name = block["toolUse"].get("name")
                        if name:
                            called_tools.append(name)
                    elif "name" in block and block.get("name"):
                        called_tools.append(str(block["name"]))
                elif hasattr(block, "name") and block.name:
                    called_tools.append(str(block.name))
        elif isinstance(msg, dict) and "tool_calls" in msg:
            for tc in msg.get("tool_calls", []):
                name = tc.get("name") or (tc.get("function", {}).get("name") if isinstance(tc.get("function"), dict) else "")
                if name:
                    called_tools.append(name)
    return [t for t in called_tools if t]


def evaluate_trajectory(expected_agent: str, called_tools: list[str]) -> EvaluationOutput:
    """Evalúa si el orquestador delegó la tarea al sub-agente/tool esperado."""
    expected_clean = expected_agent.lower().replace("agent", "").strip()
    called_clean = [t.lower().replace("agent", "").strip() for t in called_tools]

    passed = any(expected_clean in t or t in expected_clean for t in called_clean)
    reason = (
        f"Sub-agente '{expected_agent}' invocado correctamente. Herramientas ejecutadas: {called_tools}."
        if passed
        else f"Se esperaba invocar '{expected_agent}', pero se invocó: {called_tools if called_tools else 'Ninguna herramienta'}."
    )
    return EvaluationOutput(
        score=1.0 if passed else 0.0,
        test_pass=passed,
        reason=reason,
    )


def evaluate_output_keywords(expected_keywords: list[str], actual: str) -> EvaluationOutput:
    """Evalúa si el texto de salida contiene todas las palabras clave esperadas."""
    actual_lower = (actual or "").lower()
    missing = [kw for kw in expected_keywords if kw.lower() not in actual_lower]
    passed = len(missing) == 0
    reason = f"Palabras clave {expected_keywords}. " + (
        "Todas encontradas." if passed else f"Faltaron: {missing}."
    )
    return EvaluationOutput(
        score=1.0 if passed else 0.0,
        test_pass=passed,
        reason=reason,
    )


def main():
    print("=== Evaluaciones Completa: Trayectoria + Salida (Agents-as-Tools) ===")
    print(f"Modelo: {MODEL_NAME} en {OLLAMA_HOST}\n")

    results = []
    for case in EVAL_CASES:
        print(f"[DEBUG] Evaluando caso: '{case.name}'", flush=True)
        model = OllamaModel(model_id=MODEL_NAME, host=OLLAMA_HOST)
        orchestrator = create_orchestrator_agent(model=model)
        actual_output = str(orchestrator(case.input_query))

        # 1. Evaluación por Trayectoria (Tool-Call)
        called_tools = extract_called_tools(orchestrator)
        traj_eval = evaluate_trajectory(case.expected_agent, called_tools)

        # 2. Evaluación por Salida (Output Keywords)
        out_eval = evaluate_output_keywords(case.expected_keywords, actual_output)

        case_passed = traj_eval.test_pass and out_eval.test_pass
        overall_status = "[PASS]" if case_passed else "[FAIL]"

        print(f"  Resultados del caso '{case.name}': {overall_status}")
        print(f"    |- 1. Trayectoria: {'[PASS]' if traj_eval.test_pass else '[FAIL]'} - {traj_eval.reason}")
        print(f"    +- 2. Output:      {'[PASS]' if out_eval.test_pass else '[FAIL]'} - {out_eval.reason}\n")

        results.append((case.name, case_passed))

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"=== Resultado Global: {passed}/{total} casos totalmente aprobados ===")
    return results


if __name__ == "__main__":
    main()