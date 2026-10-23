# ----------- Parametros ----------
param l, integer, >= 1;                 # lado del pallet
param n, integer, := l * l;             # numero de cajas (n = l^2)

set CAJAS    := 1..n;                   # indice c de cada caja
set FILAS    := 1..l;                   # indice i (fila)
set COLUMNAS := 1..l;                   # indice j (columna)

param p{CAJAS}, integer, >= 1;          # prioridad de cada caja

# ----------------- variables de decision ---------------------
# x[c,i,j] = 1 si la caja c se coloca en la fila i, columna j; 0 si no
var x{c in CAJAS, i in FILAS, j in COLUMNAS}, binary;

# --------------------------- Funcion objetivo -----------------------
 /* Coste de una caja en (i,j): suma de prioridades de las cajas que
 tiene por delante en su columna (filas i+1..l). Sumando para todas
 las cajas, la prioridad de la caja en la fila i se cuenta (i-1)
 veces. Se minimiza el coste medio (dividido entre n). */

minimize coste_medio:
        (1 / n) * sum{c in CAJAS, i in FILAS, j in COLUMNAS} (i - 1) * p[c] * x[c,i,j];

# ----------------------------- Restricciones ------------------------

# (1) Cada caja se coloca exactamente en una posicion

s.t. una_posicion_por_caja{c in CAJAS}:
    sum{i in FILAS, j in COLUMNAS} x[c,i,j] = 1;

# (2) Cada posicion contiene exactamente una caja (pallet lleno)

s.t. una_caja_por_posicion{i in FILAS, j in COLUMNAS}: sum{c in CAJAS} x[c,i,j] = 1;

/* (3) Orden de prioridad en cada columna: la caja de la fila i+1
        (mas cerca del acceso) tiene prioridad igual o mayor (numero
        menor o igual) que la de la fila i */

s.t. orden_prioridad{i in 1..l-1, j in COLUMNAS}:
        sum{c in CAJAS} p[c] * x[c,i+1,j] <= sum{c in CAJAS} p[c] * x[c,i,j];

solve;

# ----------------- Volcado de la solucion para el script -----------
printf "OBJ %.10g\n", coste_medio;
printf{c in CAJAS, i in FILAS, j in COLUMNAS: x[c,i,j] > 0.5}
    "SOL %d %d %d\n", c, i, j;

end;
