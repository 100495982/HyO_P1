#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Heuristica y Optimizacion - Practica 1, Parte 4
Uso:  ./sol-4.py <fichero-entrada> <fichero-salida.dat>

1. Lee el fichero de entrada (l, h y P en la 1a linea, y en las lineas 2, 3
   y 4 las prioridades, pesos y capacidades de las n cajas).
2. Genera el fichero .dat indicado como segundo argumento (no se borra).
3. Invoca glpsol con parte-4.mod y el .dat generado.
4. Muestra en pantalla: <num. variables> <num. restricciones> <objetivo>
5. Escribe la disposicion optima de forma grafica (pallet a pallet y nivel
   a nivel) en un fichero de salida con el mismo nombre que el .dat y
   extension .out
"""

import os
import re
import subprocess
import sys
import tempfile

DIR_SCRIPT = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(DIR_SCRIPT, "parte-4.mod")

# Limite de tiempo de glpsol en segundos (None = sin limite, se busca el
# optimo demostrado). Si se fija un limite y se alcanza, se usa la mejor
# solucion encontrada y se avisa por la salida de error.
LIMITE_TIEMPO = None

# Opciones extra de glpsol. Con varios pallets el modelo tiene muchas
# soluciones equivalentes y la relajacion lineal es debil (restricciones con
# "M"); los cortes (--cuts) y la ramificacion por pseudocostes (--pcost)
# reducen mucho el tiempo en las instancias medianas (p. ej. 9 cajas, l = 2,
# h = 3: de ~45 s a ~2 s). No cambian el optimo, solo la forma de buscarlo.
OPCIONES_GLPK = ["--cuts", "--pcost"]


def resolver_ruta(ruta):
    """Si la ruta no contiene directorio, se asume el del script."""
    if os.path.dirname(ruta) == "":
        return os.path.join(DIR_SCRIPT, ruta)
    return ruta


def error(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def numero(texto):
    """Convierte a int si es entero; si no, a float (P puede ser real)."""
    valor = float(texto)
    return int(valor) if valor.is_integer() else valor


def leer_entrada(ruta):
    """Devuelve (l, h, P, prioridades, pesos, capacidades)."""
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            lineas = [ln.replace(",", " ").split() for ln in f if ln.strip()]
    except OSError as e:
        error(f"no se puede leer '{ruta}': {e}")

    if len(lineas) < 4:
        error("el fichero de entrada debe tener 4 lineas "
              "(l h P, prioridades, pesos y capacidades)")
    try:
        l, h = int(lineas[0][0]), int(lineas[0][1])
        coste_pallet = numero(lineas[0][2])
        prioridades = [int(v) for v in lineas[1]]
        pesos = [int(v) for v in lineas[2]]
        capacidades = [int(v) for v in lineas[3]]
    except (ValueError, IndexError):
        error("el fichero de entrada contiene valores no validos "
              "o faltan valores en la primera linea (l h P)")

    if l < 1 or h < 1:
        error("el lado del pallet y el numero de niveles deben ser >= 1")
    if coste_pallet < 0:
        error("el coste de montar un pallet, P, debe ser >= 0")
    n = len(prioridades)
    if n < 1:
        error("debe haber al menos una caja")
    if len(pesos) != n or len(capacidades) != n:
        error(f"se esperaban {n} pesos y {n} capacidades "
              f"y se han leido {len(pesos)} y {len(capacidades)}")
    if any(p < 1 for p in prioridades):
        error("las prioridades deben ser enteros >= 1")
    if any(w < 0 for w in pesos) or any(g < 0 for g in capacidades):
        error("los pesos y las capacidades deben ser enteros >= 0")
    return l, h, coste_pallet, prioridades, pesos, capacidades


def escribir_dat(ruta, l, h, coste_pallet, prioridades, pesos, capacidades):
    """Genera el fichero de datos en formato MathProg."""
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("data;\n\n")
        f.write(f"param l := {l};\n")
        f.write(f"param h := {h};\n")
        f.write(f"param n := {len(prioridades)};\n")
        f.write(f"param P := {coste_pallet};\n\n")
        for nombre, lista in (("p", prioridades), ("w", pesos),
                              ("y", capacidades)):
            f.write(f"param {nombre} :=\n")
            for c, valor in enumerate(lista, start=1):
                f.write(f"  {c} {valor}\n")
            f.write(";\n\n")
        f.write("end;\n")


def ejecutar_glpk(ruta_dat):
    """Invoca glpsol y devuelve
    (n_vars, n_restr, objetivo, num_pallets, asignacion)."""
    with tempfile.TemporaryDirectory() as tmp:
        f_salida = os.path.join(tmp, "glpk.out")      # informe de glpsol
        f_display = os.path.join(tmp, "glpk.disp")    # printf del modelo
        cmd = ["glpsol", "--model", MODELO, "--data", ruta_dat,
               "--output", f_salida, "--display", f_display] + OPCIONES_GLPK
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
        print("Aviso: limite de tiempo alcanzado; se usa la mejor solucion "
              "encontrada (no se ha demostrado que sea optima)",
              file=sys.stderr)

    # 'Rows' incluye la fila de la funcion objetivo -> se resta 1
    filas = int(re.search(r"^Rows:\s+(\d+)", informe, re.M).group(1))
    columnas = int(re.search(r"^Columns:\s+(\d+)", informe, re.M).group(1))
    n_restricciones = filas - 1
    n_variables = columnas

    objetivo = None
    num_pallets = 0
    asignacion = {}                         # (i, j, k, m) -> caja c
    for linea in display.splitlines():
        partes = linea.split()
        if not partes:
            continue
        if partes[0] == "OBJ":
            objetivo = float(partes[1])
        elif partes[0] == "PALLETS":
            num_pallets = int(round(float(partes[1])))
        elif partes[0] == "SOL":
            c, i, j, k, m = map(int, partes[1:6])
            asignacion[(i, j, k, m)] = c
    if objetivo is None:
        error("no se ha podido leer el valor de la funcion objetivo")
    return n_variables, n_restricciones, objetivo, num_pallets, asignacion


def coste_caja(asignacion, prioridades, l, i, j, k, m):
    """Suma de prioridades de las cajas delante de (i,j,k) en el pallet m."""
    return sum(prioridades[asignacion[(ii, j, k, m)] - 1]
               for ii in range(i + 1, l + 1) if (ii, j, k, m) in asignacion)


def escribir_solucion(ruta, l, h, coste_pallet, prioridades, pesos,
                      capacidades, objetivo, num_pallets, asignacion):
    """Dibuja cada nivel de cada pallet usado (vista cenital).
    Fila l arriba, junto al acceso. Cada celda muestra: peso (arriba a la
    izquierda), prioridad (centro) y capacidad (abajo a la derecha).
    Las posiciones vacias se dejan en blanco."""
    n = len(prioridades)
    ancho = max(9, len(f"w={max(pesos)}") + 2, len(f"c={max(capacidades)}") + 2,
                len(f"p={max(prioridades)}") + 2)
    sep = "+" + "+".join(["-" * ancho] * l) + "+"
    margen = " " * 9
    blanco = " " * ancho

    # Pallets realmente usados, en orden (por si alguno quedara vacio)
    usados = sorted({m for (_, _, _, m) in asignacion})
    coste_cajas = sum(coste_caja(asignacion, prioridades, l, i, j, k, m)
                      for (i, j, k, m) in asignacion)

    lineas = []
    lineas.append(f"Pallets de lado l = {l} con un maximo de h = {h} niveles; "
                  f"coste de montar cada pallet P = {coste_pallet}")
    lineas.append(f"{n} cajas repartidas en {len(usados)} pallets")
    lineas.append(f"Coste total optimo = {objetivo:.2f}  "
                  f"(cajas: {coste_cajas} + pallets: {len(usados)} x "
                  f"{coste_pallet})")
    lineas.append("")
    lineas.append("Cada celda muestra: w = peso (arriba izquierda), "
                  "p = prioridad (centro, 1 = maxima),")
    lineas.append("c = capacidad (abajo derecha). Nivel 1 = inferior. "
                  "Las posiciones vacias se dejan en blanco.")

    for num, m in enumerate(usados, start=1):
        lineas.append("")
        lineas.append("#" * (len(sep) + len(margen)))
        lineas.append(f"PALLET {num}")
        lineas.append("#" * (len(sep) + len(margen)))
        # Solo se dibujan los niveles que tienen alguna caja
        niveles = [k for k in range(1, h + 1)
                   if any((i, j, k, m) in asignacion
                          for i in range(1, l + 1) for j in range(1, l + 1))]
        for k in niveles:
            lineas.append("")
            lineas.append(f"=== Nivel {k}, pallet {num} ===")
            lineas.append(margen + "PUNTO DE ACCESO".center(len(sep)))
            lineas.append(margen + "v".center(len(sep)))
            cab = "".join(f"Col {j}".center(ancho + 1)
                          for j in range(1, l + 1))
            lineas.append(margen + " " + cab)
            lineas.append(margen + sep)
            for i in range(l, 0, -1):
                arriba, medio, abajo = [], [], []
                for j in range(1, l + 1):
                    c = asignacion.get((i, j, k, m))
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
    lineas.append("Detalle pallet: (fila, columna, nivel) -> caja [prioridad, "
                  "peso, capacidad] : coste ; peso soportado")
    for num, m in enumerate(usados, start=1):
        for k in range(1, h + 1):
            for i in range(l, 0, -1):
                for j in range(1, l + 1):
                    c = asignacion.get((i, j, k, m))
                    if c is None:
                        continue
                    coste = coste_caja(asignacion, prioridades, l, i, j, k, m)
                    soportado = sum(pesos[asignacion[(i, j, kk, m)] - 1]
                                    for kk in range(k + 1, h + 1)
                                    if (i, j, kk, m) in asignacion)
                    lineas.append(
                        f"  P{num}: ({i},{j},{k}) -> caja {c} "
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

    l, h, coste_pallet, prioridades, pesos, capacidades = leer_entrada(ruta_in)
    escribir_dat(ruta_dat, l, h, coste_pallet, prioridades, pesos,
                 capacidades)
    n_vars, n_restr, obj, num_pallets, asig = ejecutar_glpk(ruta_dat)

    print(f"{n_vars} {n_restr} {obj:.2f}")
    escribir_solucion(ruta_out, l, h, coste_pallet, prioridades, pesos,
                      capacidades, obj, num_pallets, asig)


if __name__ == "__main__":
    main()
