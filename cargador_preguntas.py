"""
Módulo para cargar preguntas desde diferentes formatos:
- Excel (.xlsx) con columnas: Tema, Pregunta, A, B, C, D, Correcta
- JSON con estructura: questions[] con options[] (id, text, isCorrect, value)
"""

import json
import pandas as pd
from pathlib import Path
from typing import Optional


def cargar_json_preguntas(ruta_archivo: str) -> Optional[pd.DataFrame]:
    """
    Carga preguntas desde un archivo JSON con la estructura:
    {
      "questions": [
        {
          "id": "q1",
          "text": "Pregunta?",
          "options": [
            {"id": "o1", "text": "Opción A", "isCorrect": false},
            ...
          ]
        }
      ]
    }
    
    Retorna un DataFrame con columnas: Tema, Pregunta, A, B, C, D, Correcta
    """
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró '{ruta_archivo}'.")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error: El archivo JSON '{ruta_archivo}' no tiene un formato válido.")
        return None

    preguntas = []
    
    # Extraer título/tema del documento JSON (si existe)
    tema_global = data.get("title", "") or data.get("description", "")
    
    questions = data.get("questions", [])
    
    for pregunta_obj in questions:
        texto_pregunta = pregunta_obj.get("text", "")
        options = pregunta_obj.get("options", [])
        
        # Asegurarse de que hay exactamente 4 opciones
        if len(options) < 4:
            print(f"⚠️ Advertencia: Pregunta '{texto_pregunta[:50]}...' tiene menos de 4 opciones. Se omite.")
            continue
        
        # Limitar a máximo 4 opciones
        options = options[:4]
        
        # Encontrar la respuesta correcta
        respuesta_correcta = None
        for idx, option in enumerate(options):
            if option.get("isCorrect", False):
                respuesta_correcta = chr(65 + idx)  # Convertir índice (0,1,2,3) a (A,B,C,D)
                break
        
        if respuesta_correcta is None:
            print(f"⚠️ Advertencia: Pregunta '{texto_pregunta[:50]}...' no tiene respuesta correcta. Se omite.")
            continue
        
        # Construir fila del DataFrame
        fila = {
            "Tema": tema_global or pregunta_obj.get("theme", "General"),
            "Pregunta": texto_pregunta,
            "A": options[0].get("text", ""),
            "B": options[1].get("text", ""),
            "C": options[2].get("text", ""),
            "D": options[3].get("text", ""),
            "Correcta": respuesta_correcta
        }
        
        preguntas.append(fila)
    
    if not preguntas:
        print(f"❌ Error: No se pudieron extraer preguntas válidas del archivo JSON.")
        return None
    
    df = pd.DataFrame(preguntas)
    print(f"✅ Se cargaron {len(df)} preguntas desde {ruta_archivo}")
    return df


def cargar_excel(ruta_archivo: str) -> Optional[pd.DataFrame]:
    """
    Carga preguntas desde un archivo Excel (.xlsx).
    
    Retorna un DataFrame con columnas: Tema, Pregunta, A, B, C, D, Correcta
    """
    try:
        df = pd.read_excel(ruta_archivo)
        print(f"✅ Se cargaron {len(df)} preguntas desde {ruta_archivo}")
        return df
    except FileNotFoundError:
        print(f"❌ Error: No se encontró '{ruta_archivo}'.")
        return None
    except Exception as e:
        print(f"❌ Error al leer Excel: {e}")
        return None


def cargar_preguntas(ruta_archivo: str) -> Optional[pd.DataFrame]:
    """
    Carga preguntas automáticamente detectando el formato por extensión.
    
    Soporta:
    - .xlsx -> Excel
    - .json -> JSON con estructura de preguntas
    
    Retorna un DataFrame con columnas: Tema, Pregunta, A, B, C, D, Correcta
    """
    ruta = Path(ruta_archivo)
    
    if ruta.suffix.lower() == ".json":
        return cargar_json_preguntas(ruta_archivo)
    elif ruta.suffix.lower() == ".xlsx":
        return cargar_excel(ruta_archivo)
    else:
        print(f"❌ Error: Formato no soportado '{ruta.suffix}'. Use .xlsx o .json")
        return None


def listar_archivos_soportados() -> dict:
    """
    Lista todos los archivos Excel (.xlsx) y JSON (.json) en el directorio actual
    y en la carpeta 'examenes ipo' (si existe).
    
    Retorna un diccionario con estructura:
    {
        "excel": ["archivo1.xlsx", "archivo2.xlsx"],
        "json": ["preguntas1.json", "preguntas2.json"],
        "todos": ["archivo1.xlsx", "preguntas1.json", ...]
    }
    """
    ruta_actual = Path(".")
    ruta_examenes = Path("examenes ipo")
    
    excels = sorted([p.name for p in ruta_actual.glob("*.xlsx")])
    jsons = sorted([p.name for p in ruta_actual.glob("*.json")])
    
    # Buscar archivos en subcarpeta "examenes ipo"
    jsons_subcarpeta = []
    if ruta_examenes.exists():
        jsons_subcarpeta = sorted([p.name for p in ruta_examenes.glob("*.json")])
        # Añadir prefijo de ruta relativa
        jsons_subcarpeta = [f"examenes ipo/{nombre}" for nombre in jsons_subcarpeta]
    
    # Excluir sim_config.json de la lista (es de configuración, no de preguntas)
    jsons = [j for j in jsons if j != "sim_config.json"]
    
    todos = sorted(excels + jsons + jsons_subcarpeta)
    
    return {
        "excel": excels,
        "json": jsons,
        "json_subcarpeta": jsons_subcarpeta,
        "todos": todos
    }
