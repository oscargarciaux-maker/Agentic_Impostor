# La mesa del impostor

Juego autónomo para cuatro agentes con interfaz web en español. Requiere Python 3.10+; no instala dependencias.

```sh
python3 server.py
```

Abre el puerto 8000 en tu navegador. Pulsa **Comenzar partida**: se asignan tres civiles y un impostor con aleatoriedad del sistema, los agentes dan tres rondas de pistas y votan sin intervención. Si expulsan a un civil, continúan los tres restantes durante otro ciclo. Con dos jugadores vivos gana el impostor. Los empates se resuelven por sorteo anunciado entre los más votados. Los roles se muestran solo al terminar.

Por defecto funciona como **simulación local**: cuatro políticas independientes de pistas e inferencia, sin modelos de lenguaje. Para usar cuatro participantes mediante un modelo, configura en el proceso `AGENT_API_KEY`, y opcionalmente `AGENT_MODEL` (predeterminado `gpt-4o-mini`) y `AGENT_API_URL` (endpoint compatible con OpenAI Chat Completions). Cada llamada recibe únicamente el rol propio, la palabra si es civil y las pistas públicas. No recibe roles ajenos ni votos previos. El modelo compartido no conserva conversaciones entre llamadas. Las llamadas de API tienen un límite de 25 segundos; un fallo detiene la partida con un error visible, sin inventar respuestas.

También puedes abrir `static/demo.html` directamente en tu navegador: incluye el motor local completo y permite descargar el registro, sin servidor. Esta demo guarda los roles en la memoria del navegador; el aislamiento de roles en el servidor requiere `server.py`.

Cada sesión se guarda inmediatamente en `data/<id>.json` con roles, palabra, pistas, votos y resultado. Esta carpeta no se sirve por HTTP y se excluye de Git. `/api/state` oculta secretos hasta finalizar y `/api/record` solo entrega la partida terminada. Quien tenga acceso al disco puede auditar los registros. No es un servicio multiusuario: hay una mesa compartida por proceso, sin autenticación. Un reinicio conserva los archivos de auditoría, pero no reanuda la partida.

Duración local aproximada: 24–42 segundos (uno o dos ciclos, según las expulsiones). Se puede ajustar `AGENT_TURN_SECONDS`; cada votación ocurre tras completar tres rondas. Con API, se añade el tiempo de respuesta del proveedor. El registro y el resultado muestran llamadas y tokens de entrada/salida reportados por el proveedor. Se envían como máximo las últimas 16 pistas por llamada. No hay límite de gasto monetario implementado; el máximo es 28 llamadas por partida, con 120 tokens de salida por llamada. Los agentes locales usan 24 temas y razonan con puntuaciones de afinidad y repetición; siguen siendo simulaciones programadas, no modelos de lenguaje. `PORT` permite cambiar el puerto.

Validación: `python3 -m unittest discover -s tests -v`.
