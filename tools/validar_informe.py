#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar_informe.py — Validador y Linter Pericial Académico (Antigravity)
Verifica que un borrador técnico (informe.md) cumpla estrictamente todas las reglas
de redacción, estructura, extensión (mínimo global de 2.000 palabras y máximo configurable)
y calidad antes de autorizar su traspaso a Word (.docx).
"""

import sys
import os
import re
import argparse

# Lista de palabras o patrones grandilocuentes estrictamente prohibidos
PALABRAS_PROHIBIDAS = [
    (r"\bat[oó]mic[ao]s?\b", "atómica / atómico (usar: directo, en bloque, completo, secuencial)"),
    (r"\briguros[ao]s?\b", "riguroso / rigurosa (usar: detallado, metódico, preciso, exhaustivo)"),
    (r"\brigurosamente\b", "rigurosamente (usar: con precisión, conforme a la norma, metódicamente)"),
    (r"\bmicrosc[oó]pic[ao]s?\b", "microscópico / microscópica (usar: en profundidad, a bajo nivel, detallado)"),
    (r"\binquebrantables?\b", "inquebrantable (usar: obligatorio, formal, estándar, establecido)"),
    (r"\bfehacientes?\b", "fehaciente (usar: comprobable, demostrado, verificado)"),
    (r"\bfehacientemente\b", "fehacientemente (usar: de forma comprobable, demostradamente)"),
    (r"\birrestrict[ao]s?\b", "irrestricto / irrestricta (usar: total, completo, estricto)"),
    (r"\birrestrictamente\b", "irrestrictamente (usar: en su totalidad, estrictamente)"),
    (r"\bsine\s+qua\s+non\b", "sine qua non (usar: indispensable, necesario, mandatorio)"),
    (r"\btaxativ[ao]s?\b", "taxativo / taxativa (usar: específico, delimitado, estricto)"),
    (r"\btaxativamente\b", "taxativamente (usar: específicamente, expresamente)"),
    (r"\bp[aá]rrafos?\s+cardinales?\b", "párrafos cardinales (usar: párrafos principales, puntos clave)"),
    (r"\bsecci[oó]n\s+medular\b", "sección medular (usar: núcleo del análisis, sección central)"),
    (r"\bflagrantes?\b", "flagrante (usar: notorio, manifiesto, evidente)"),
    (r"\bcoartadas?\s+temporales?\b", "coartada temporal (usar: marcas temporales alteradas, falsificación cronológica)"),
]

# Frases clichés comunes de LLMs prohibidas
CLICHES_LLM = [
    (r"\bes\s+importante\s+destacar\b", "es importante destacar"),
    (r"\bcabe\s+mencionar\b", "cabe mencionar"),
    (r"\ben\s+el\s+mundo\s+actual\b", "en el mundo actual"),
    (r"\ben\s+conclusi[oó]n\s+podemos\s+decir\b", "en conclusión podemos decir"),
]


def contar_palabras(texto: str) -> int:
    """Cuenta palabras en el texto."""
    palabras = re.findall(r"\b[a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ_-]+\b", texto)
    return len(palabras)


def validar_informe(ruta_md: str, min_palabras_total: int = 2000, max_palabras_total: int = None) -> bool:
    if not os.path.exists(ruta_md):
        print(f"[ERROR] No se encontró el archivo: {ruta_md}")
        return False

    with open(ruta_md, "r", encoding="utf-8") as f:
        contenido = f.read()

    errores = []
    advertencias = []

    print("=" * 80)
    print(f"AUDITORÍA PERICIAL DE CALIDAD — {os.path.basename(ruta_md)}")
    print(f"Ruta: {os.path.abspath(ruta_md)}")
    print("=" * 80)

    # 1. Total general de palabras (Mínimo y Máximo del informe completo)
    total_palabras = contar_palabras(contenido)
    print(f"\n[1] Recuento total de palabras del informe completo: {total_palabras} palabras")
    
    if total_palabras < min_palabras_total:
        errores.append(f"El informe completo contiene {total_palabras} palabras, inferior al mínimo exigido de {min_palabras_total} palabras.")
        print(f"  [FALLO] Total de palabras insuficiente (Mínimo requerido: {min_palabras_total}).")
    else:
        print(f"  [OK] Extensión mínima cumplida (Mínimo: {min_palabras_total} palabras).")

    if max_palabras_total is not None:
        if total_palabras > max_palabras_total:
            errores.append(f"El informe completo contiene {total_palabras} palabras, excediendo el límite máximo acordado de {max_palabras_total} palabras.")
            print(f"  [FALLO] Total de palabras excede el límite máximo fijado ({max_palabras_total} palabras).")
        else:
            print(f"  [OK] Dentro del límite máximo fijado ({max_palabras_total} palabras).")
    else:
        print("  [INFO] No se ha establecido un límite máximo de palabras para esta auditoría.")

    # 2. Verificación de índice general (PROHIBIDO salvo solicitud expresa)
    if re.search(r"^#+\s*(?:índice|tabla\s+de\s+contenido)", contenido, re.IGNORECASE | re.MULTILINE):
        errores.append("Se detectó sección de 'Índice General' o 'Tabla de Contenidos'. La directriz prohíbe índices.")
    else:
        print("  [OK] Ausencia de Índice General verificada.")

    # 3. Detección de palabras pomposas prohibidas
    print("\n[2] Verificación de lenguaje y términos prohibidos:")
    palabras_encontradas = 0
    for patron, explicacion in PALABRAS_PROHIBIDAS:
        matches = list(re.finditer(patron, contenido, re.IGNORECASE))
        if matches:
            palabras_encontradas += len(matches)
            for m in matches:
                start = max(0, m.start() - 30)
                end = min(len(contenido), m.end() + 30)
                snippet = contenido[start:end].replace("\n", " ")
                errores.append(f"Término prohibido encontrado: '{m.group(0)}' -> {explicacion}. Contexto: '...{snippet}...'")

    for patron, explicacion in CLICHES_LLM:
        matches = list(re.finditer(patron, contenido, re.IGNORECASE))
        if matches:
            for m in matches:
                errores.append(f"Frase cliché de LLM detectada: '{m.group(0)}' -> {explicacion}.")

    if palabras_encontradas == 0:
        print("  [OK] No se detectaron palabras grandilocuentes ni clichés prohibidos.")
    else:
        print(f"  [FALLO] Se detectaron {palabras_encontradas} ocurrencias de términos prohibidos.")

    # 4. Desglose informativo por sección
    print("\n[3] Desglose de contenido por sección:")
    secciones = re.split(r"(?m)^(?=#{2,3}\s+)", contenido)
    for sec in secciones:
        m_titulo = re.match(r"^#{2,3}\s+(.+)$", sec.strip(), re.MULTILINE)
        if not m_titulo:
            continue
        titulo = m_titulo.group(1).strip()
        palabras_sec = contar_palabras(sec)
        print(f"  - {titulo[:65]}: {palabras_sec} palabras")

    # 5. Verificación de marcadores de evidencias visuales diferidas y sus guías
    print("\n[4] Verificación de marcadores de evidencias visuales y guías prácticas:")
    marcadores = list(re.finditer(r"\[INSERTAR\s+CAPTURA\s+DE\s+PANTALLA:[^\]]+\]", contenido))
    print(f"  Se encontraron {len(marcadores)} marcadores de captura reservados para el estudiante.")
    if len(marcadores) == 0:
        advertencias.append("No se detectaron marcadores '[INSERTAR CAPTURA DE PANTALLA: ...]'.")
    else:
        sin_guia = 0
        for idx, m in enumerate(marcadores, 1):
            start = m.end()
            proximo_bloque = contenido[start:start+400]
            tiene_guia = bool(re.search(r"(?:Guía\s+para\s+la\s+captura|Guía\s+de\s+captura|Entorno\s*/\s*Herramienta)", proximo_bloque, re.IGNORECASE))
            estado_guia = "[Con Guía]" if tiene_guia else "[SIN GUÍA]"
            print(f"    {idx}. {estado_guia} {m.group(0)[:75]}...")
            if not tiene_guia:
                sin_guia += 1
                advertencias.append(f"El marcador '{m.group(0)[:60]}...' no posee una guía práctica explicativa inmediatamente después.")
        if sin_guia == 0:
            print("  [OK] Todos los marcadores de captura cuentan con su guía práctica correspondiente.")

    # 6. Verificación de Citas APA 7
    print("\n[5] Verificación de Citas APA 7 en el texto:")
    citas = re.findall(r"\([A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúÁÉÍÓÚñÑ\s\.,&]+,\s*(?:19|20)\d{2}[a-z]?(?:,\s*p+\.\s*\d+)?\)", contenido)
    print(f"  Se detectaron {len(citas)} citas parentéticas potenciales.")
    if len(citas) < 5:
        advertencias.append(f"Se detectaron pocas citas parentéticas ({len(citas)}). Comprobar fundamentación APA 7.")
    else:
        print("  [OK] Nivel de fundamentación con citas parentéticas adecuado.")

    # 7. Verificación de sección final de Referencias
    if re.search(r"^#+\s*(?:\d+[\.\)]\s*)?(?:referencias(?:\s+bibliográficas)?|bibliografía)", contenido, re.IGNORECASE | re.MULTILINE):
        print("  [OK] Sección de Referencias bibliográficas presente.")
    else:
        errores.append("No se encontró la sección final obligatoria de 'Referencias bibliográficas'.")

    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN DE AUDITORÍA")
    print("=" * 80)

    if advertencias:
        print(f"\nADVERTENCIAS ({len(advertencias)}):")
        for adv in advertencias:
            print(f"  - [AVISO] {adv}")

    if errores:
        print(f"\nERRORES DETECTADOS ({len(errores)}):")
        for err in errores:
            print(f"  - [FALLO] {err}")
        print("\nResultado: RECHAZADO. Corrija los errores antes de proceder a la generación en Word (.docx).")
        return False
    else:
        print("\nResultado: APROBADO. El informe cumple todos los estándares institucionales de Antigravity.")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validador y Linter pericial de informes académicos.")
    parser.add_argument("informe", nargs="?", default="informe.md", help="Ruta al archivo Markdown a auditar.")
    parser.add_argument("--min", type=int, default=2000, help="Mínimo de palabras para el informe completo (default: 2000).")
    parser.add_argument("--max", type=int, default=None, help="Límite máximo de palabras para el informe completo (opcional).")
    args = parser.parse_args()

    aprobado = validar_informe(args.informe, min_palabras_total=args.min, max_palabras_total=args.max)
    sys.exit(0 if aprobado else 1)
