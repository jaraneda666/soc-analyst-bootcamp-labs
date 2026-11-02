#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sincronizar_obsidian.py — Automatización de Documentación en Obsidian (Antigravity)
Sincroniza informes de estudio y fichas técnicas hacia Obsidian Vault vía Local REST API with MCP.
Directriz del Estudiante:
- Ruta en Vault: Estudios/IACC/[Nombre-Asignatura]/Semana [N]/
- Formato Dual: Ficha Técnica Ejecutiva + Informe Completo enlazados.
- Ejecución: Al aprobar el borrador Markdown, antes de generar el Word.
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# Garantizar codificación UTF-8 en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

DEFAULT_REST_URL = "http://192.168.1.100:27123"



def cargar_configuracion_env(ruta_env: str = None) -> tuple:
    """Lee OBSIDIAN_REST_URL y OBSIDIAN_API_KEY desde .env o variables de entorno."""
    if ruta_env is None:
        # Buscar .env en el directorio actual o en la raíz del proyecto
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ruta_env = os.path.join(base_dir, ".env")
        if not os.path.exists(ruta_env):
            ruta_env = os.path.join(os.getcwd(), ".env")

    rest_url = os.environ.get("OBSIDIAN_REST_URL", DEFAULT_REST_URL)
    api_key = os.environ.get("OBSIDIAN_API_KEY", "")

    if os.path.exists(ruta_env):
        with open(ruta_env, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith("#") or "=" not in linea:
                    continue
                k, v = linea.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k == "OBSIDIAN_REST_URL" and v:
                    rest_url = v
                elif k == "OBSIDIAN_API_KEY" and v:
                    api_key = v

    rest_url = rest_url.rstrip("/")
    if api_key.startswith("Bearer "):
        api_key = api_key[7:].strip()
    return rest_url, api_key



def test_conexion(rest_url: str, api_key: str) -> dict:
    """Verifica la conectividad y autenticación con Obsidian Local REST API."""
    url = f"{rest_url}/"
    headers = {
        "Accept": "application/json"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            return {"status": "ok", "authenticated": data.get("authenticated", False), "data": data}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            err_json = json.loads(body)
            msg = err_json.get("message", body)
        except Exception:
            msg = body
        return {"status": "error", "code": e.code, "message": msg}
    except Exception as e:
        return {"status": "error", "code": 0, "message": str(e)}


def subir_archivo_vault(rest_url: str, api_key: str, ruta_vault: str, contenido: str) -> bool:
    """Sube o actualiza un archivo en el Vault de Obsidian usando PUT /vault/{filename}."""
    # Codificar la ruta URL preservando los slashes
    partes = [urllib.parse.quote(p) for p in ruta_vault.split("/")]
    url_path = "/".join(partes)
    url = f"{rest_url}/vault/{url_path}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "text/markdown; charset=utf-8"
    }

    req = urllib.request.Request(url, data=contenido.encode("utf-8"), headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 204)
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Error al subir '{ruta_vault}': HTTP {e.code} - {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"[ERROR] Error de conexión al subir '{ruta_vault}': {e}")
        return False


def generar_ficha_tecnica(asignatura: str, semana: str, ruta_informe: str, nombre_informe_obsidian: str) -> str:
    """Genera una nota ejecutiva de síntesis técnica enlazada al informe completo."""
    with open(ruta_informe, "r", encoding="utf-8") as f:
        contenido_md = f.read()

    # Extraer métricas básicas
    palabras = len(re.findall(r"\b\w+\b", contenido_md))
    
    # Extraer título del informe
    m_titulo = re.search(r"^#\s+(.+)$", contenido_md, re.MULTILINE)
    titulo = m_titulo.group(1).strip() if m_titulo else f"Informe Académico {semana}"

    # Extraer proyecto si existe
    m_proy = re.search(r"\*\*Proyecto:\*\*\s*(.+)$", contenido_md, re.MULTILINE)
    proyecto = m_proy.group(1).strip() if m_proy else "Proyecto de Especialidad"

    # Extraer fecha
    m_fecha = re.search(r"\*\*Fecha:\*\*\s*(.+)$", contenido_md, re.MULTILINE)
    fecha_doc = m_fecha.group(1).strip() if m_fecha else datetime.now().strftime("%d-%m-%Y")

    # Extraer normas y estándares citados
    normas = []
    if "ISO/IEC 27001" in contenido_md or "ISO 27001" in contenido_md:
        normas.append("ISO/IEC 27001:2022")
    if "ISO/IEC 27037" in contenido_md:
        normas.append("ISO/IEC 27037:2012")
    if "CIS Benchmark" in contenido_md or "CIS" in contenido_md:
        normas.append("CIS Benchmarks")
    if "NIST" in contenido_md:
        normas.append("NIST SP 800-Series")
    if "MITRE ATT&CK" in contenido_md:
        normas.append("MITRE ATT&CK")
    if "RFC 3227" in contenido_md:
        normas.append("RFC 3227")

    normas_str = ", ".join(normas) if normas else "Estándares Institucionales IACC"

    # Normalizar etiquetas para Obsidian
    tag_asig = re.sub(r"[^\w\s-]", "", asignatura).replace(" ", "_")
    tag_sem = semana.replace(" ", "")

    ficha = f"""---
title: "Ficha Técnica: {titulo}"
asignatura: "{asignatura}"
semana: "{semana}"
proyecto: "{proyecto}"
fecha: "{fecha_doc}"
estudiante: "Security Analyst"
institucion: "Instituto Profesional IACC"
estado: "Aprobado"
palabras_informe: {palabras}
normativas: [{", ".join(f'"{n}"' for n in normas)}]
tags:
  - iacc
  - ciberseguridad
  - {tag_asig}
  - {tag_sem}
---

# 🛡️ Ficha Técnica de Síntesis: {semana}

> **Proyecto:** {proyecto}  
> **Asignatura:** {asignatura}  
> **Estado:** Documento Académico Aprobado  
> **Enlace al documento completo:** [[{nombre_informe_obsidian}|📄 Abrir Informe Completo ({palabras} palabras)]]

---

## 📌 1. Resumen Ejecutivo y Alcance
Esta semana aborda la actividad evaluativa de **{semana}** enfocada en **{titulo}**. La investigación técnica profundiza en la evaluación empírica, bastionado, aseguramiento de infraestructuras y alineación con las directrices institucionales de ciberseguridad.

- **Total de palabras del informe:** {palabras} palabras.
- **Marco normativo aplicado:** {normas_str}.
- **Entregable oficial generado:** `Juan_Araneda_Tarea{re.search(r'\d+', semana).group(0) if re.search(r'\d+', semana) else 'X'}.docx` (exclusivo Word, sin PDF).

---

## 🎯 2. Objetivos y Controles Clave Evaluados
1. **Auditoría e Inocuidad:** Implementación de revisiones no invasivas en modo de solo lectura con mínimo impacto de recursos (CPU < 5%).
2. **Cumplimiento de Estándares:** Validación cruzada de directivas frente a {normas_str}.
3. **Optimización con Inteligencia Artificial:** Análisis determinista de hallazgos mediante modelos RAG a baja temperatura (0.1) para evitar alucinaciones.
4. **Gobernanza y Remediación:** Diseño de políticas declarativas (Ansible/DSC) y protocolos formales de gestión de excepciones.

---

## 💻 3. Guía Rápida de Comandos y Evidencias de Laboratorio
Los procedimientos prácticos asociados a esta entrega se resumen a continuación:

```bash
# Comandos clave de validación y simulación de auditoría
# 1. Ejecución del orquestador analítico
python orchestrator.py --target <IP_SERVIDOR> --benchmark cis --output json

# 2. Simulación de playbooks declarativos sin impactar producción
ansible-playbook -i hosts hardening.yml --syntax-check
ansible-playbook -i hosts hardening.yml --check
```

*(Para la guía pericial paso a paso de cada una de las capturas de pantalla, consulta el [[{nombre_informe_obsidian}#guía-para-la-captura|Informe Completo]]).)*

---

## 📚 4. Referencias Centrales
Para consultar el detalle bibliográfico en formato APA 7 y el desarrollo exhaustivo de cada consulta evaluativa, dirígete a la nota completa:
➡️ **[[{nombre_informe_obsidian}|Acceder a la Memoria e Informe Completo de la {semana}]]**
"""
    return ficha


def preparar_informe_para_obsidian(ruta_informe: str, nombre_ficha: str, asignatura: str, semana: str) -> str:
    """Prepara el informe completo con frontmatter para Obsidian y enlace de retorno."""
    with open(ruta_informe, "r", encoding="utf-8") as f:
        contenido = f.read()

    tag_asig = re.sub(r"[^\w\s-]", "", asignatura).replace(" ", "_")
    tag_sem = semana.replace(" ", "")

    cabecera = f"""---
title: "Informe Completo - {semana} ({asignatura})"
asignatura: "{asignatura}"
semana: "{semana}"
tags:
  - informe-completo
  - {tag_asig}
  - {tag_sem}
---

> ⬅️ **Navegación:** [[{nombre_ficha}|Volver a la Ficha Técnica de Síntesis]]

---

"""
    return cabecera + contenido


def sincronizar_semana(asignatura: str, semana: str, ruta_informe: str, ruta_env: str = None) -> bool:
    """Sincroniza la ficha técnica y el informe completo hacia el Vault de Obsidian."""
    print("=" * 80)
    print("SINCRONIZADOR AUTOMÁTICO DE ESTUDIOS HACIA OBSIDIAN VAULT (ANTIGRAVITY)")
    print("=" * 80)
    print(f"Asignatura: {asignatura}")
    print(f"Semana:     {semana}")
    print(f"Informe:    {ruta_informe}")

    rest_url, api_key = cargar_configuracion_env(ruta_env)
    print(f"Endpoint:   {rest_url}")

    if not api_key or api_key == "PEGA_AQUI_TU_API_KEY":
        print("\n[AVISO REQUERIDO] No se ha configurado la API Key de Obsidian en el archivo .env.")
        print("Por favor, abre el archivo .env y asigna tu OBSIDIAN_API_KEY:")
        print("  1. En Obsidian, ve a Ajustes -> Opciones de complementos -> Local REST API with MCP.")
        print("  2. Copia tu API Key.")
        print("  3. Pégala en el archivo '.env' en la variable OBSIDIAN_API_KEY=...\n")
        return False

    # Probar conexión
    test = test_conexion(rest_url, api_key)
    if test["status"] != "ok":
        print(f"\n[ERROR] No fue posible conectar con Obsidian Local REST API en {rest_url}:")
        print(f"  Detalle: {test.get('message', 'Error desconocido')}")
        print("Asegúrate de que Obsidian esté abierto y el complemento 'Local REST API with MCP' activo.\n")
        return False

    if not test.get("authenticated", False):
        print(f"\n[ERROR] Conexión establecida pero la API Key es inválida o no fue autorizada por Obsidian.")
        print(f"  Detalle: {test.get('message', 'Error de autenticación')}\n")
        return False

    print("[OK] Conexión y autenticación con Obsidian REST API confirmadas.")

    # Rutas dentro del Vault de Obsidian:
    # Directriz: Estudios/IACC/[Nombre-Asignatura]/Semana [N]/
    num_sem = re.search(r"\d+", semana).group(0) if re.search(r"\d+", semana) else "X"
    carpeta_vault = f"Estudios/IACC/{asignatura}/{semana}"

    nombre_ficha = f"Ficha_Tecnica_Semana_{num_sem}"
    nombre_informe = f"Informe_Completo_Semana_{num_sem}"

    ruta_vault_ficha = f"{carpeta_vault}/{nombre_ficha}.md"
    ruta_vault_informe = f"{carpeta_vault}/{nombre_informe}.md"

    # Generar contenidos
    contenido_ficha = generar_ficha_tecnica(asignatura, semana, ruta_informe, nombre_informe)
    contenido_informe = preparar_informe_para_obsidian(ruta_informe, nombre_ficha, asignatura, semana)

    # Subir al Vault
    print(f"\nSubiendo notas al Vault en: '{carpeta_vault}'...")

    ok_ficha = subir_archivo_vault(rest_url, api_key, ruta_vault_ficha, contenido_ficha)
    if ok_ficha:
        print(f"  [OK] Ficha Técnica creada: '{ruta_vault_ficha}'")
    else:
        print(f"  [FALLO] No se pudo crear la Ficha Técnica: '{ruta_vault_ficha}'")

    ok_informe = subir_archivo_vault(rest_url, api_key, ruta_vault_informe, contenido_informe)
    if ok_informe:
        print(f"  [OK] Informe Completo creado: '{ruta_vault_informe}'")
    else:
        print(f"  [FALLO] No se pudo crear el Informe Completo: '{ruta_vault_informe}'")

    if ok_ficha and ok_informe:
        print("\n" + "=" * 80)
        print("DOCUMENTACION EN OBSIDIAN COMPLETADA EXITOSAMENTE")
        print(f"Visualiza las notas en tu Obsidian en la carpeta:\n  [VAULT] {carpeta_vault}")
        print("=" * 80)
        return True

    return False


def main():
    parser = argparse.ArgumentParser(description="Sincronizador automático de informes académicos a Obsidian Vault.")
    parser.add_argument("--asignatura", default="Taller de Integracion en Seguridad de Datos", help="Nombre del ramo.")
    parser.add_argument("--semana", default="Semana 7", help="Semana académica (ej: Semana 7).")
    parser.add_argument("--informe", default="informe.md", help="Ruta al archivo Markdown del informe.")
    parser.add_argument("--env-file", default=None, help="Ruta al archivo .env.")
    parser.add_argument("--test", action="store_true", help="Solo probar conexión y autenticación con Obsidian.")
    args = parser.parse_args()

    if args.test:
        rest_url, api_key = cargar_configuracion_env(args.env_file)
        print(f"Probando conexión con {rest_url}...")
        res = test_conexion(rest_url, api_key)
        print(f"Resultado: {res}")
        sys.exit(0 if res.get("authenticated") else 1)

    if not os.path.exists(args.informe):
        print(f"[ERROR] No se encuentra el archivo de informe: {args.informe}")
        sys.exit(1)

    exito = sincronizar_semana(args.asignatura, args.semana, args.informe, args.env_file)
    sys.exit(0 if exito else 1)


if __name__ == "__main__":
    main()
