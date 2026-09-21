import streamlit as st
from textblob import TextBlob
from deep_translator import GoogleTranslator

# ── Configuración de la pantalla ──────────────────────────────────────────────
st.set_page_config(
    page_title="Gestión de Opiniones - Taller MotoCarro",
    page_icon="🤖",
    layout="wide",
)

# ── Inicialización de la sesión ───────────────────────────────────────────────
if "reviews" not in st.session_state:
    st.session_state.reviews = []

# ── Diccionario auxiliar en español ──────────────────────────────────────────
PALABRAS_POSITIVAS = [
    "excelente", "bueno", "buena", "genial", "rapido", "rápido", "perfecto",
    "amable", "justo", "gran", "nuevo", "satisfecho", "magnifico", "magnífico",
    "increible", "increíble", "recomiendo", "eficiente", "me gasta", "me gusto", "me gustó"
]

PALABRAS_NEGATIVAS = [
    "pesimo", "pésimo", "malo", "mala", "terrible", "horrible", "caro", "cara",
    "tardo", "tardó", "demora", "demorado", "defectuoso", "falla", "fallo",
    "peor", "dañado", "estafa", "sucio", "incompetente", "lento", "lenta"
]

# ── Función robusta de análisis ──────────────────────────────────────────────
def analizar_comentario(texto, usar_traduccion=True):
    if not texto.strip():
        return None

    texto_lower = texto.lower()
    score_manual = 0.0

    # 1. Ajuste manual por palabras clave en español
    for p in PALABRAS_POSITIVAS:
        if p in texto_lower:
            score_manual += 0.45

    for p in PALABRAS_NEGATIVAS:
        if p in texto_lower:
            score_manual -= 0.45

    # 2. Intento de traducción con TextBlob
    texto_traducido = texto
    if usar_traduccion:
        try:
            texto_traducido = GoogleTranslator(source="auto", target="en").translate(texto)
        except Exception:
            texto_traducido = texto

    blob = TextBlob(texto_traducido)
    polaridad_tb = blob.sentiment.polarity
    subjetividad = blob.sentiment.subjectivity

    # Combinación de scores
    if abs(score_manual) > 0:
        polaridad_final = score_manual
        if polaridad_tb != 0:
            polaridad_final = (score_manual + polaridad_tb) / 2
    else:
        polaridad_final = polaridad_tb

    # Normalización [-1, 1]
    polaridad_final = max(-1.0, min(1.0, polaridad_final))

    # Criterio de clasificación
    if polaridad_final > 0.1:
        categoria = "Positivo"
        emoji = "🟢 😊"
    elif polaridad_final < -0.1:
        categoria = "Negativo"
        emoji = "🔴 😞"
    else:
        categoria = "Neutral / Aceptable"
        emoji = "🟡 😐"

    return {
        "texto_original": texto,
        "categoria": categoria,
        "emoji": emoji,
        "polaridad": polaridad_final,
        "subjetividad": subjetividad,
    }

# ── Encabezado Principal ──────────────────────────────────────────────────────
st.title("🛠️ Sistema de Satisfacción - Taller de Moto-Carros")
st.caption("Herramienta automatizada para analizar las reseñas y opiniones de los clientes.")

# ── Formulario de ingreso ────────────────────────────────────────────────────
st.subheader("📝 Registrar nueva opinión del cliente")

with st.form("form_comentario", clear_on_submit=True):
    col_input, col_opcion = st.columns([3, 1])
    
    with col_input:
        nuevo_texto = st.text_area(
            "Comentario del servicio:",
            placeholder="Ej.: La reparación fue excelente pero el repuesto estuvo caro...",
            height=100
        )
    
    with col_opcion:
        st.write("Configuración:")
        traducir = st.checkbox("Traducción / Análisis avanzado", value=True)
        btn_guardar = st.form_submit_button("Analizar y Guardar 🚀")

    if btn_guardar:
        if nuevo_texto.strip():
            resultado = analizar_comentario(nuevo_texto, traducir)
            if resultado:
                st.session_state.reviews.append(resultado)
                st.success("¡Comentario registrado e interpretado con éxito!")
        else:
            st.warning("Por favor escribe un comentario antes de enviar.")

st.divider()

# ── Análisis y Métricas ──────────────────────────────────────────────────────
st.subheader("📊 Análisis General y Estadísticas de Satisfacción")

if not st.session_state.reviews:
    st.info("Aún no se han ingresado comentarios. Registra el primero arriba.")
else:
    total = len(st.session_state.reviews)
    positivos = sum(1 for r in st.session_state.reviews if r["categoria"] == "Positivo")
    negativos = sum(1 for r in st.session_state.reviews if r["categoria"] == "Negativo")
    neutrales = sum(1 for r in st.session_state.reviews if r["categoria"] == "Neutral / Aceptable")
    
    promedio_polaridad = sum(r["polaridad"] for r in st.session_state.reviews) / total

    if promedio_polaridad > 0.1:
        prevalente = "Positivo 😊"
    elif promedio_polaridad < -0.1:
        prevalente = "Negativo 😞"
    else:
        prevalente = "Neutral / Balanceado 😐"

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Opiniones", total)
    c2.metric("Positivos 🟢", positivos)
    c3.metric("Neutrales 🟡", neutrales)
    c4.metric("Negativos 🔴", negativos)
    c5.metric("Promedio General", f"{promedio_polaridad:.2f}")

    st.markdown(f"**Sentimiento Prevalente en el Taller:** `{prevalente}`")
    st.progress((promedio_polaridad + 1) / 2, text="Línea de tendencia: ← Negativo | Neutro | Positivo →")

    st.divider()

    # ── Histórico ─────────────────────────────────────────────────────────────
    st.subheader("📋 Registro Histórico de Comentarios")
    
    for idx, rev in enumerate(reversed(st.session_state.reviews), 1):
        with st.expander(f"Comentario #{total - idx + 1} - Status: {rev['emoji']} ({rev['categoria']})"):
            st.write(f"**Texto:** *\"{rev['texto_original']}\"*")
            col_a, col_b = st.columns(2)
            col_a.write(f"**Puntaje de Polaridad:** {rev['polaridad']:.3f}")
            col_b.write(f"**Grado de Subjetividad:** {rev['subjetividad']:.3f}")

    if st.button("Limpiar todos los comentarios"):
        st.session_state.reviews = []
        st.rerun()