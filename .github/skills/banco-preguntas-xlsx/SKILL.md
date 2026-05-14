---
name: banco-preguntas-xlsx
description: 'Audita, sanea y reequilibra un banco de preguntas tipo test en Excel (.xlsx) con columnas Tema/Pregunta/A/B/C/D/Correcta. Úsalo para detectar opciones sin sentido o demasiado largas, duplicados, sesgo A/B/C/D y para balancear Correcta sin romper el formato.'
argument-hint: 'Ruta del .xlsx a auditar/arreglar (p.ej. preguntas-actualizadas.xlsx)'
user-invocable: true
---

# Banco de preguntas (Excel)

Skill para mejorar la calidad del banco de preguntas y evitar que el agente “se vaya” a texto largo/incoherente.

## Cuándo usar
- Quieres un informe rápido del estado del Excel (sesgo de Correcta, longitudes, duplicados, opciones vacías).
- El agente ha generado preguntas pero algunas quedan demasiado largas o sin sentido.
- Quieres reequilibrar la letra correcta (A/B/C/D) de forma mecánica y segura (solo reordenando opciones).

## Requisitos
- Python con `pandas` y `openpyxl`.

## Procedimiento recomendado
1. Audita el Excel (siempre primero)
   - Ejecuta: `python3 .github/skills/banco-preguntas-xlsx/scripts/audit_xlsx_questions.py RUTA.xlsx`
   - Para trabajar por lotes, exporta las filas problemáticas a CSV:
     - `python3 .github/skills/banco-preguntas-xlsx/scripts/audit_xlsx_questions.py RUTA.xlsx --export-flags flags.csv`
   - Si hay muchos flags de longitud/incoherencia, no sigas generando: primero corrige esas filas.

2. Reequilibra Correcta (opcional)
   - Ejecuta: `python3 .github/skills/banco-preguntas-xlsx/scripts/balance_correcta.py IN.xlsx OUT.xlsx`
   - Esto NO cambia el contenido, solo reordena A/B/C/D y actualiza `Correcta`.

3. Elimina duplicados exactos (opcional)
   - Ejecuta: `python3 .github/skills/banco-preguntas-xlsx/scripts/dedupe_exact_questions.py IN.xlsx OUT.xlsx`

## Guardarraíles (para evitar “texto loco”)
- Trabaja por lotes pequeños (5–10 preguntas nuevas por iteración).
- Después de cada lote, vuelve a ejecutar la auditoría y corrige solo las filas flaggeadas.
- Prioriza corregir flags `ratio_len>=...` y `correcta_delata_por_longitud` (son los que más “cantan”).
- Si un lote genera varias opciones demasiado largas o incoherentes, descártalo y regenera con restricciones más estrictas.

## Scripts
- [Auditoría](./scripts/audit_xlsx_questions.py)
- [Balanceo de Correcta](./scripts/balance_correcta.py)
- [Deduplicación exacta](./scripts/dedupe_exact_questions.py)
