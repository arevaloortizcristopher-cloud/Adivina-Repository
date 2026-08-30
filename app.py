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
    "naranja": "#F3B08C",
    "amarillo": "#EFE08A",
    "verde": "#B9DFAE",
    "azul": "#AECBEA",
    "morado": "#C6B3E3",
    "fondo": "#FAFAFA",
    "tarjeta": "#FFFFFF",
    "texto": "#22232A",
    "negro_suave": "#20222B",
}

# Colores de las pastillas de navegación del dashboard (mismo orden que
# la maqueta "3. PANEL PRINCIPAL"): Perfil, Puntaje, Chat, Materias,
# Preferencias, Configuración.
COLORES_DASHBOARD = ["#EE9C74", "#EE9C74", "#DCE07E", "#9BCB9B", "#93DFC7", "#B7A6E0"]
# Colores de los accesos rápidos del chat (tonos verdes, como en la maqueta).
COLORES_CHAT_ACCIONES = ["#BFE6C9", "#A8DDB8", "#8FCB9E"]

COLOR_MATERIA = {
    "Ciencias": PALETA["verde"],
    "Matemáticas": PALETA["azul"],
    "Lenguaje": PALETA["rosa"],
    "Historia": PALETA["naranja"],
    "General": PALETA["morado"],
}


DESTINOS_DASHBOARD = ["perfil", "puntaje", "chat", "adivinanzas", "preferencias", "configuracion"]
DESTINOS_CHAT_ACCIONES = ["juego", "repaso", "examen"]


def _regla_color_dashboard() -> str:
    reglas = []
    for destino, color in zip(DESTINOS_DASHBOARD, COLORES_DASHBOARD):
        reglas.append(
            f'.st-key-dash_{destino} button {{'
            f'background:{color} !important; color:{PALETA["negro_suave"]} !important;}}'
        )
    return "\n".join(reglas)


def _regla_color_chat_acciones() -> str:
    reglas = []
    for destino, color in zip(DESTINOS_CHAT_ACCIONES, COLORES_CHAT_ACCIONES):
        reglas.append(
            f'.st-key-accion_{destino} button {{'
            f'background:{color} !important; color:{PALETA["negro_suave"]} !important;}}'
        )
    return "\n".join(reglas)


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;600;700;800&family=Quicksand:wght@400;500;600;700&display=swap');

html, body, .stApp {{
    background-color: {PALETA['fondo']};
    font-family: 'Quicksand', sans-serif;
}}

/* --------------------------------------------------------------------
   TEXTO SIEMPRE VISIBLE
   Streamlit Cloud a veces aplica un tema oscuro según el sistema
   operativo del usuario, y varios widgets (selectbox, menús, tooltips)
   se dibujan en un "portal" FUERA de .stApp, por lo que las reglas que
   solo apuntaban a ".stApp ..." no los cubrían y el texto quedaba
   blanco sobre blanco o negro sobre negro. Aquí se fuerza el color en
   TODO el árbol, incluidos esos portales.
   -------------------------------------------------------------------- */
*, *::before, *::after {{
    color: {PALETA['texto']};
}}
.stApp h1, .stApp h2, .stApp h3, .stApp h4,
.ghostie-title, .rainbow-text h1, .rainbow-text p {{
    font-family: 'Baloo 2', sans-serif !important;
    color: {PALETA['negro_suave']} !important;
}}

/* Campos de texto, área de texto y select */
.stApp input, .stApp textarea,
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea {{
    color: {PALETA['texto']} !important;
    background-color: #FFFFFF !important;
    border-radius: 12px !important;
}}
/* Selectbox: versiones antiguas de Streamlit usan data-baseweb="select";
   versiones recientes usan un ComboBox de react-aria. Cubrimos ambas. */
[data-baseweb="select"] *, .react-aria-ComboBox * {{
    color: {PALETA['texto']} !important;
}}
[data-baseweb="select"] > div, .react-aria-ComboBox,
.react-aria-ComboBox [role="group"], .react-aria-ComboBox input,
.react-aria-ComboBox button {{
    background-color: #FFFFFF !important;
    border-radius: 12px !important;
}}
.react-aria-ComboBox button svg {{
    fill: {PALETA['texto']} !important;
    color: {PALETA['texto']} !important;
}}

