# La mesa del impostor

Juego autónomo para cuatro agentes con interfaz web en español. Requiere Python 3.10+; no instala dependencias.

```sh
python3 server.py
```

Abre el puerto 8000 en tu navegador. Pulsa **Comenzar partida**: se asignan tres civiles y un impostor con aleatoriedad del sistema, los agentes dan tres rondas de pistas y votan sin intervención. Si expulsan a un civil, continúan los tres restantes durante otro ciclo. Con dos jugadores vivos gana el impostor. Los empates se resuelven por sorteo anunciado entre los más votados. Los roles se muestran solo al terminar.

El servidor selecciona el motor con `AGENT_BACKEND`:

- `auto` (predeterminado): usa Codex CLI si está instalado; en caso contrario usa API si existe `AGENT_API_KEY`, o la simulación local.
- `codex`: IA mediante la sesión de ChatGPT de Codex CLI. Ejecuta `codex login` (o `codex login --device-auth` en un servidor) y después `python3 server.py`. No necesita `AGENT_API_KEY` ni saldo de la API; consume los límites de Codex de la cuenta. Usa el modelo predeterminado de Codex y razonamiento bajo, no GPT-5 nano. La disponibilidad, los límites y las condiciones dependen de tu cuenta. Cada decisión inicia una conversación efímera con solo el rol propio y pistas públicas. Se desactivan herramientas de terminal, navegador, apps y delegación; no se entrega al jugador el documento de roles. No se copian credenciales ni sesiones a Git. La sesión pertenece al equipo donde se ejecuta el servidor; otros equipos deben iniciar sesión por separado.
- `api`: OpenAI Chat Completions con `AGENT_API_KEY` y opcionalmente `AGENT_MODEL` (predeterminado `gpt-5-nano`) y `AGENT_API_URL`. Este modo sí factura API por separado.
- `local`: simulación programada sin modelos, sin acceso a servicios externos.

Consulta `/api/config` para comprobar el motor seleccionado. No hay cambio silencioso a simulación si falla la IA: la partida se detiene y muestra un error. Codex tiene un límite de 90 segundos por decisión; la API, 25 segundos. Una respuesta inválida recibe una corrección como máximo. Cada llamada Codex usa un esquema JSON y una conversación nueva. Las opciones de CLI requieren una versión reciente compatible con `codex exec --ephemeral --output-schema`.

También puedes abrir `static/demo.html` directamente en tu navegador: incluye el motor local completo y permite descargar el registro, sin servidor. Esta demo guarda los roles en la memoria del navegador; el aislamiento de roles en el servidor requiere `server.py`.

Cada sesión se guarda inmediatamente en `data/<id>.json` con roles, palabra, pistas, votos y resultado. Esta carpeta no se sirve por HTTP y se excluye de Git. `/api/state` oculta secretos hasta finalizar y `/api/record` solo entrega la partida terminada. Quien tenga acceso al disco puede auditar los registros. No es un servicio multiusuario: hay una mesa compartida por proceso, sin autenticación. Un reinicio conserva los archivos de auditoría, pero no reanuda la partida.

Duración local aproximada: 24–42 segundos (uno o dos ciclos, según las expulsiones). Se puede ajustar `AGENT_TURN_SECONDS`; cada votación ocurre tras completar tres rondas. Con API, se añade el tiempo de respuesta del proveedor. El registro y el resultado muestran llamadas y tokens de entrada/salida reportados por el motor. Codex incluye en el consumo el contexto interno del CLI, además de las pistas del juego; no equivale a los tokens de una llamada API mínima. Se envían como máximo las últimas 12 pistas por llamada. Hay hasta 28 decisiones por partida y un máximo de 40 llamadas incluyendo correcciones, En modo API hay 256 tokens de salida por llamada y una reserva conservadora de 30.000 tokens por partida calculada antes de enviar cada petición. En modo Codex el límite es de 40 decisiones, incluidos reintentos; la longitud y el consumo dependen del CLI y de los límites de la cuenta. Al agotar un límite, la partida se detiene con un error visible. Cada pista debe ser una sola palabra nueva; las repeticiones se comparan sin distinguir mayúsculas ni acentos. Un intento inválido recibe una sola corrección y nunca se publica. El orden es fijo: Bruno → Leo → Mateo → Nico, saltando expulsados. GPT-5 nano usa reasoning_effort=minimal. La última prueba de la API con clave fue rechazada por saldo insuficiente; Codex usa una autenticación independiente. Tarifas consultadas: https://developers.openai.com/api/docs/models/gpt-5-nano (US$0,05 entrada / US$0,40 salida por millón de tokens; sujetas a cambios). Los agentes locales usan 24 temas y razonan con puntuaciones de afinidad y repetición; siguen siendo simulaciones programadas, no modelos de lenguaje. `PORT` permite cambiar el puerto.

Validación: `python3 -m unittest discover -s tests -v`.
