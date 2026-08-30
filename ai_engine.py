"""
ai_engine.py
------------
Motor socrático de IA para el "Chat de Asistente" (Ghostie).

Implementa el objetivo general del proyecto: orientar mediante
preguntas socráticas a estudiantes menores de edad, evitando que la
IA resuelva la tarea por ellos, fomentando pensamiento crítico,
verificación activa de fuentes y conciencia sobre sesgos.

Usa la Groq API (mencionada en el documento como opción gratuita y
ultrarrápida con Llama 3) mediante peticiones HTTP simples, sin SDKs
adicionales. Si no hay API key configurada, cae en un modo local de
respaldo ("modo offline") para que el prototipo siga siendo usable
en una demo sin conexión ni credenciales.
"""

import os
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-70b-8192"

SYSTEM_PROMPT = """Eres "Ghostie", el asistente virtual fantasma de la app \
educativa Adivina_Estudio, dirigida a estudiantes menores de edad.

REGLAS INQUEBRANTABLES:
1. Nunca das la respuesta final de una tarea, ejercicio o pregunta de \
examen. En su lugar, guías con preguntas socráticas ("¿qué sabes ya \
sobre esto?", "¿qué pasaría si...?", "¿cómo podrías comprobarlo?").
2. Fomentas la verificación activa: cuando el tema lo permite, invitas \
al estudiante a contrastar la información con un libro, su docente o \
una fuente confiable, en lugar de aceptar todo como verdad absoluta.
3. Estás alerta a sesgos de género, raza o cultura en cualquier \
ejemplo que uses, y ofreces perspectivas equilibradas.
4. Cuidas la privacidad: nunca pides datos personales sensibles (dirección, \
teléfono, ubicación exacta, contraseñas) y recuerdas al estudiante que no \
debe compartirlos.
5. Tu tono es cálido, paciente y motivador, adecuado para menores de edad. \
Usas un lenguaje claro y sencillo, evitando cualquier contenido no apto \
para su edad.
6. Materia actual de la conversación: {materia}. Ajusta tus preguntas y \
ejemplos a esa materia cuando sea posible.
"""


class GhostieOffline:
    """Respaldo sin conexión: banco de preguntas socráticas genéricas.

    Se activa automáticamente si no hay GROQ_API_KEY configurada o si
    la llamada a la API falla, para que el prototipo nunca se quede sin
    respuesta durante una demostración.
    """

    PREGUNTAS_GUIA = [
        "Antes de seguir, ¿qué es lo primero que ya sabes sobre este tema?",
        "¿Qué parte del problema te parece más confusa? Vamos por partes.",
        "Si tuvieras que explicárselo a un compañero, ¿cómo empezarías?",
        "¿Se te ocurre alguna fuente (libro, apunte, docente) donde puedas "
        "verificar esa idea antes de darla por segura?",
        "¿Qué pasaría si cambiamos un dato del problema? ¿La respuesta seguiría igual?",
    ]

    def responder(self, mensaje_usuario: str, materia: str, historial=None) -> str:
        import random

        pregunta = random.choice(self.PREGUNTAS_GUIA)
        return (
            f"👻 (modo sin conexión) Entiendo que estás trabajando en {materia}. "
            f"{pregunta}"
        )


def _construir_mensajes(materia: str, historial: list, mensaje_usuario: str):
    mensajes = [{"role": "system", "content": SYSTEM_PROMPT.format(materia=materia)}]
    for turno in historial or []:
        rol = "assistant" if turno["rol"] == "ghostie" else "user"
        mensajes.append({"role": rol, "content": turno["mensaje"]})
    mensajes.append({"role": "user", "content": mensaje_usuario})
    return mensajes


def responder_socratico(mensaje_usuario: str, materia: str, historial=None,
                         api_key: str | None = None) -> str:
    """Genera una respuesta socrática de Ghostie.

    Parameters
    ----------
    mensaje_usuario: texto que escribió el estudiante.
    materia: materia/asignatura activa del chat (para dar contexto).
    historial: lista de dicts {"rol": "usuario"|"ghostie", "mensaje": str}.
    api_key: clave de Groq; si es None, se busca en la variable de
        entorno GROQ_API_KEY. Si tampoco existe, se usa el modo offline.
    """
    api_key = api_key or os.environ.get("GROQ_API_KEY")

    if not api_key:
        return GhostieOffline().responder(mensaje_usuario, materia, historial)

    payload = {
        "model": GROQ_MODEL,
        "messages": _construir_mensajes(materia, historial, mensaje_usuario),
        "temperature": 0.6,
        "max_tokens": 400,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        # Cualquier error de red/API cae a modo offline en vez de romper la demo.
        return GhostieOffline().responder(mensaje_usuario, materia, historial)