/* Menús / listas desplegables: se inyectan en un portal fuera de .stApp.
   Cubrimos tanto <ul role="listbox"><li role="option"> (BaseWeb) como
   <div role="listbox"><div role="option"> (react-aria). */
[role="listbox"], [role="option"], [role="presentation"],
div[data-baseweb="popover"], div[data-baseweb="menu"] {{
    background-color: #FFFFFF !important;
    color: {PALETA['texto']} !important;
}}
[role="option"]:hover {{
    background-color: {PALETA['amarillo']} !important;
}}

/* Encabezado superior y barra inferior del chat: se dibujan fuera del
   flujo normal y heredaban el fondo oscuro del tema del sistema. */
[data-testid="stHeader"], [data-testid="stBottom"],
[data-testid="stBottomBlockContainer"], [data-testid="stChatInput"] {{
    background-color: {PALETA['fondo']} !important;
}}
/* Streamlit añade divs intermedios con fondo oscuro fijo dentro de
   stBottom / stChatInput cuando el sistema está en modo oscuro; los
   neutralizamos para que se vea el fondo claro de la app. */
[data-testid="stBottom"] > div,
[data-testid="stChatInput"] > div {{
    background-color: transparent !important;
}}

/* Alertas (success / error / warning / info) */
[data-testid="stAlert"] * {{
    color: {PALETA['negro_suave']} !important;
}}

/* Botones normales y de formularios */
div.stButton > button, [data-testid="stFormSubmitButton"] button {{
    border-radius: 999px !important;
    border: none !important;
    padding: 0.6em 1.4em !important;
    font-family: 'Baloo 2', sans-serif !important;
    font-weight: 700 !important;
    width: 100%;
    background: linear-gradient(90deg, {PALETA['rosa']}, {PALETA['amarillo']});
    color: {PALETA['negro_suave']} !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}}
div.stButton > button *, [data-testid="stFormSubmitButton"] button * {{
    color: {PALETA['negro_suave']} !important;
}}
div.stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover {{
    filter: brightness(0.96);
}}

