"""
app.py
------
Adivina_Estudio - Prototipo funcional en Streamlit.

Estructura basada en las 5 pantallas del documento "interfaz_grafica":
    1. Página principal (Inicio)
    2. Registro / Inicio de sesión
    3. Panel principal (Dashboard)
    4. Chat de asistente (Ghostie, motor socrático de IA)
    5. Adivinanzas (quiz con puntos y recompensas)

Ejecutar con:
    streamlit run app.py
"""

import streamlit as st

import database as db
import riddles
from ai_engine import responder_socratico

# ----------------------------------------------------------------------
# Configuración general y paleta "arcoíris pastel" descrita en el documento
# ----------------------------------------------------------------------
st.set_page_config(page_title="Adivina_Estudio", page_icon="👻", layout="centered")

PALETA = {
    "rosa": "#F7B9C2",
    "naranja": "#F6C89F",
    "amarillo": "#F3E39C",
    "verde": "#C9E4B4",
    "azul": "#B9D7EA",
    "morado": "#C9B6E4",
    "fondo": "#FAFAFA",
    "texto": "#222222",
}

CSS = f"""
<style>
.stApp {{
    background-color: {PALETA['fondo']};
}}
/* Streamlit Cloud aplica texto blanco cuando detecta modo oscuro del
   sistema operativo del usuario; como forzamos un fondo claro, hay que
   forzar también el color de TODO el texto para que no quede invisible. */
.stApp, .stApp p, .stApp li, .stApp label, .stApp span,
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p,
[data-testid="stHeader"], .stApp h1, .stApp h2, .stApp h3 {{
    color: {PALETA['texto']} !important;
}}
div.stButton > button {{
    border-radius: 999px;
    border: none;
    padding: 0.6em 1.4em;
    font-weight: 600;
    background: linear-gradient(90deg, {PALETA['rosa']}, {PALETA['amarillo']});
    color: {PALETA['texto']} !important;
}}
div.stButton > button p {{
    color: {PALETA['texto']} !important;
}}
.ghostie-title {{
    text-align: center;
    font-size: 2.2em;
    font-weight: 800;
    color: {PALETA['texto']} !important;
}}
.materia-chip {{
    display: inline-block;
    padding: 0.3em 0.9em;
    border-radius: 999px;
    margin: 0.2em;
    font-weight: 600;
    color: {PALETA['texto']} !important;
}}
.rainbow-bar {{
    height: 8px;
    border-radius: 999px;
    margin: 4px 0 22px 0;
    background: linear-gradient(90deg,
        {PALETA['rosa']}, {PALETA['naranja']}, {PALETA['amarillo']},
        {PALETA['verde']}, {PALETA['azul']}, {PALETA['morado']});
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def barra_arcoiris():
    """Franja decorativa arcoíris, como en la maqueta de la interfaz."""
    st.markdown('<div class="rainbow-bar"></div>', unsafe_allow_html=True)

COLOR_MATERIA = {
    "Ciencias": PALETA["verde"],
    "Matemáticas": PALETA["azul"],
    "Lenguaje": PALETA["rosa"],
    "Historia": PALETA["naranja"],
    "General": PALETA["morado"],
}

db.init_db()

# ----------------------------------------------------------------------
# Estado de sesión
# ----------------------------------------------------------------------
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"
if "usuario" not in st.session_state:
    st.session_state.usuario = None


def ir_a(pagina: str):
    st.session_state.pagina = pagina


def usuario_actual():
    if st.session_state.usuario:
        return db.obtener_usuario(st.session_state.usuario["id"])
    return None


# ----------------------------------------------------------------------
# 1. PÁGINA PRINCIPAL (INICIO)
# ----------------------------------------------------------------------
def pagina_inicio():
    barra_arcoiris()
    st.markdown('<div class="ghostie-title">👻 Adivina_Estudio</div>', unsafe_allow_html=True)
    st.caption("IA con enfoque pedagógico — piensa, no dependas.")
    st.write(
        "Ghostie es tu mascota-guía: te ayuda a razonar con preguntas, "
        "juega adivinanzas contigo y nunca hace la tarea por ti."
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Iniciar sesión", use_container_width=True):
            ir_a("login")
    with col2:
        if st.button("Registrarme", use_container_width=True):
            ir_a("registro")


# ----------------------------------------------------------------------
# 2. REGISTRO / INICIO DE SESIÓN
# ----------------------------------------------------------------------
def pagina_login():
    barra_arcoiris()
    st.header("Inicia sesión")
    st.caption("Utiliza tu usuario para poder ingresar.")
    with st.form("form_login"):
        nombre_usuario = st.text_input("Nombre de usuario")
        password = st.text_input("Contraseña", type="password")
        enviar = st.form_submit_button("Siguiente")
    if enviar:
        usuario = db.validar_login(nombre_usuario, password)
        if usuario:
            st.session_state.usuario = usuario
            ir_a("dashboard")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
    st.divider()
    if st.button("¿No tienes cuenta? Regístrate"):
        ir_a("registro")


def pagina_registro():
    barra_arcoiris()
    st.header("Regístrate")
    st.caption("¡Únete a esta comunidad!")
    with st.form("form_registro"):
        correo = st.text_input("Correo electrónico")
        nombre_usuario = st.text_input("Nombre de usuario")
        password = st.text_input("Contraseña", type="password")
        enviar = st.form_submit_button("Siguiente")
    if enviar:
        if not correo or not nombre_usuario or not password:
            st.warning("Completa todos los campos.")
        else:
            ok, msg = db.crear_usuario(nombre_usuario, correo, password)
            if ok:
                st.success(msg + " Ahora inicia sesión.")
                ir_a("login")
                st.rerun()
            else:
                st.error(msg)
    st.divider()
    if st.button("En caso de ya ser usuario, favor iniciar sesión"):
        ir_a("login")


# ----------------------------------------------------------------------
# 3. PANEL PRINCIPAL (DASHBOARD)
# ----------------------------------------------------------------------
def pagina_dashboard():
    usuario = usuario_actual()
    st.markdown(f"### 👻 ¡Hola, {usuario['nombre_usuario']}!")
    st.write(f"⭐ Puntos: **{usuario['puntos']}**  |  📘 Materia preferida: **{usuario['materia_preferida']}**")

    st.write("")
    cols = st.columns(3)
    opciones = [
        ("Perfil", "perfil"),
        ("Puntaje", "puntaje"),
        ("Chat", "chat"),
        ("Materias / Adivinanzas", "adivinanzas"),
        ("Preferencias", "preferencias"),
        ("Configuración", "configuracion"),
    ]
    for i, (etiqueta, destino) in enumerate(opciones):
        with cols[i % 3]:
            if st.button(etiqueta, use_container_width=True, key=f"dash_{destino}"):
                ir_a(destino)

    st.divider()
    if st.button("Cerrar sesión"):
        st.session_state.usuario = None
        ir_a("inicio")
        st.rerun()


def pagina_perfil():
    usuario = usuario_actual()
    st.header("Perfil")
    st.write(f"**Usuario:** {usuario['nombre_usuario']}")
    st.write(f"**Correo:** {usuario['correo']}")
    st.write(f"**Miembro desde:** {usuario['fecha_registro'][:10]}")
    st.write(f"**Puntos acumulados:** {usuario['puntos']}")
    if st.button("⬅ Volver al panel"):
        ir_a("dashboard")


def pagina_puntaje():
    st.header("🏆 Puntaje y recompensas")
    tabla = db.tabla_posiciones()
    if tabla:
        for i, fila in enumerate(tabla, start=1):
            st.write(f"{i}. **{fila['nombre_usuario']}** — {fila['puntos']} pts")
    else:
        st.info("Aún no hay puntajes registrados.")
    if st.button("⬅ Volver al panel"):
        ir_a("dashboard")


def pagina_preferencias():
    usuario = usuario_actual()
    st.header("Preferencias")
    materia = st.selectbox(
        "Materia preferida", riddles.MATERIAS,
        index=riddles.MATERIAS.index(usuario["materia_preferida"])
        if usuario["materia_preferida"] in riddles.MATERIAS else 0,
    )
    if st.button("Guardar preferencia"):
        db.actualizar_preferencia(usuario["id"], materia)
        st.success("Preferencia actualizada.")
        st.rerun()
    if st.button("⬅ Volver al panel"):
        ir_a("dashboard")


def pagina_configuracion():
    st.header("Configuración")
    st.write("Clave de Groq API (opcional, para el motor de IA en línea).")
    clave = st.text_input("GROQ_API_KEY", type="password",
                           value=st.session_state.get("groq_api_key", ""))
    if st.button("Guardar clave"):
        st.session_state.groq_api_key = clave
        st.success("Clave guardada para esta sesión.")
    st.caption(
        "Si no configuras una clave, Ghostie funcionará en modo sin conexión "
        "con preguntas socráticas genéricas."
    )
    if st.button("⬅ Volver al panel"):
        ir_a("dashboard")


# ----------------------------------------------------------------------
# 4. CHAT DE ASISTENTE (Ghostie)
# ----------------------------------------------------------------------
def pagina_chat():
    usuario = usuario_actual()
    materia = st.selectbox("Materia del chat", riddles.MATERIAS + ["General"],
                            index=(riddles.MATERIAS + ["General"]).index(usuario["materia_preferida"])
                            if usuario["materia_preferida"] in riddles.MATERIAS + ["General"] else 0)
    color = COLOR_MATERIA.get(materia, PALETA["morado"])
    st.markdown(
        f'<span class="materia-chip" style="background:{color}">Ghostie · {materia}</span>',
        unsafe_allow_html=True,
    )

    historial = db.obtener_historial_chat(usuario["id"], materia)
    for turno in historial:
        with st.chat_message("assistant" if turno["rol"] == "ghostie" else "user"):
            st.write(turno["mensaje"])

    mensaje = st.chat_input("Escribe algo...")
    if mensaje:
        db.guardar_mensaje_chat(usuario["id"], materia, "usuario", mensaje)
        with st.chat_message("user"):
            st.write(mensaje)

        api_key = st.session_state.get("groq_api_key") or None
        with st.chat_message("assistant"):
            with st.spinner("Ghostie está pensando..."):
                respuesta = responder_socratico(mensaje, materia, historial, api_key=api_key)
            st.write(respuesta)
        db.guardar_mensaje_chat(usuario["id"], materia, "ghostie", respuesta)

    st.divider()
    if st.button("⬅ Volver al panel"):
        ir_a("dashboard")


# ----------------------------------------------------------------------
# 5. ADIVINANZAS
# ----------------------------------------------------------------------
def pagina_adivinanzas():
    usuario = usuario_actual()
    st.header("🔮 Adivinanzas")

    if "materia_adivinanza" not in st.session_state:
        st.session_state.materia_adivinanza = None
    if "adivinanza_actual" not in st.session_state:
        st.session_state.adivinanza_actual = None

    if st.session_state.materia_adivinanza is None:
        st.write("Selecciona un tema para comenzar:")
        cols = st.columns(len(riddles.MATERIAS))
        for i, materia in enumerate(riddles.MATERIAS):
            with cols[i]:
                if st.button(materia, key=f"mat_{materia}", use_container_width=True):
                    st.session_state.materia_adivinanza = materia
                    resueltas = db.adivinanzas_resueltas(usuario["id"])
                    st.session_state.adivinanza_actual = riddles.elegir_adivinanza(materia, resueltas)
                    st.rerun()
        if st.button("⬅ Volver al panel"):
            ir_a("dashboard")
        return

    materia = st.session_state.materia_adivinanza
    adivinanza = st.session_state.adivinanza_actual
    color = COLOR_MATERIA.get(materia, PALETA["morado"])
    st.markdown(
        f'<span class="materia-chip" style="background:{color}">{materia}</span>',
        unsafe_allow_html=True,
    )
    st.subheader("La adivinanza de hoy es...")
    st.write(adivinanza["pregunta"])

    with st.expander("🕷️ Pedir una pista"):
        st.write(adivinanza["pista"])

    respuesta = st.text_input("¿Qué soy?", key=f"resp_{adivinanza['id']}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Comprobar respuesta"):
            acerto = riddles.validar_respuesta(adivinanza, respuesta)
            db.registrar_intento_adivinanza(usuario["id"], adivinanza["id"], acerto)
            if acerto:
                db.sumar_puntos(usuario["id"], 10)
                st.success("✅ ¡Correcto! +10 puntos")
            else:
                st.error(f"❌ No es correcto. La respuesta era: {adivinanza['respuesta']}.")
    with col2:
        if st.button("Siguiente adivinanza"):
            resueltas = db.adivinanzas_resueltas(usuario["id"])
            st.session_state.adivinanza_actual = riddles.elegir_adivinanza(materia, resueltas)
            st.rerun()

    st.divider()
    if st.button("Cambiar de materia"):
        st.session_state.materia_adivinanza = None
        st.session_state.adivinanza_actual = None
        st.rerun()
    if st.button("⬅ Volver al panel"):
        ir_a("dashboard")


# ----------------------------------------------------------------------
# Enrutador principal
# ----------------------------------------------------------------------
PAGINAS_PUBLICAS = {"inicio": pagina_inicio, "login": pagina_login, "registro": pagina_registro}
PAGINAS_PRIVADAS = {
    "dashboard": pagina_dashboard,
    "perfil": pagina_perfil,
    "puntaje": pagina_puntaje,
    "chat": pagina_chat,
    "adivinanzas": pagina_adivinanzas,
    "preferencias": pagina_preferencias,
    "configuracion": pagina_configuracion,
}

pagina = st.session_state.pagina
if pagina in PAGINAS_PUBLICAS:
    PAGINAS_PUBLICAS[pagina]()
elif pagina in PAGINAS_PRIVADAS:
    if st.session_state.usuario is None:
        st.warning("Debes iniciar sesión primero.")
        ir_a("login")
        st.rerun()
    else:
        PAGINAS_PRIVADAS[pagina]()
else:
    ir_a("inicio")
    st.rerun()
