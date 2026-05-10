import sys
import subprocess
from pathlib import Path


def instalar_si_falta(libreria, nombre_paquete=None):
    if nombre_paquete is None:
        nombre_paquete = libreria
    try:
        __import__(libreria)
    except ImportError:
        print(f"⏳ Instalando '{nombre_paquete}'...")
        try:
            # Intentar con uv, ya que estás usando este             uv run ExamTetsCS.pyentorno
            subprocess.check_call(["uv", "pip", "install", nombre_paquete])
        except FileNotFoundError:
            # Si no hay uv, recurrir a pip clásico
            subprocess.check_call([sys.executable, "-m", "pip", "install", nombre_paquete])
        print(f"✅ '{nombre_paquete}' instalada.\n")


# --- INSTALACIÓN AUTOMÁTICA ---
instalar_si_falta('pandas')
instalar_si_falta('openpyxl')

import pandas as pd
import random


def cargar_excel(ruta_archivo):
    try:
        return pd.read_excel(ruta_archivo)
    except FileNotFoundError:
        print(f"Error: No se encontró '{ruta_archivo}'.")
        return None


def motor_preguntas(df_preguntas):
    """
    Recibe un grupo de preguntas, hace el test, hace la pausa del ENTER
    y devuelve el total de aciertos y fallos.
    """
    aciertos = 0
    fallos = 0
    total = len(df_preguntas)

    for indice, fila in df_preguntas.iterrows():
        print("\n" + "-" * 40)
        print(f"Tema: {fila['Tema']}")
        print(f"Pregunta: {fila['Pregunta']}")
        print(f"  A) {fila['A']}")
        print(f"  B) {fila['B']}")
        print(f"  C) {fila['C']}")
        print(f"  D) {fila['D']}")

        respuesta_usuario = input("\nTu respuesta (A/B/C/D): ").strip().upper()
        respuesta_correcta = str(fila['Correcta']).strip().upper()

        # Comprobar si es correcta
        if respuesta_usuario == respuesta_correcta:
            print("\n✅ ¡CORRECTO!")
            aciertos += 1
        else:
            print(f"\n❌ INCORRECTO. La respuesta correcta era la: {respuesta_correcta}")
            fallos += 1

        # Pausa obligatoria
        input("Pulsa ENTER para continuar...")

    return aciertos, fallos, total


def menu_principal():
    excels = sorted([p.name for p in Path('.').glob('*.xlsx')])
    if 'preguntas.xlsx' in excels:
        excels.remove('preguntas.xlsx')
        excels.insert(0, 'preguntas.xlsx')

    archivo_excel = 'preguntas.xlsx'
    if excels:
        print("\nArchivos Excel disponibles:")
        for i, f in enumerate(excels, 1):
            print(f" {i}. {f}")
        eleccion = input(
            "\nElige un número (o ENTER para usar 'preguntas.xlsx'): "
        ).strip()
        if eleccion:
            if eleccion.isdigit() and 1 <= int(eleccion) <= len(excels):
                archivo_excel = excels[int(eleccion) - 1]
            elif eleccion in excels:
                archivo_excel = eleccion
            else:
                print("⚠️ Elección no válida. Usando 'preguntas.xlsx'.")

    df = cargar_excel(archivo_excel)

    if df is None:
        input("Pulsa ENTER para salir...")
        return

    while True:
        print("\n" + "=" * 40)
        print("      📚 SIMULADOR DE EXÁMENES 📚")
        print("=" * 40)
        print("1. Resolver TODAS las preguntas (Mix general)")
        print("2. Examen Normal (50 preguntas | Acierto: +2, Fallo: -0.66)")
        print("3. Examen por Tema (Todas las preguntas de un tema)")
        print("4. Salir")

        opcion = input("\nElige una opción (1-4): ").strip()

        if opcion == '1':
            # Barajamos todas las preguntas usando sample(frac=1)
            preguntas = df.sample(frac=1)
            print(f"\nIniciando modo: TODAS LAS PREGUNTAS ({len(preguntas)} en total)")
            aciertos, fallos, total = motor_preguntas(preguntas)

            print("\n" + "=" * 40)
            print("📊 RESULTADOS: TODAS LAS PREGUNTAS 📊")
            print(f"Aciertos: {aciertos}")
            print(f"Fallos:   {fallos}")
            print("=" * 40)

        elif opcion == '2':
            # Cogemos 50 preguntas (o el máximo que haya si hay menos de 50)
            cantidad = min(50, len(df))
            preguntas = df.sample(n=cantidad)
            print(f"\nIniciando modo: EXAMEN NORMAL ({cantidad} preguntas)")
            aciertos, fallos, total = motor_preguntas(preguntas)

            # Cálculo de nota
            puntuacion = (aciertos * 2) - (fallos * 0.66)
            puntuacion_maxima = total * 2

            print("\n" + "=" * 40)
            print("📊 RESULTADOS: EXAMEN NORMAL 📊")
            print(f"Aciertos (+2):    {aciertos}")
            print(f"Fallos (-0.66):   {fallos}")
            print("-" * 40)
            # Mostramos la nota con 2 decimales
            print(f"NOTA FINAL:       {puntuacion:.2f} / {puntuacion_maxima}")
            print("=" * 40)

        elif opcion == '3':
            # Mostrar temas disponibles para que el usuario elija bien
            temas_disponibles = df['Tema'].unique()
            print("\nTemas disponibles en tu Excel:")
            for t in temas_disponibles:
                print(f" - {t}")

            tema_elegido = input("\nEscribe el nombre del tema que quieres estudiar: ").strip()

            # Filtramos el excel por el tema ignorando mayúsculas/minúsculas
            df_tema = df[df['Tema'].str.lower() == tema_elegido.lower()]

            if df_tema.empty:
                print(f"⚠️ No se ha encontrado el tema '{tema_elegido}'. Revisa cómo lo has escrito.")
                input("Pulsa ENTER para volver al menú...")
                continue

            # Barajamos las preguntas de ese tema
            preguntas = df_tema.sample(frac=1)
            print(f"\nIniciando modo: TEMA '{tema_elegido.upper()}' ({len(preguntas)} preguntas)")
            aciertos, fallos, total = motor_preguntas(preguntas)

            print("\n" + "=" * 40)
            print(f"📊 RESULTADOS: TEMA {tema_elegido.upper()} 📊")
            print(f"Aciertos: {aciertos}")
            print(f"Fallos:   {fallos}")
            print("=" * 40)

        elif opcion == '4':
            print("\n¡Mucha suerte con el estudio! Hasta la próxima.\n")
            break

        else:
            print("\n⚠️ Opción no válida. Por favor, escribe 1, 2, 3 o 4.")


if __name__ == "__main__":
    menu_principal()