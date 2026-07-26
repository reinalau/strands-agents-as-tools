"""
Evaluaciones del patrón Agents-as-Tools: versión original basada únicamente
en evaluación por Salida (Output/Keywords).

Copia de respaldo (backup).
"""
from strands_evals.types.evaluation import EvaluationOutput
from strands.models.ollama import OllamaModel

from evals.eval_cases import EVAL_CASES
from src.config import OLLAMA_HOST, MODEL_NAME
from src.agents.orchestrator import create_orchestrator_agent


def check_expected_keywords(expected_keywords: list[str], actual: str) -> EvaluationOutput:
    actual_lower = (actual or "").lower()
    missing = [kw for kw in expected_keywords if kw.lower() not in actual_lower]
    passed = len(missing) == 0
    reason = f"Se esperaban las palabras clave {expected_keywords}. " + (
        "Todas encontradas." if passed else f"Faltaron: {missing}."
    )
    return EvaluationOutput(
        score=1.0 if passed else 0.0,
        test_pass=passed,
        reason=reason,
    )


def main():
    print("=== Ejecutando Evaluaciones del Patrón Agents-as-Tools (Sólo Output) ===")
    print(f"Modelo: {MODEL_NAME} en {OLLAMA_HOST}\n")

    results = []
    for case in EVAL_CASES:
        print(f"[DEBUG] Iniciando caso: {case.name}", flush=True)
        model = OllamaModel(model_id=MODEL_NAME, host=OLLAMA_HOST)
        orchestrator = create_orchestrator_agent(model=model)
        actual_output = str(orchestrator(case.input_query))
        print(f"[DEBUG] Caso {case.name} completado, len={len(actual_output)}", flush=True)

        eval_result = check_expected_keywords(case.expected_keywords, actual_output)
        status = "[PASS]" if eval_result.test_pass else "[FAIL]"
        print(f"  {status} - {eval_result.reason}\n")
        results.append((case.name, eval_result.test_pass))

    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n=== Resultado: {passed}/{total} casos aprobados ===")
    return results


if __name__ == "__main__":
    main()
