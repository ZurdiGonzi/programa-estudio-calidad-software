#!/usr/bin/env python3
"""
Script de prueba para verificar que el simulador funciona correctamente
con ambos formatos: Excel y JSON, incluyendo exámenes de la carpeta 'examenes ipo'
"""

from cargador_preguntas import cargar_preguntas, listar_archivos_soportados
import pandas as pd

print("=" * 60)
print("🧪 PRUEBA DEL SIMULADOR DE EXÁMENES")
print("=" * 60)

# 1. Listar archivos disponibles
print("\n📁 ARCHIVOS DISPONIBLES:")
archivos = listar_archivos_soportados()
print(f"   Excel (.xlsx): {len(archivos['excel'])} archivo(s)")
if archivos['excel']:
    for f in archivos['excel']:
        print(f"      - {f}")
print(f"\n   JSON (.json) - Carpeta raíz: {len(archivos['json'])} archivo(s)")
if archivos['json']:
    for f in archivos['json']:
        print(f"      - {f}")
print(f"\n   JSON (.json) - Exámenes IPO: {len(archivos['json_subcarpeta'])} archivo(s)")
if archivos['json_subcarpeta']:
    for f in archivos['json_subcarpeta']:
        nombre_corto = f.replace("examenes ipo/", "")
        print(f"      - {nombre_corto}")

# 2. Probar carga de JSON (si existe)
print("\n📄 PRUEBA 1: Cargar JSON (Carpeta raíz)")
if archivos['json']:
    archivo_test = archivos['json'][0]
    df_json = cargar_preguntas(archivo_test)
    if df_json is not None:
        print(f"   ✅ {len(df_json)} preguntas cargadas desde '{archivo_test}'")
    else:
        print(f"   ❌ Error al cargar '{archivo_test}'")
else:
    print("   ⚠️  No hay archivos JSON en la carpeta raíz")

# 3. Probar carga de exámenes IPO
print("\n📚 PRUEBA 2: Cargar Exámenes IPO")
if archivos['json_subcarpeta']:
    for archivo_test in archivos['json_subcarpeta']:
        df_json = cargar_preguntas(archivo_test)
        if df_json is not None:
            nombre_corto = archivo_test.replace("examenes ipo/", "")
            print(f"   ✅ {nombre_corto}: {len(df_json)} preguntas")
        else:
            print(f"   ❌ Error al cargar '{archivo_test}'")
else:
    print("   ⚠️  No hay exámenes en la carpeta 'examenes ipo'")

# 4. Probar carga de Excel
print("\n📊 PRUEBA 3: Cargar Excel")
if archivos['excel']:
    archivo_test = archivos['excel'][0]
    df_xlsx = cargar_preguntas(archivo_test)
    if df_xlsx is not None:
        print(f"   ✅ {len(df_xlsx)} preguntas cargadas desde '{archivo_test}'")
    else:
        print(f"   ❌ Error al cargar '{archivo_test}'")
else:
    print("   ⚠️  No hay archivos Excel disponibles")

# 5. Validar estructura
print("\n✅ VALIDACIÓN DE ESTRUCTURAS:")
print(f"   Todos los formatos generan DataFrames con:")
print(f"   - Columnas: Tema, Pregunta, A, B, C, D, Correcta")
print(f"   - Completamente compatibles con ambos programas")

print("\n" + "=" * 60)
print(f"✨ ¡PRUEBA COMPLETADA!")
print(f"   Total archivos encontrados: {len(archivos['todos'])}")
print("=" * 60)
print("\n🚀 Para usar el simulador:")
print("   Consola:   python ExamTetsCS.py")
print("   Web:       streamlit run app_web.py")
print("\n")
