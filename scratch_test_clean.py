# -*- coding: utf-8 -*-
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


CLAUSE = r'(?:Amazon(?:\s*\+\s*fabricante)?,\s*confianza\s+\w+|confirmado(?:\s+(?:por|en)\s+[^,)]+)?|resuelto manualmente|fabricante_oficial[^)]*)'


def limpiar_procedencia(v):
    if not v:
        return v
    # Parentesis ENTERO que es solo 1+ clausulas de procedencia (unidas por coma)
    v = re.sub(rf'\s*\(\s*{CLAUSE}(?:\s*,\s*{CLAUSE})*\s*\)', '', v, flags=re.IGNORECASE)
    # Clausula de procedencia al FINAL de un parentesis con mas contenido
    v = re.sub(rf',\s*{CLAUSE}(?=\s*\))', '', v, flags=re.IGNORECASE)
    # Clausula de procedencia al INICIO de un parentesis con mas contenido
    v = re.sub(rf'\(\s*{CLAUSE}\s*,\s*', '(', v, flags=re.IGNORECASE)
    # limpieza de restos (parentesis vacios, comas colgantes, espacios dobles)
    for _ in range(2):
        v = re.sub(r'\(\s*\)', '', v)
        v = re.sub(r'\(\s*,\s*', '(', v)
        v = re.sub(r',\s*\)', ')', v)
    v = re.sub(r'\s+\)', ')', v)
    v = re.sub(r'\s{2,}', ' ', v).strip()
    return v


casos = [
    "Grupo 0+/1/2/3 (Amazon, confianza media)",
    "Grupo 2/3 (Amazon + fabricante, confianza alta)",
    "Arnés de 3 puntos (confirmado por fabricante)",
    "No (confirmado por fabricante, resuelto manualmente)",
    "Sí (confirmado por fabricante)",
    "Sí (Sistema L.S.P., confirmado en Amazon)",
    "Sí (lavable a máquina 30°C, confirmado en Amazon)",
    "No — 180° (confirmado, no 360° completo)",
    "Compatible (adaptador para cochecitos Cybex/gb, confirmado en ficha)",
    "Compatible con numerosos cochecitos (confirmado por fabricante)",
    "Ambas (RWF 40-105cm + FWF 76-150cm, confirmado por fabricante)",
    "Sí — como refuerzo de estabilidad junto al cinturón (confirmado por fabricante)",
]
for c in casos:
    print(repr(c))
    print("  ->", repr(limpiar_procedencia(c)))
    print()