/* Botón negro tipo "pastilla" usado en el logo / encabezados */
.pill-dark {{
    display: inline-block;
    background: {PALETA['negro_suave']};
    color: #FFFFFF !important;
    font-family: 'Baloo 2', sans-serif;
    font-weight: 700;
    padding: 0.5em 1.6em;
    border-radius: 999px;
    font-size: 1.1em;
}}
.pill-dark * {{ color: #FFFFFF !important; }}

/* Tarjeta blanca redondeada (usada en Inicio) */
.tarjeta-blanca {{
    background: {PALETA['tarjeta']};
    border-radius: 28px;
    padding: 28px 20px;
    text-align: center;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    margin-bottom: 18px;
}}
.ghost-icon {{
    font-size: 4.5em;
    line-height: 1;
}}

/* Encabezado con arco de arcoíris + título superpuesto */
.rainbow-hero {{
    position: relative;
    text-align: center;
    padding-top: 10px;
    margin-bottom: 6px;
}}
.rainbow-hero svg {{
    width: 100%;
    max-width: 380px;
    display: block;
    margin: 0 auto;
}}
.rainbow-text {{
    margin-top: -46px;
}}
.rainbow-text h1 {{
    font-size: 2em;
    margin: 0;
}}
.rainbow-text p {{
    margin-top: 4px;
    font-size: 0.95em;
    color: {PALETA['texto']} !important;
}}

/* Chip de materia */
.materia-chip {{
    display: inline-block;
    padding: 0.3em 0.9em;
    border-radius: 999px;
    margin-bottom: 0.6em;
    font-family: 'Baloo 2', sans-serif;
    font-weight: 700;
    color: {PALETA['negro_suave']} !important;
}}

/* Franja decorativa arcoíris simple */
.rainbow-bar {{
    height: 8px;
    border-radius: 999px;
    margin: 4px 0 22px 0;
    background: linear-gradient(90deg,
        {PALETA['rosa']}, {PALETA['naranja']}, {PALETA['amarillo']},
        {PALETA['verde']}, {PALETA['azul']}, {PALETA['morado']});
}}

/* Encabezado del chat (estilo tarjeta café/dorado de la maqueta) */
.chat-header {{
    background: linear-gradient(135deg, #A9895E, #8C6F45);
    color: #FFFFFF !important;
    border-radius: 18px;
    padding: 14px 18px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.chat-header * {{ color: #FFFFFF !important; }}
.chat-header .icon {{ font-size: 1.8em; }}
.chat-header .titulo {{
    font-family: 'Baloo 2', sans-serif;
    font-weight: 700;
    font-size: 1.2em;
}}

/* Listón / ribbon para la pregunta de la adivinanza */
.ribbon-titulo {{
    text-align: center;
    font-family: 'Baloo 2', sans-serif;
    font-weight: 700;
    font-size: 1.4em;
    margin-bottom: 10px;
}}
.ribbon {{
    background: {PALETA['morado']};
    color: {PALETA['negro_suave']} !important;
    font-weight: 600;
    text-align: center;
    padding: 22px 34px;
    border-radius: 10px;
    clip-path: polygon(4% 0, 100% 0, 96% 100%, 0% 100%);
    margin-bottom: 18px;
}}
.ribbon * {{ color: {PALETA['negro_suave']} !important; }}

.resultado-correcto, .resultado-incorrecto {{
    text-align: center;
    font-family: 'Baloo 2', sans-serif;
    font-weight: 700;
    font-size: 1.1em;
    padding: 10px;
    border-radius: 12px;
    margin-top: 10px;
}}
.resultado-correcto {{ background: {PALETA['verde']}; }}
.resultado-incorrecto {{ background: {PALETA['rosa']}; }}

{_regla_color_dashboard()}
{_regla_color_chat_acciones()}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def _arco_arcoiris_svg() -> str:
    """Arco de arcoíris en SVG, como el de las maquetas de Registro/Login."""
    colores = [PALETA["rosa"], PALETA["naranja"], PALETA["amarillo"],
               PALETA["verde"], PALETA["azul"]]
    radios = [180, 154, 128, 102, 76]
    paths = []
    for color, r in zip(colores, radios):
        cx = 200
        x1, x2 = cx - r, cx + r
        paths.append(
            f'<path d="M{x1} 190 A{r} {r} 0 0 1 {x2} 190" '
            f'fill="none" stroke="{color}" stroke-width="24" stroke-linecap="round"/>'
        )
    return (
        '<svg viewBox="0 0 400 200" preserveAspectRatio="xMidYMax meet">'
        + "".join(paths) + "</svg>"
    )


def rainbow_header(titulo: str, subtitulo: str = ""):
    """Encabezado con arco de arcoíris y título superpuesto, como en las
    maquetas de Inicio / Registro / Login / Adivinanzas."""
    st.markdown(
        f"""
        <div class="rainbow-hero">
            {_arco_arcoiris_svg()}
            <div class="rainbow-text">
                <h1>{titulo}</h1>
                {f'<p>{subtitulo}</p>' if subtitulo else ''}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def barra_arcoiris():
    """Franja decorativa arcoíris, como en la maqueta de la interfaz."""
    st.markdown('<div class="rainbow-bar"></div>', unsafe_allow_html=True)


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
    st.markdown(
        f"""
        <div class="tarjeta-blanca">
            <div class="ghost-icon">👻</div>
            <div class="pill-dark" style="margin-top:14px;">Adivina_Estudio</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    barra_arcoiris()
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
    col_hero, col_form = st.columns([1, 1.1])
    with col_hero:
        rainbow_header("Inicia Sesión", "Utiliza tu usuario para poder ingresar.")
    with col_form:
        with st.form("form_login"):
            nombre_usuario = st.text_input("Nombre de usuario")
            password = st.text_input("Contraseña", type="password")
            enviar = st.form_submit_button("Siguiente", use_container_width=True)
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
    col_hero, col_form = st.columns([1, 1.1])
    with col_hero:
        rainbow_header("Regístrate", "¡Únete a esta comunidad!")
        st.caption("En caso de ya ser usuario, ¡por favor inicia sesión!")
    with col_form:
        with st.form("form_registro"):
            correo = st.text_input("Correo electrónico")
            nombre_usuario = st.text_input("Nombre de usuario")
            password = st.text_input("Contraseña", type="password")
            enviar = st.form_submit_button("Siguiente", use_container_width=True)
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
    barra_arcoiris()

    opciones = [
        ("Perfil", "perfil"),
        ("Puntaje", "puntaje"),
        ("Chat", "chat"),
        ("Materias / Adivinanzas", "adivinanzas"),
        ("Preferencias", "preferencias"),
        ("Configuración", "configuracion"),
    ]
    with st.container(key="dash_nav"):
        for etiqueta, destino in opciones:
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
def _enviar_a_ghostie(usuario, materia, mensaje, historial):
    db.guardar_mensaje_chat(usuario["id"], materia, "usuario", mensaje)
    api_key = st.session_state.get("groq_api_key") or None
    with st.spinner("Ghostie está pensando..."):
        respuesta = responder_socratico(mensaje, materia, historial, api_key=api_key)
    db.guardar_mensaje_chat(usuario["id"], materia, "ghostie", respuesta)


def pagina_chat():
    usuario = usuario_actual()
    materias_disponibles = riddles.MATERIAS + ["General"]
    materia = st.selectbox(
        "Materia del chat", materias_disponibles,
        index=materias_disponibles.index(usuario["materia_preferida"])
        if usuario["materia_preferida"] in materias_disponibles else 0,
    )

    st.markdown(
        f"""
        <div class="chat-header">
            <div class="icon">👻</div>
            <div class="titulo">Ghostie · {materia}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    historial = db.obtener_historial_chat(usuario["id"], materia)

    st.caption("¿Qué puedo hacer por ti hoy?")
    acciones = [
        ("🎲 Juego adivinanza", "juego"),
        ("📖 Repaso de lo visto", "repaso"),
        ("📝 Examen rápido", "examen"),
    ]
    with st.container(key="chat_acciones"):
        cols = st.columns(3)
        for col, (etiqueta, accion) in zip(cols, acciones):
            with col:
                if st.button(etiqueta, use_container_width=True, key=f"accion_{accion}"):
                    if accion == "juego":
                        st.session_state.materia_adivinanza = materia if materia in riddles.MATERIAS else None
                        st.session_state.adivinanza_actual = None
                        ir_a("adivinanzas")
                        st.rerun()
                    elif accion == "repaso":
                        _enviar_a_ghostie(usuario, materia, f"Ayúdame a repasar lo que hemos visto de {materia}.", historial)
                        st.rerun()
                    elif accion == "examen":
                        _enviar_a_ghostie(usuario, materia, f"Hazme un examen rápido de {materia}.", historial)
                        st.rerun()

    for turno in historial:
        with st.chat_message("assistant" if turno["rol"] == "ghostie" else "user"):
            st.write(turno["mensaje"])

    mensaje = st.chat_input("Escribe algo...")
    if mensaje:
        with st.chat_message("user"):
            st.write(mensaje)
        with st.chat_message("assistant"):
            api_key = st.session_state.get("groq_api_key") or None
            db.guardar_mensaje_chat(usuario["id"], materia, "usuario", mensaje)
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

    if "materia_adivinanza" not in st.session_state:
        st.session_state.materia_adivinanza = None
    if "adivinanza_actual" not in st.session_state:
        st.session_state.adivinanza_actual = None

    if st.session_state.materia_adivinanza is None:
        rainbow_header("Adivinanzas", "Selecciona un tema para comenzar:")
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
        f'<span class="materia-chip" style="background:{color}">🕷️ {materia}</span>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="ribbon-titulo">La adivinanza de hoy es...</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ribbon">{adivinanza["pregunta"]}</div>', unsafe_allow_html=True)

    with st.expander("🕷️ Pedir una pista"):
        st.write(adivinanza["pista"])

    respuesta = st.text_input("¿Qué soy?", key=f"resp_{adivinanza['id']}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Comprobar respuesta", use_container_width=True):
            acerto = riddles.validar_respuesta(adivinanza, respuesta)
            db.registrar_intento_adivinanza(usuario["id"], adivinanza["id"], acerto)
            if acerto:
                db.sumar_puntos(usuario["id"], 10)
                st.markdown(
                    '<div class="resultado-correcto">✅ ¡Correcto! +10 puntos</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="resultado-incorrecto">❌ No es correcto. '
                    f'La respuesta era: {adivinanza["respuesta"]}.</div>',
                    unsafe_allow_html=True,
                )
    with col2:
        if st.button("Siguiente adivinanza", use_container_width=True):
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
