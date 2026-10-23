
# ---------------------------- Parametros ----------------------------
param l, integer, >= 1;                 # lado del pallet
param h, integer, >= 1;                 # numero de niveles
param n, integer, := h * l * l;        # numero de cajas (n = h*l^2)

set CAJAS    := 1..n;                  # indice c de cada caja
set FILAS    := 1..l;                 # indice i (fila)
set COLUMNAS := 1..l;                   # indice j (columna)
set NIVELES  := 1..h;                  # indice k (nivel)

param p{CAJAS}, integer, >= 1;          # prioridad de cada caja
param w{CAJAS}, integer, >= 0;          # peso de cada caja (gramos)
param y{CAJAS}, integer, >= 0;         # capacidad de cada caja (g)

# ----------------- variables de decision ---------------------
# x[c,i,j,k] = 1 si la caja c se coloca en la fila i, columna j y nivel k; 0 si no

var x{c in CAJAS, i in FILAS, j in COLUMNAS, k in NIVELES}, binary;

# --------------------------- Funcion objetivo -----------------------
# La misma que la parte 1 pero ahora con la dimension de niveles

minimize coste_medio:
    (1 / n) * sum{c in CAJAS, i in FILAS, j in COLUMNAS, k in NIVELES}
        (i - 1) * p[c] * x[c,i,j,k];

# ----------------------------- Restricciones ------------------------
# (1) Cada caja se coloca exactamente en una posicion

s.t. una_posicion_por_caja{c in CAJAS}:
    sum{i in FILAS, j in COLUMNAS, k in NIVELES} x[c,i,j,k] = 1;

# (2) Cada posicion contiene exactamente una caja (pallet lleno)

s.t. una_caja_por_posicion{i in FILAS, j in COLUMNAS, k in NIVELES}:
    sum{c in CAJAS} x[c,i,j,k] = 1;

/* (3) Orden de prioridad en cada columna: la caja de la fila i+1
        (mas cerca del acceso) tiene prioridad igual o mayor (numero
        menor o igual) que la de la fila i. Es independiente del nivel. Es la misma que
        la parte 1 pero con la dimension de niveles.*/

s.t. orden_prioridad{i in 1..l-1, j in COLUMNAS, k in NIVELES}:
    sum{c in CAJAS} p[c] * x[c,i+1,j,k] <= sum{c in CAJAS} p[c] * x[c,i,j,k];

/* (4) Capacidad: la caja en (i,j,k) debe soportar el peso de todas las cajas apiladas
        encima de ella (niveles k+1..h) en la misma fila y columna. El nivel
        superior no soporta nada, por lo que la restriccion solo se plantea para k =
        1..h-1. */

s.t. capacidad{i in FILAS, j in COLUMNAS, k in 1..h-1}:
    sum{c in CAJAS} y[c] * x[c,i,j,k] >= sum{c in CAJAS, kk in k+1..h} w[c] * x[c,i,j,kk];

solve;

#------------------- Volcado de la solucion para el scritp ---------
printf "OBJ %.10g\n", coste_medio;
printf{c in CAJAS, i in FILAS, j in COLUMNAS, k in NIVELES: x[c,i,j,k] > 0.5}
    "SOL %d %d %d %d\n", c, i, j, k;

end;
