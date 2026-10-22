#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Heuristica y Optimizacion - Practica 1, Parte 3

1. Lee el fichero de entrada (l y h en la 1a linea, y en las lineas 2, 3 y 4 las prioridades, pesos y capacidades de las n cajas, n <= h*l^2).
2. Genera el fichero .dat indicado como segundo argumento (no se borra).
3. Invoca glpsol con parte-3.mod y el .dat generado.
4. Muestra en pantalla: <num. variables> <num. restricciones> <objetivo>
5. Escribe la disposicion optima de forma grafica en un fichero de salida con el mismo nombre que el .dat y extension .out
"""

import os
import re
import subprocess
import sys
import tempfile

DIR_SCRIPT = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(DIR_SCRIPT, "parte-3.mod")

# Orden de los dos numeros de la primera linea del fichero de entrada.
# El enunciado dice "<l> <h>" (como en las partes 2 y 4), pero el ejemplo
# de la parte 3 ("3 2" para un pallet de lado l = 2 y 3 niveles) parece usar
# el orden contrario. Poner a False si el orden es "<h> <l>".
PRIMERA_LINEA_ES_L_H = True

# Limite de tiempo de glpsol en segundos (None = sin limite, se busca el
# optimo demostrado). GLPK encuentra casi siempre la solucion optima rapido,
# pero demostrar que lo es puede tardar mucho en instancias medianas. Si se
# fija un limite y se alcanza, se usa la mejor solucion encontrada y se
# avisa por la salida de error.
LIMITE_TIEMPO = None


def resolver_ruta(ruta):
    "Si la ruta no contiene directorio, toma el del script."
    if os.path.dirname(ruta) == "":
        return os.path.join(DIR_SCRIPT, ruta)
    return ruta


def error(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def leer_entrada(ruta):
    "Devuelve (l, h, prioridades, pesos, capacidades)."
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            lineas = [ln.split() for ln in f if ln.strip()]
    except OSError as e:
        error(f"no se puede leer '{ruta}': {e}")

    if len(lineas) < 4:
        error("el fichero de entrada debe tener 4 lineas (l y h, prioridades, pesos y capacidades)")
    try:
        a, b = int(lineas[0][0]), int(lineas[0][1])
        prioridades = [int(v) for v in lineas[1]]
        pesos = [int(v) for v in lineas[2]]
        capacidades = [int(v) for v in lineas[3]]
    except (ValueError, IndexError):
        error("el fichero de entrada contiene valores no enteros o falta alguno en la primera linea")

    l, h = (a, b) if PRIMERA_LINEA_ES_L_H else (b, a)
    if l < 1 or h < 1:
        error("el lado del pallet y el numero de niveles deben ser >= 1")
    n = len(prioridades)
    if not 1 <= n <= h * l * l:
        error(f"el numero de cajas n = {n} debe cumplir 1 <= n <= h*l^2 "
              f"= {h * l * l}")
    if len(pesos) != n or len(capacidades) != n:
        error(f"se esperaban {n} pesos y {n} capacidades "
              f"y se han leido {len(pesos)} y {len(capacidades)}")
    if any(p < 1 for p in prioridades):
        error("las prioridades deben ser enteros >= 1")
    if any(w < 0 for w in pesos) or any(g < 0 for g in capacidades):
        error("los pesos y las capacidades deben ser enteros >= 0")
    return l, h, prioridades, pesos, capacidades


def escribir_dat(ruta, l, h, prioridades, pesos, capacidades):
    "Genera el fichero de datos en formato MathProg."
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("data;\n\n")
        f.write(f"param l := {l};\n")
        f.write(f"param h := {h};\n")
        f.write(f"param n := {len(prioridades)};\n\n")
        for nombre, lista in (("p", prioridades), ("w", pesos),
                              ("y", capacidades)):
            f.write(f"param {nombre} :=\n")
            for c, valor in enumerate(lista, start=1):
                f.write(f"  {c} {valor}\n")
            f.write(";\n\n")
        f.write("end;\n")


def ejecutar_glpk(ruta_dat):
    "Invoca glpsol y devuelve (n_vars, n_restr, objetivo, asignacion)."
    with tempfile.TemporaryDirectory() as tmp:
        f_salida = os.path.join(tmp, "glpk.out")      # informe de glpsol
        f_display = os.path.join(tmp, "glpk.disp")    # printf del modelo
        cmd = ["glpsol", "--model", MODELO, "--data", ruta_dat,
               "--output", f_salida, "--display", f_display]
        if LIMITE_TIEMPO is not None:
            cmd += ["--tmlim", str(int(LIMITE_TIEMPO))]
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

    limite = "TIME LIMIT EXCEEDED" in proc.stdout
    if "INTEGER UNDEFINED" in informe or "INTEGER EMPTY" in informe:
        if limite:
            error("limite de tiempo alcanzado sin encontrar ninguna solucion")
        error("el problema no tiene solucion factible")
    if limite:
        print("Aviso: limite de tiempo alcanzado; se usa la mejor solucion encontrada (no se ha demostrado que sea optima)",
              file=sys.stderr)

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
    """Dibuja cada nivel del pallet (vista cenital). Fila l arriba, junto al acceso. Cada celda muestra: peso (arriba a la
    izquierda), prioridad (centro) y capacidad (abajo a la derecha). Las posiciones vacias se dejan en blanco."""
    n = len(prioridades)
    ancho = max(9, len(f"w={max(pesos)}") + 2, len(f"c={max(capacidades)}") + 2,
                len(f"p={max(prioridades)}") + 2)
    sep = "+" + "+".join(["-" * ancho] * l) + "+"
    margen = " " * 9
    blanco = " " * ancho

    lineas = []
    lineas.append(f"Pallet de lado l = {l} y maximo h = {h} niveles "
                  f"({n} cajas, {h * l * l - n} posiciones vacias)")
    lineas.append(f"Coste medio optimo = {objetivo:.2f}")
    lineas.append("")
    lineas.append("Cada celda muestra: w = peso (arriba izquierda), "
                  "p = prioridad (centro, 1 = maxima),")
    lineas.append("c = capacidad (abajo derecha). Nivel 1 = inferior. "
                  "Las posiciones vacias se dejan en blanco.")

    for k in range(1, h + 1):
        lineas.append("")
        lineas.append(f"=== Nivel {k} ===")
        lineas.append(margen + "PUNTO DE ACCESO".center(len(sep)))
        lineas.append(margen + "v".center(len(sep)))
        cab = "".join(f"Col {j}".center(ancho + 1) for j in range(1, l + 1))
        lineas.append(margen + " " + cab)
        lineas.append(margen + sep)
        for i in range(l, 0, -1):
            arriba, medio, abajo = [], [], []
            for j in range(1, l + 1):
                c = asignacion.get((i, j, k))
                if c is None:
                    arriba.append(blanco)
                    medio.append(blanco)
                    abajo.append(blanco)
                else:
                    arriba.append(f" w={pesos[c - 1]}".ljust(ancho))
                    medio.append(f"p={prioridades[c - 1]}".center(ancho))
                    abajo.append(f"c={capacidades[c - 1]} ".rjust(ancho))
            lineas.append(margen + "|" + "|".join(arriba) + "|")
            lineas.append(f"Fila {i:<3} " + "|" + "|".join(medio) + "|")
            lineas.append(margen + "|" + "|".join(abajo) + "|")
            lineas.append(margen + sep)

    lineas.append("")
    lineas.append("Detalle (fila, columna, nivel) -> caja [prioridad, peso, capacidad] : coste ; peso soportado")
    for k in range(1, h + 1):
        for i in range(l, 0, -1):
            for j in range(1, l + 1):
                c = asignacion.get((i, j, k))
                if c is None:
                    continue
                coste = sum(prioridades[asignacion[(ii, j, k)] - 1]
                            for ii in range(i + 1, l + 1)
                            if (ii, j, k) in asignacion)
                soportado = sum(pesos[asignacion[(i, j, kk)] - 1]
                                for kk in range(k + 1, h + 1)
                                if (i, j, kk) in asignacion)
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
