# Strands Agents - Patron de Orquestacion Agents As Tools

Este es un ejemplo educativo del patron de orquestacion Agents As Tools del framework Strands Agents. Es un patron jerarquico (hub-and-spoke) donde un orquestador delega tareas a agentes especializados. 
Cuando usar? Sabés de antemano quién hace qué, y querés que un "manager" delegue tareas específicas sin que el ruido de cada especialista contamine el contexto principal.

La idea principal es mostrar como se puede estructurar y testear localmente por medio de Ollama con el pequeño modelo gemma4:e2b-it-qat sin la necesidad de desplegar en AWS.

## Caso de Uso

El caso de uso es la automatización del soporte básico de TI. Se recibe un ticket de soporte y se determina si es un ticket de facturación, técnico o seguridad. Luego se envía a los agentes correspondientes para que lo resuelvan. En este ejemplo se simula esto con un archivo .py que lee los tickets de un archivo .json y los procesa.


## Estructura de carpetas

```
agents-as-tools
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── billing_agent.py
│   │   ├── technical_agent.py
│   │   └── security_agent.py
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── billing_tools.py
│   │   ├── technical_tools.py
│   │   └── security_tools.py
│   │
│   └── hooks/
│       ├── __init__.py
│       └── security_verification_hook.py   # SteeringHandler de dominio
│
├── examples/
│   └── sample_tickets.py
│
├── evals/
│   ├── __init__.py
│   ├── eval_cases.py                 # Casos con inputs, agent esperado y keywords
│   └── run_evals.py                  # Evaluador dual: Trayectoria (Tool Call) + Output (Keywords)
│
└── tests/
    └── test_agents.py                # Tests unitarios de tools (sin LLM)
```

---

## Cómo funciona

### Patrón Agents-as-Tools en Strands

El patrón **Agents-as-Tools** (hub-and-spoke) consiste en exponer agentes especializados como herramientas (`@tool`) que el agente orquestador puede invocar. Cada agente especialista vive en su propio contexto aislado: el orquestador nunca accede al historial interno ni a las tools del especialista, solo recibe el resultado final como string.

En Strands esto se implementa con dos primitivas del framework:

```python
# 1. Cada especialista es un Agent con tools y system_prompt propios
specialist = Agent(tools=[...], system_prompt="...")

# 2. Se expone al orquestador como una función @tool normal
@tool
def billing_agent(query: str) -> str:
    agent = create_billing_agent(model=_MODEL)  # instancia fresca = contexto aislado
    return str(agent(query))

# 3. El orquestador recibe las tools-agente igual que cualquier otra tool
orchestrator = Agent(tools=[billing_agent, technical_agent, security_agent])
```

### Aislamiento de contexto (por qué importa)

Cada vez que el orquestador llama a una tool-agente, se instancia un `Agent` nuevo con historial vacío. Esto garantiza que:

- Las tools del BillingAgent **nunca son visibles** para el TechnicalAgent o el SecurityAgent.
- El contexto del orquestador no se contamina con el razonamiento interno del especialista.
- Cada especialista responde solo con información relevante a su dominio.

Los logs en runtime lo hacen visible:

```
[ORCHESTRATOR] Instanciando SecurityAgent con contexto aislado...
[SECURITY HOOK] Nueva invocación — se requiere audit_ip_address antes de revocar accesos.
```

### Memoria del orquestador (ConversationManager)

El orquestador usa `SlidingWindowConversationManager(window_size=10)` para retener los últimos 10 mensajes de la sesión, lo que le permite mantener coherencia entre tickets consecutivos (por ejemplo, saber que el usuario anterior ya reportó la misma IP). --> Mantiene los mensajes en una lista dentro del objeto Python en RAM durante la ejecución del proceso

Los sub-agentes especialistas **no** tienen conversation manager propio: son stateless por diseño, consistente con el aislamiento del patrón.

```python
conv_manager = SlidingWindowConversationManager(window_size=10)
orchestrator = Agent(..., conversation_manager=conv_manager)
```

### Hook de dominio (SteeringHandler)

`SecurityVerificationHook` implementa `HookProvider` de Strands y fuerza el orden de pasos del protocolo de respuesta ante incidentes de seguridad:

