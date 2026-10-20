#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Heuristica y Optimizacion - Practica 1, Parte 2
Uso:  ./sol-2.py <fichero-entrada> <fichero-salida.dat>

1. Lee el fichero de entrada (l y h en la 1a linea, prioridades en la 2a,
   pesos en la 3a y capacidades en la 4a).
2. Genera el fichero .dat indicado como segundo argumento (no se borra).
3. Invoca glpsol con parte-2.mod y el .dat generado.
4. Muestra en pantalla: <num. variables> <num. restricciones> <objetivo>
5. Escribe la disposicion optima de forma grafica en un fichero de
   salida con el mismo nombre que el .dat y extension .out
"""

import os
import re
import subprocess
import sys
import tempfile

DIR_SCRIPT = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(DIR_SCRIPT, "parte-2.mod")


def resolver_ruta(ruta):
    """Si la ruta no contiene directorio, se asume el del script."""
    if os.path.dirname(ruta) == "":
        return os.path.join(DIR_SCRIPT, ruta)
    return ruta


def error(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def leer_entrada(ruta):
    """Devuelve (l, h, prioridades, pesos, capacidades)."""
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            lineas = [ln.split() for ln in f if ln.strip()]
    except OSError as e:
        error(f"no se puede leer '{ruta}': {e}")

    if len(lineas) < 4:
        error("el fichero de entrada debe tener 4 lineas "
              "(l y h, prioridades, pesos y capacidades)")
    try:
        l = int(lineas[0][0])
        h = int(lineas[0][1])
        prioridades = [int(v) for v in lineas[1]]
        pesos = [int(v) for v in lineas[2]]
        capacidades = [int(v) for v in lineas[3]]
    except (ValueError, IndexError):
        error("el fichero de entrada contiene valores no enteros "
              "o falta alguno en la primera linea")

    if l < 1 or h < 1:
        error("el lado del pallet y el numero de niveles deben ser >= 1")
    n = h * l * l
    for nombre, lista in (("prioridades", prioridades), ("pesos", pesos),
                          ("capacidades", capacidades)):
        if len(lista) != n:
            error(f"se esperaban {n} {nombre} (n = h*l^2) "
                  f"y se han leido {len(lista)}")
    if any(p < 1 for p in prioridades):
        error("las prioridades deben ser enteros >= 1")
    if any(w < 0 for w in pesos) or any(g < 0 for g in capacidades):
        error("los pesos y las capacidades deben ser enteros >= 0")
    return l, h, prioridades, pesos, capacidades


def escribir_dat(ruta, l, h, prioridades, pesos, capacidades):
    """Genera el fichero de datos en formato MathProg."""
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("data;\n\n")
        f.write(f"param l := {l};\n")
        f.write(f"param h := {h};\n\n")
        for nombre, lista in (("p", prioridades), ("w", pesos),
                              ("y", capacidades)):
            f.write(f"param {nombre} :=\n")
            for c, valor in enumerate(lista, start=1):
                f.write(f"  {c} {valor}\n")
            f.write(";\n\n")
        f.write("end;\n")


def ejecutar_glpk(ruta_dat):
    """Invoca glpsol y devuelve (n_vars, n_restr, objetivo, asignacion)."""
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
    asignacion = {}                         # (i, j, k) -> caja c
    for linea in display.splitlines():
        partes = linea.split()
        if not partes:
            continue
        if partes[0] == "OBJ":
            objetivo = float(partes[1])
        elif partes[0] == "SOL":
            c, i, j, k = map(int, partes[1:5])
            asignacion[(i, j, k)] = c
    if objetivo is None:
        error("no se ha podido leer el valor de la funcion objetivo")
    return n_variables, n_restricciones, objetivo, asignacion


def escribir_solucion(ruta, l, h, prioridades, pesos, capacidades,
                      objetivo, asignacion):
    """Dibuja cada nivel del pallet (vista cenital).
    Fila l arriba, junto al acceso. Cada celda muestra: peso (arriba a la
    izquierda), prioridad (centro) y capacidad (abajo a la derecha)."""
    ancho = max(9, len(f"w={max(pesos)}") + 2, len(f"c={max(capacidades)}") + 2,
                len(f"p={max(prioridades)}") + 2)
    sep = "+" + "+".join(["-" * ancho] * l) + "+"
    margen = " " * 9

    lineas = []
    lineas.append(f"Pallet de lado l = {l} y h = {h} niveles "
                  f"(n = {h * l * l} cajas)")
    lineas.append(f"Coste medio optimo = {objetivo:.2f}")
    lineas.append("")
    lineas.append("Cada celda muestra: w = peso (arriba izquierda), "
                  "p = prioridad (centro, 1 = maxima),")
    lineas.append("c = capacidad (abajo derecha). Nivel 1 = inferior.")

    for k in range(1, h + 1):
        lineas.append("")
        lineas.append(f"=== Nivel {k} ===")
        lineas.append(margen + "PUNTO DE ACCESO".center(len(sep)))
        lineas.append(margen + "v".center(len(sep)))
        cab = "".join(f"Col {j}".center(ancho + 1) for j in range(1, l + 1))
        lineas.append(margen + " " + cab)
        lineas.append(margen + sep)
        for i in range(l, 0, -1):
            cajas = [asignacion[(i, j, k)] for j in range(1, l + 1)]
            arriba = [f" w={pesos[c - 1]}".ljust(ancho) for c in cajas]
            medio = [f"p={prioridades[c - 1]}".center(ancho) for c in cajas]
            abajo = [f"c={capacidades[c - 1]} ".rjust(ancho) for c in cajas]
            lineas.append(margen + "|" + "|".join(arriba) + "|")
            lineas.append(f"Fila {i:<3} " + "|" + "|".join(medio) + "|")
            lineas.append(margen + "|" + "|".join(abajo) + "|")
            lineas.append(margen + sep)

    lineas.append("")
    lineas.append("Detalle (fila, columna, nivel) -> caja [prioridad, peso, "
                  "capacidad] : coste ; peso soportado")
    for k in range(1, h + 1):
        for i in range(l, 0, -1):
            for j in range(1, l + 1):
                c = asignacion[(i, j, k)]
                coste = sum(prioridades[asignacion[(ii, j, k)] - 1]
                            for ii in range(i + 1, l + 1))
                soportado = sum(pesos[asignacion[(i, j, kk)] - 1]
                                for kk in range(k + 1, h + 1))
                lineas.append(
                    f"  ({i},{j},{k}) -> caja {c} "
                    f"[p={prioridades[c - 1]}, w={pesos[c - 1]}, "
                    f"c={capacidades[c - 1]}] : coste {coste} ; "
                    f"soporta {soportado}/{capacidades[c - 1]}")

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

    l, h, prioridades, pesos, capacidades = leer_entrada(ruta_in)
    escribir_dat(ruta_dat, l, h, prioridades, pesos, capacidades)
    n_vars, n_restr, obj, asig = ejecutar_glpk(ruta_dat)

    print(f"{n_vars} {n_restr} {obj:.2f}")
    escribir_solucion(ruta_out, l, h, prioridades, pesos, capacidades,
                      obj, asig)


if __name__ == "__main__":
    main()
