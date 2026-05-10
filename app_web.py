import sys
import subprocess

def instalar_si_falta(libreria, nombre_paquete=None):
    if nombre_paquete is None:
        nombre_paquete = libreria
    try:
        __import__(libreria)
    except ImportError:
        print(f"⏳ Instalando '{nombre_paquete}'...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", nombre_paquete])
        print(f"✅ '{nombre_paquete}' instalada.\n")

# --- INSTALACIÓN AUTOMÁTICA ---
instalar_si_falta('streamlit')
instalar_si_falta('pandas')
instalar_si_falta('openpyxl')

import streamlit as st
import pandas as pd
import random
from pathlib import Path

# Configuración de la página
st.set_page_config(page_title="Simulador de Exámenes", page_icon="📚", layout="centered")

st.title("📚 Simulador de Exámenes 📚")

REQUIRED_COLS = ["Tema", "Pregunta", "A", "B", "C", "D", "Correcta"]


def _listar_excels_locales() -> list[str]:
    excels = sorted([p.name for p in Path(".").glob("*.xlsx")])
    # Preferimos el banco estándar si existe.
    if "preguntas.xlsx" in excels:
        excels.remove("preguntas.xlsx")
        excels.insert(0, "preguntas.xlsx")
    return excels

# Cacheamos la carga de datos para que no se recargue en cada interacción
@st.cache_data
def cargar_excel(ruta_archivo):
    try:
        df = pd.read_excel(ruta_archivo)
        return df
    except FileNotFoundError:
        return None

# --- Gestión del estado de la aplicación (Manejo de navegación y memoria) ---
if 'estado' not in st.session_state:
    st.session_state.estado = 'MENU' # Posibles estados: MENU, JUGANDO, RESULTADOS
if 'preguntas' not in st.session_state:
    st.session_state.preguntas = None
if 'indice_pregunta' not in st.session_state:
    st.session_state.indice_pregunta = 0
if 'aciertos' not in st.session_state:
    st.session_state.aciertos = 0
if 'fallos' not in st.session_state:
    st.session_state.fallos = 0
if 'modo' not in st.session_state:
    st.session_state.modo = None
if 'feedback' not in st.session_state:
    st.session_state.feedback = None


# --- Selección de Excel (al inicio) ---
st.sidebar.markdown("### Archivo de preguntas")
excels_disponibles = _listar_excels_locales()
if not excels_disponibles:
    st.sidebar.error("No se han encontrado archivos .xlsx en esta carpeta.")
    st.stop()

archivo_excel = st.sidebar.selectbox(
    "Selecciona el Excel a usar",
    options=excels_disponibles,
    index=0,
    key="excel_seleccionado",
    disabled=(st.session_state.estado != "MENU"),
)
st.sidebar.caption("(Puedes añadir más .xlsx a la carpeta y aparecerán aquí)" )

df = cargar_excel(archivo_excel)
if df is None:
    st.error(
        f"Error: No se encontró el archivo '{archivo_excel}'. Asegúrate de que exista en la misma carpeta."
    )
    st.stop()

missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
if missing_cols:
    st.error(
        "El Excel seleccionado no tiene el formato esperado. "
        f"Faltan columnas: {missing_cols}."
    )
    st.stop()

# Funciones de utilidad para el control del test
def iniciar_test(df_seleccionado, modo_nombre):
    # Barajamos las preguntas
    st.session_state.preguntas = df_seleccionado.sample(frac=1).reset_index(drop=True)
    st.session_state.estado = 'JUGANDO'
    st.session_state.indice_pregunta = 0
    st.session_state.aciertos = 0
    st.session_state.fallos = 0
    st.session_state.modo = modo_nombre
    st.session_state.feedback = None

def volver_al_menu():
    st.session_state.estado = 'MENU'
    st.session_state.feedback = None

def responder(respuesta_elegida, correcta):
    # Evaluamos la respuesta
    if respuesta_elegida == correcta:
        st.session_state.aciertos += 1
        st.session_state.feedback = {"tipo": "success", "texto": "✅ ¡CORRECTO!"}
    else:
        st.session_state.fallos += 1
        st.session_state.feedback = {"tipo": "error", "texto": f"❌ INCORRECTO. La respuesta correcta era la: {correcta}"}

def avanzar_pregunta():
    st.session_state.feedback = None
    st.session_state.indice_pregunta += 1
    if st.session_state.indice_pregunta >= len(st.session_state.preguntas):
        st.session_state.estado = 'RESULTADOS'


# ==========================================
# VISTAS DE LA APLICACIÓN
# ==========================================