**audit_ip_address → revoke_access_token** (en ese orden, siempre)

Si el LLM intenta llamar a `revoke_access_token` sin haber auditado primero la IP, el hook lo bloquea con `event.cancel_tool` antes de que la función se ejecute. Esto demuestra el uso del framework para imponer lógica de negocio determinista, sin depender del criterio del modelo.

Los tres eventos que usa:

| Evento | Rol |
|---|---|
| `BeforeInvocationEvent` | Reinicia `_audit_done = False` al inicio de cada invocación |
| `AfterToolInvocationEvent` | Marca `_audit_done = True` cuando `audit_ip_address` termina |
| `BeforeToolCallEvent` | Bloquea `revoke_access_token` si `_audit_done` es `False` |

### Evaluaciones (evals/ vs tests/)

| Directorio | Qué evalúa | Cómo |
|---|---|---|
| `tests/` | Que las tools retornan el formato correcto | `pytest` + asserts directos, sin LLM |
| `evals/` | Que el orquestador clasifica y delega correctamente | Llama al agente real y realiza evaluación dual: Trayectoria de llamadas (Tool-Call) + Palabras clave en Output |

---

### Puntos clave de esta estructura segun lo que nos ofrece Strands Agents:

* `config.py`: centraliza `OllamaModel(host="http://localhost:11434", model_id="gemma4:e2b-it-qat")` — un solo lugar para cambiar el modelo.
* Cada `*_agent.py` en `agents/` es un `Agent` independiente con su propio `system_prompt` + tools acotadas a su dominio.
* `orchestrator.py` es el único que conoce a los 3 especialistas, envueltos con `@tool`, y decide a quién delegar según el ticket.
* `tools/` separado de `agents/`: cada archivo de tools queda acotado a su dominio y es reutilizable sin importar el agente.
* Tools con datos mock (no APIs reales) para que el repo sea reproducible por cualquiera sin credenciales.

### Notas:

* `hooks/security_verification_hook.py` → `HookProvider` real con lógica de dominio, no solo detección de strings peligrosos.
* `evals/` separado de `tests/` porque conceptualmente son distintos: `tests/` = unit tests clásicos, `evals/` = evaluación de comportamiento del agente con `Contains`.
* `requirements.txt` incluye `strands-agents-evals` además de `strands-agents`.

---

## Ejecución Local

### 1. Requisitos Previos e Instalación

1. Tener Docker Desktop instalado y corriendo.

2. Levantar el servidor de Ollama con un volumen persistente (para que el modelo no se vuelva a descargar si el contenedor se recrea):

   ```bash
   docker run -d --name ollama -p 11434:11434 -v ollama_data:/root/.ollama ollama/ollama
   ```

3. Descargar el modelo (solo la primera vez; con el volumen montado, quedará guardado):

   ```bash
   docker exec -it ollama ollama pull gemma4:e2b-it-qat
   ```

4. Probar que el modelo responde:

   ```bash
   docker exec -it ollama ollama run gemma4:e2b-it-qat
   ```
Interactuar con el modelo diciendo al menos "hola" y verificar si contesta. La manera de salir es presionar Ctrl + d o /bye

5. Verificar que el modelo está corriendo:

   ```bash
   docker exec -it ollama ollama ps
   ```

6. Entorno Virtual 
```bash
pip install -r requirements.txt
```

7. Variables de Entorno 
```bash
cp .env.example .env
```

### 2. Pruebas Unitarias (`tests/`)
Es el primer filtro recomendado porque no requiere Ollama ni LLM activo; valida rápidamente en milisegundos que el entorno Python y las @tool deterministas funcionen correctamente.

```bash
pytest tests/
```
O

```bash
python -m pytest tests/
```

### 3. Ejecución Real (`src/main.py`)
El flujo principal demostrativo donde se ejecuta el script interactivo y se ve al orquestador delegar tickets a los especialistas procesados por Ollama.

```bash
python -m src.main
```
Puede ser algo lento debido al modelo de ollama elegido pero finalmente termina el flujo con los ejemplos de tickets.
En mis pruebas se vio algo como esto:

