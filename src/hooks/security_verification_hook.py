"""
Hook de verificación de seguridad implementado como HookProvider real de Strands Agents.

Aplica steering determinista de dominio:
  - Bloquea revoke_access_token si antes NO se llamó audit_ip_address
    en la misma invocación del agente. Esto fuerza el orden de pasos:
    auditar → revocar, que es el protocolo real de respuesta ante incidentes.

Para registrarlo: pasar hooks=[SecurityVerificationHook()] en Agent(...)
"""

from strands.hooks import (
    HookProvider,
    HookRegistry,
    BeforeInvocationEvent,
    BeforeToolCallEvent,
    AfterToolCallEvent,
)


class SecurityVerificationHook(HookProvider):
    """
    SteeringHandler determinista para el SecurityAgent (y el orquestador).

    Registra callbacks en:
      - BeforeInvocationEvent      → reinicia el estado de auditoría al inicio
                                     de cada invocación nueva.
      - AfterToolCallEvent   → marca que audit_ip_address fue ejecutada.
      - BeforeToolCallEvent        → bloquea revoke_access_token si aún no se
                                     auditó la IP en esta misma invocación.

    Patrón demostrado: forzar orden de pasos determinista desde el framework,
    sin depender de que el LLM lo haga por su cuenta.
    """

    def __init__(self):
        # Estado por invocación: ¿ya se ejecutó audit_ip_address?
        self._audit_done: bool = False

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeInvocationEvent, self._reset_state)
        registry.add_callback(AfterToolCallEvent, self._track_audit)
        registry.add_callback(BeforeToolCallEvent, self._enforce_audit_first)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _reset_state(self, event: BeforeInvocationEvent) -> None:
        """Al inicio de cada invocación, la auditoría vuelve a estar pendiente."""
        self._audit_done = False
        print("[SECURITY HOOK] Nueva invocación — se requiere audit_ip_address antes de revocar accesos.")

    def _track_audit(self, event: AfterToolCallEvent) -> None:
        """Marca que la auditoría de IP ya fue completada en esta invocación."""
        tool_name = event.tool_use.get("name", "") if isinstance(event.tool_use, dict) else getattr(event.tool_use, "name", "")
        if tool_name == "audit_ip_address":
            self._audit_done = True
            print("[SECURITY HOOK] audit_ip_address completada — revocación de accesos habilitada.")

    def _enforce_audit_first(self, event: BeforeToolCallEvent) -> None:
        """
        Bloquea revoke_access_token si no se ejecutó audit_ip_address antes.
        Fuerza el protocolo: auditar → revocar.
        """
        tool_name = event.tool_use.get("name", "") if isinstance(event.tool_use, dict) else getattr(event.tool_use, "name", "")

        if tool_name == "revoke_access_token" and not self._audit_done:
            msg = (
                "[SECURITY HOOK] BLOQUEADO: no se puede revocar accesos sin auditar primero la IP. "
                "Llama a audit_ip_address antes de ejecutar revoke_access_token."
            )
            print(msg)
            event.cancel_tool = msg