# 1. PANTALLA MENÚ
if st.session_state.estado == 'MENU':
    st.header("Menú Principal")
    st.write("Elige el modo de estudio:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Mix General")
        st.write("Resuelve todas las preguntas disponibles.")
        if st.button("Iniciar Mix", use_container_width=True):
            iniciar_test(df, "Mix General")
            st.rerun()
            
    with col2:
        st.subheader("Examen Normal")
        st.write("50 preguntas aleatorias. Acierto: +2, Fallo: -0.66")
        if st.button("Iniciar Examen", use_container_width=True):
            cantidad = min(50, len(df))
            iniciar_test(df.sample(n=cantidad), "Examen Normal")
            st.rerun()
            
    with col3:
        st.subheader("Por Tema")
        temas_disponibles = df['Tema'].unique()
        tema_elegido = st.selectbox("Elige un tema:", temas_disponibles)
        if st.button("Iniciar por Tema", use_container_width=True):
            df_tema = df[df['Tema'].str.lower() == tema_elegido.lower()]
            iniciar_test(df_tema, f"Tema: {tema_elegido.upper()}")
            st.rerun()

# 2. PANTALLA JUGANDO
elif st.session_state.estado == 'JUGANDO':
    idx = st.session_state.indice_pregunta
    total = len(st.session_state.preguntas)
    
    st.progress(idx / total if total > 0 else 0)
    st.caption(f"**Modo:** {st.session_state.modo} | **Pregunta:** {idx + 1} de {total}")
    
    st.sidebar.markdown("### Configuración")
    mostrar_puntuacion = st.sidebar.toggle("Mostrar puntuación en vivo", value=True)
    
    if mostrar_puntuacion:
        st.sidebar.metric("Aciertos ✅", st.session_state.aciertos)
        st.sidebar.metric("Fallos ❌", st.session_state.fallos)
    else:
        st.sidebar.info("🙈 Puntuación oculta")
    
    pregunta_actual = st.session_state.preguntas.iloc[idx]
    correcta = str(pregunta_actual['Correcta']).strip().upper()
    
    # Mejora de contraste: Ponemos la pregunta en un bloque azul (info)
    st.markdown(f"**Tema:** `{pregunta_actual['Tema']}`")
    st.info(f"### {pregunta_actual['Pregunta']}")
    
    # Si aún no hemos respondido, mostramos botones
    if st.session_state.feedback is None:
        opciones = ['A', 'B', 'C', 'D']
        for opt in opciones:
            texto_opcion = f"**{opt})** {pregunta_actual[opt]}"
            if st.button(texto_opcion, key=f"btn_{opt}_{idx}", use_container_width=True):
                responder(opt, correcta)
                st.rerun()
    # Si ya respondimos, mostramos feedback y botón de continuar
    else:
        if mostrar_puntuacion:
            if st.session_state.feedback["tipo"] == "success":
                st.success(st.session_state.feedback["texto"])
            else:
                st.error(st.session_state.feedback["texto"])
        else:
            st.info("✅ Respuesta registrada de forma anónima.")
            
        if st.button("Continuar ➡️", use_container_width=True, type="primary"):
            avanzar_pregunta()
            st.rerun()

    st.divider()
    if st.button("🛑 Terminar test anticipadamente", type="secondary"):
        st.session_state.estado = 'RESULTADOS'
        st.rerun()

# 3. PANTALLA DE RESULTADOS
elif st.session_state.estado == 'RESULTADOS':
    st.header("📊 Resultados del Test 📊")
    st.write(f"**Modo finalizado:** {st.session_state.modo}")
    
    aciertos = st.session_state.aciertos
    fallos = st.session_state.fallos
    total_preguntas = len(st.session_state.preguntas)
    respondidas = aciertos + fallos
    
    st.markdown(f"**Has respondido {respondidas} de {total_preguntas} preguntas.**")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Aciertos ✅", aciertos)
    col2.metric("Fallos ❌", fallos)
    col3.metric("Sin responder ⚪", total_preguntas - respondidas)
    
    if st.session_state.modo == "Examen Normal":
        puntuacion = (aciertos * 2) - (fallos * 0.66)
        
        st.divider()
        
        # Opción para calcular solo sobre lo respondido si salió antes de tiempo
        puntuacion_maxima = total_preguntas * 2
        if respondidas > 0 and respondidas < total_preguntas:
            calcular_proporcional = st.toggle("Ver nota en proporción a las respondidas", value=False)
            if calcular_proporcional:
                puntuacion_maxima = respondidas * 2
                st.caption(f"*(Calculando nota sobre las {respondidas} preguntas contestadas)*")
            else:
                st.caption(f"*(Calculando nota sobre el total de {total_preguntas} preguntas)*")
        
        st.subheader(f"NOTA FINAL: {puntuacion:.2f} / {puntuacion_maxima:.2f}")
        
        # Calcular y mostrar la nota sobre 10 (mínimo 0)
        nota_sobre_10 = max(0.0, (puntuacion / puntuacion_maxima) * 10) if puntuacion_maxima > 0 else 0.0
        st.markdown(f"### 🎯 Nota sobre 10: **{nota_sobre_10:.2f} / 10.0**")
        
        if puntuacion >= (puntuacion_maxima / 2) and puntuacion_maxima > 0:
            st.balloons()
            st.success("¡Enhorabuena! Has aprobado.")
        else:
            st.warning("No has superado el examen o la nota no es suficiente. ¡Sigue repasando!")
            
    st.divider()
    if st.button("Volver al Menú Principal", use_container_width=True, type="primary"):
        volver_al_menu()
        st.rerun()