```plaintext

=== Iniciando Sistema de Soporte TI (Strands Agents - Agents as Tools) ===
Conectando a Ollama (http://localhost:11434) usando modelo: gemma4:e2b-it-qat...

--------------------------------------------------
Ticket ID: TCK-101 | Categoría: Facturación
Usuario: ana.garcia@empresa.com
Consulta: ¿Cuál es el estado de la factura INV-1001 y cuándo se acreditó el pago?
--------------------------------------------------
[SECURITY HOOK] Nueva invocación — se requiere audit_ip_address antes de revocar accesos.

Tool #1: billing_agent
[ORCHESTRATOR] Instanciando BillingAgent con contexto aislado...

Tool #1: check_invoice_status
La factura **INV-1001** tiene un estado **Pagado**.

Detalles:
*   **Monto:** $150.00
*   **Fecha de pago:** 2026-07-01

Respecto al acreditamiento del pago para ana.garcia@empresa.com, como agente de soporte, puedo consultar el estado de facturas y procesar solicitudes de reembolso, pero no tengo la capacidad directa de realizar transferencias o 
gestionar el proceso de acreditación bancaria de pagos. Para esa gestión, le sugiero contactar directamente a nuestro departamento de cuentas o finanzas indicando esta información.

¿Necesita ayuda con alguna otra consulta sobre esta factura, como un proceso de devolución (reembolso)?Hola ana.garcia@empresa.com,

He procesado tu solicitud (Ticket TCK-101) sobre la factura INV-1001. El especialista de facturación ha confirmado lo siguiente:

**Estado de la Factura INV-1001:**
*   **Estado:** Pagado
*   **Monto:** $150.00
*   **Fecha de Pago:** 2026-07-01

Respecto a tu pregunta sobre la acreditación del pago, como agente orquestador, puedo consultar el estado financiero de las facturas; sin embargo, no tengo acceso directo para gestionar transferencias o procesos bancarios de acreditación. Para esa gestión específica, por favor contacta directamente con nuestro departamento de cuentas o finanzas proporcionándoles esta información.

¿Te gustaría que te ayude con alguna otra consulta relacionada con la facturación?
Respuesta del Orquestador:
Hola ana.garcia@empresa.com,

He procesado tu solicitud (Ticket TCK-101) sobre la factura INV-1001. El especialista de facturación ha confirmado lo siguiente:

**Estado de la Factura INV-1001:**
*   **Estado:** Pagado
*   **Monto:** $150.00
*   **Fecha de Pago:** 2026-07-01

Respecto a tu pregunta sobre la acreditación del pago, como agente orquestador, puedo consultar el estado financiero de las facturas; sin embargo, no tengo acceso directo para gestionar transferencias o procesos bancarios de acreditación. Para esa gestión específica, por favor contacta directamente con nuestro departamento de cuentas o finanzas proporcionándoles esta información.
--------------------------------------------------
Ticket ID: TCK-102 | Categoría: Técnico
Usuario: carlos.lopez@empresa.com
Consulta: No puedo conectarme a la VPN corporativa desde esta mañana. ¿El servicio está caído?
--------------------------------------------------
[SECURITY HOOK] Nueva invocación — se requiere audit_ip_address antes de revocar accesos.

Tool #2: technical_agent
[ORCHESTRATOR] Instanciando TechnicalAgent con contexto aislado...

[SECURITY HOOK] Nueva invocación — se requiere audit_ip_address antes de revocar accesos.

Tool #2: technical_agent
[ORCHESTRATOR] Instanciando TechnicalAgent con contexto aislado...

Tool #1: check_system_status
Entiendo que estás experimentando un problema de conexión para la VPN corporativa con tu usuario `carlos.lopez@empresa.com`. El primer intento de verificación del estado del servicio no arrojó resultados directos, lo cual puede 
[SECURITY HOOK] Nueva invocación — se requiere audit_ip_address antes de revocar accesos.

Tool #2: technical_agent
[ORCHESTRATOR] Instanciando TechnicalAgent con contexto aislado...

[ORCHESTRATOR] Instanciando TechnicalAgent con contexto aislado...

Tool #1: check_system_status
Entiendo que estás experimentando un problema de conexión para la VPN corporativa con tu usuario `carlos.lopez@empresa.com`. El primer intento de verificación del estado del servicio no arrojó resultados directos, lo cual puede 
indicar que el registro del servicio está fuera de línea o que el problema es de autenticación/configuración específica de usuario.

Para poder ayudarte de manera más efectiva, por favor proporcióneme la siguiente información:

1.  **¿Cuál es el mensaje de error exacto** que aparece al intentar conectarse a la VPN?
2.  **¿Has verificado las credenciales (usuario y contraseña)** para asegurar que son correctas?

Mientras tanto, podemos proceder con una medida de seguridad estándar si se sospecha un problema con las credenciales guardadas: puedo generar un enlace de restablecimiento de contraseña.

Si deseas continuar inmediatamente con el **restablecimiento de la contraseña** para Carlos López, por favor confírmame su dirección de correo electrónico corporativa y procedo a ejecutar la herramienta correspondiente.Hola carlos.lopez@empresa.com, he procesado tu solicitud (Ticket TCK-102) sobre la conexión VPN. El especialista técnico ha revisado el caso y te indica lo siguiente:

El primer intento de verificación no arrojó una caída general del servicio. Esto sugiere que el problema podría estar en la autenticación o en la configuración específica de tu usuario.

**Para poder diagnosticarlo mejor, el especialista requiere dos cosas de tu parte:**
1.  El **mensaje de error exacto** que aparece cuando intentas conectarte a la VPN.
2.  Confirmar que estás utilizando las **credenciales correctas**.

Como medida inmediata y para facilitar la solución, podemos proceder con un restablecimiento de contraseña. Por favor, confírmame tu dirección de correo electrónico corporativa si deseas que proceda a generar ese enlace para que puedas intentar conectarte nuevamente.
Respuesta del Orquestador:
Hola carlos.lopez@empresa.com, he procesado tu solicitud (Ticket TCK-102) sobre la conexión VPN. El especialista técnico ha revisado el caso y te indica lo siguiente:

El primer intento de verificación no arrojó una caída general del servicio. Esto sugiere que el problema podría estar en la autenticación o en la configuración específica de tu usuario.

**Para poder diagnosticarlo mejor, el especialista requiere dos cosas de tu parte:**
1.  El **mensaje de error exacto** que aparece cuando intentas conectarte a la VPN.
2.  Confirmar que estás utilizando las **credenciales correctas**.

Como medida inmediata y para facilitar la solución, podemos proceder con un restablecimiento de contraseña. Por favor, confírmame tu dirección de correo electrónico corporativa si deseas que proceda a generar ese enlace para que puedas intentar conectarte nuevamente.


--------------------------------------------------
Ticket ID: TCK-103 | Categoría: Seguridad
Usuario: maria.rodriguez@empresa.com
Consulta: Detectamos intentos no autorizados de acceso desde la IP 192.168.1.100. Necesito auditar esa IP.        
--------------------------------------------------
[SECURITY HOOK] Nueva invocación — se requiere audit_ip_address antes de revocar accesos.

Tool #3: security_agent
[ORCHESTRATOR] Instanciando SecurityAgent con contexto aislado...
[SECURITY HOOK] Nueva invocación — se requiere audit_ip_address antes de revocar accesos.

Tool #1: audit_ip_address
[SECURITY HOOK] audit_ip_address completada — revocación de accesos habilitada.
**Alerta de Seguridad Confirmada.**

La dirección IP **192.168.1.100** ha sido auditada y se confirma como una amenaza debido a múltiples intentos de acceso fallidos. Esto indica un posible intento de compromiso o escaneo de la red que podría estar enfocado en las 
credenciales asociadas a `maria.rodriguez@empresa.com`.

### Recomendaciones de Contención Inmediata:
1.  **Bloqueo Automático:** Se recomienda aplicar políticas de bloqueo (firewall/WAF) para bloquear temporalmente 
el origen 192.168.1.100 hasta que se identifique su naturaleza.
2.  **Acción sobre Cuentas:** Si existen indicadores de que la cuenta de Maria Rodríguez está siendo utilizada, debe priorizarse la **revocación inmediata de todos los tokens y sesiones activas** para asegurar el acceso restante (utilizando `revoke_access_token` si se proporciona su ID de usuario).
3.  **Investigación Profunda:** Iniciar una revisión forense del sistema afectado por la IP 192.168.1.100 y analizar los logs de autenticación para identificar el punto exacto de vulnerabilidad o movimiento lateral.

Por favor, proporcione el ID de usuario (`user_id`) si desea proceder con la revocación de accesos de Maria Rodríguez.Hola maria.rodriguez@empresa.com, he procesado tu solicitud de soporte (Ticket TCK-103) respecto a los intentos no autorizados de acceso desde la IP 192.168.1.100.

El especialista en seguridad ha confirmado una **alerta de amenaza**. Los registros indican múltiples intentos de 
acceso fallidos que sugieren un posible intento de compromiso o escaneo de la red que podría estar relacionado con tu cuenta.

**Acciones tomadas por el equipo de seguridad:**
*   La dirección IP **192.168.1.100 ha sido auditada y se confirma como una amenaza**.
*   Se recomienda aplicar bloqueos inmediatos para contener la actividad sospechosa.
*   Si me proporcionas tu ID de usuario, podemos proceder a la **revocación inmediata de todos tus tokens y sesiones activas** para asegurar el acceso restante mientras investigamos la fuente del ataque.

Por favor, indícame si deseas que proceda con la revocación de accesos o si necesitas alguna información adicional sobre esta alerta.
Respuesta del Orquestador:
Hola maria.rodriguez@empresa.com, he procesado tu solicitud de soporte (Ticket TCK-103) respecto a los intentos no autorizados de acceso desde la IP 192.168.1.100.

El especialista en seguridad ha confirmado una **alerta de amenaza**. Los registros indican múltiples intentos de 
acceso fallidos que sugieren un posible intento de compromiso o escaneo de la red que podría estar relacionado con tu cuenta.

**Acciones tomadas por el equipo de seguridad:**
*   La dirección IP **192.168.1.100 ha sido auditada y se confirma como una amenaza**.
*   Se recomienda aplicar bloqueos inmediatos para contener la actividad sospechosa.
*   Si me proporcionas tu ID de usuario, podemos proceder a la **revocación inmediata de todos tus tokens y sesiones activas** para asegurar el acceso restante mientras investigamos la fuente del ataque.

Por favor, indícame si deseas que proceda con la revocación de accesos o si necesitas alguna información adicional sobre esta alerta.

```


