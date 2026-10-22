#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Heuristica y Optimizacion - Practica 1, Parte 1

1. Lee el fichero de entrada (l en la 1a linea, prioridades en la 2a).
2. Genera el fichero .dat indicado como segundo argumento (no se borra).
3. Invoca glpsol con parte-1.mod y el .dat generado.
4. Muestra en pantalla: <num. variables> <num. restricciones> <objetivo>
5. Escribe la disposicion optima de forma grafica en un fichero de salida con el mismo nombre que el .dat y extension .out
"""

import os
import re
import subprocess
import sys
import tempfile

DIR_SCRIPT = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(DIR_SCRIPT, "parte-1.mod")


def resolver_ruta(ruta):
    "Si la ruta no contiene directorio, toma el del script."
    if os.path.dirname(ruta) == "":
        return os.path.join(DIR_SCRIPT, ruta)
    return ruta


def error(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def leer_entrada(ruta):
    "Devuelve (l, lista de prioridades)."
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            lineas = [ln.split() for ln in f if ln.strip()]
    except OSError as e:
        error(f"no se puede leer '{ruta}': {e}")

    if len(lineas) < 2:
        error("el fichero de entrada debe tener 2 lineas (l y prioridades)")
    try:
        l = int(lineas[0][0])
        prioridades = [int(v) for v in lineas[1]]
    except (ValueError, IndexError):
        error("el fichero de entrada contiene valores no enteros")

    if l < 1:
        error("el lado del pallet debe ser >= 1")
    if len(prioridades) != l * l:
        error(f"se esperaban {l * l} prioridades (n = l^2) "
              f"y se han leido {len(prioridades)}")
    if any(p < 1 for p in prioridades):
        error("las prioridades deben ser enteros >= 1")
    return l, prioridades


def escribir_dat(ruta, l, prioridades):
    "Genera el fichero de datos en formato MathProg."
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("data;\n\n")
        f.write(f"param l := {l};\n\n")
        f.write("param p :=\n")
        for c, p in enumerate(prioridades, start=1):
            f.write(f"  {c} {p}\n")
        f.write(";\n\nend;\n")


def ejecutar_glpk(ruta_dat):
    "Invoca glpsol y devuelve (n_vars, n_restr, objetivo, asignacion)."
    with tempfile.TemporaryDirectory() as tmp:
        f_salida = os.path.join(tmp, "glpk.out")      # informe de glpsol
        f_display = os.path.join(tmp, "glpk.disp")    # printf del modelo
        cmd = ["glpsol", "--model", MODELO, "--data", ruta_dat,
               "--output", f_salida, "--display", f_display]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            error("no se encuentra 'glpsol' (GLPK) en el PATH")
        if proc.returncode != 0:
            error("glpsol ha fallado:\n" + proc.stdout + proc.stderr)

        with open(f_salida, encoding="utf-8") as f:
            informe = f.read()
        with open(f_display, encoding="utf-8") as f:
            display = f.read()

    if "INTEGER UNDEFINED" in informe or "INTEGER EMPTY" in informe:
        error("el problema no tiene solucion factible")

    # 'Rows' incluye la fila de la funcion objetivo -> se resta 1
    filas = int(re.search(r"^Rows:\s+(\d+)", informe, re.M).group(1))
    columnas = int(re.search(r"^Columns:\s+(\d+)", informe, re.M).group(1))
    n_restricciones = filas - 1
    n_variables = columnas

    objetivo = None
    asignacion = {}                         # (i, j) -> caja c
    for linea in display.splitlines():
        partes = linea.split()
        if not partes:
            continue
        if partes[0] == "OBJ":
            objetivo = float(partes[1])
        elif partes[0] == "SOL":
            c, i, j = map(int, partes[1:4])
            asignacion[(i, j)] = c
    if objetivo is None:
        error("no se ha podido leer el valor de la funcion objetivo")
    return n_variables, n_restricciones, objetivo, asignacion


def escribir_solucion(ruta, l, prioridades, objetivo, asignacion):
    "Dibuja el pallet (vista cenital). Fila l arriba, junto al acceso."
    ancho = max(7, max(len(str(p)) for p in prioridades) + 2)
    sep = "+" + "+".join(["-" * ancho] * l) + "+"
    margen = " " * 9

    lineas = []
    lineas.append(f"Pallet de lado l = {l}  (n = {l * l} cajas)")
    lineas.append(f"Coste medio optimo = {objetivo:.2f}")
    lineas.append("")
    lineas.append(margen + "PUNTO DE ACCESO".center(len(sep)))
    lineas.append(margen + "v".center(len(sep)))
    cab = "".join(f"Col {j}".center(ancho + 1) for j in range(1, l + 1))
    lineas.append(margen + " " + cab)
    lineas.append(margen + sep)
    for i in range(l, 0, -1):
        celdas = [str(prioridades[asignacion[(i, j)] - 1]).center(ancho)
                  for j in range(1, l + 1)]
        lineas.append(f"Fila {i:<3} " + "|" + "|".join(celdas) + "|")
        lineas.append(margen + sep)
    lineas.append("")
    lineas.append("Cada celda muestra la prioridad de la caja (1 = maxima).")
    lineas.append("")
    lineas.append("Detalle (fila, columna) -> caja [prioridad] : coste")
    for i in range(l, 0, -1):
        for j in range(1, l + 1):
            c = asignacion[(i, j)]
            coste = sum(prioridades[asignacion[(k, j)] - 1]
                        for k in range(i + 1, l + 1))
            lineas.append(f"  ({i},{j}) -> caja {c} [p={prioridades[c - 1]}]"
                          f" : {coste}")

    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")


def main():
    if len(sys.argv) != 3:
        print(f"Uso: {sys.argv[0]} <fichero-entrada> <fichero-salida.dat>",
              file=sys.stderr)
        sys.exit(1)

    ruta_in = resolver_ruta(sys.argv[1])
    ruta_dat = resolver_ruta(sys.argv[2])
    raiz, _ = os.path.splitext(ruta_dat)
    ruta_out = raiz + ".out"

    l, prioridades = leer_entrada(ruta_in)
    escribir_dat(ruta_dat, l, prioridades)
    n_vars, n_restr, obj, asig = ejecutar_glpk(ruta_dat)

    print(f"{n_vars} {n_restr} {obj:.2f}")
    escribir_solucion(ruta_out, l, prioridades, obj, asig)


if __name__ == "__main__":
    main()