### 4. Evaluación de Comportamiento (`evals/`)
Pruebas de calidad y precisión ejecutadas sobre el agente real. 

Se recomienda (opcional) establecer `OTEL_SDK_DISABLED=true` en el entorno para desactivar el recolector de telemetría OpenTelemetry en ejecuciones locales sin servidor de trazas:

```bash
export OTEL_SDK_DISABLED="true"
python -m evals.run_evals
```

Este script ejecuta dos metodologías de evaluación según las especificaciones de **Strands Agents**:

* **Evaluación por Trayectoria / Invocación de Herramientas (Tool-Call Trajectory Evaluation):** Valida la traza de razonamiento del orquestador inspeccionando que se haya invocado explícitamente al sub-agente o herramienta correspondiente (`expected_agent`: `billing_agent`, `technical_agent`, `security_agent`).
* **Evaluación por Salida (Output / Keyword Evaluation):** Analiza la respuesta final generada en lenguaje natural para verificar determinísticamente la presencia de las palabras clave de negocio esperadas (`expected_keywords`).


## Referencias

- [Strands Agents — Documentación oficial](https://strandsagents.com/)
- [Strands Agents — Hooks y lifecycle events](https://strandsagents.com/latest/user-guide/concepts/hooks/)
- [Strands Agents — ConversationManager](https://strandsagents.com/latest/user-guide/concepts/conversation-manager/)
- [Strands Agents — Multi-agent patterns](https://strandsagents.com/latest/user-guide/concepts/multi-agent/)
- [Strands Agents — Evals](https://strandsagents.com/docs/user-guide/evals-sdk/evaluators/)
- [Ollama — Modelos locales](https://ollama.com/)

## Licencia 

