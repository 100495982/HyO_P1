
# ---------------------------- Parametros ----------------------------
param l, integer, >= 1;                  # lado del pallet
param h, integer, >= 1;                 # numero maximo de niveles
param n, integer, >= 1, <= h * l * l;   # numero de cajas (n <= h*l^2)
param P, >= 0;                          #coste de montar un pallet

set CAJAS    := 1..n;                   # indice c de cada caja
set FILAS    := 1..l;                   # indice i (fila)
set COLUMNAS := 1..l;                   # indice j (columna)
set NIVELES  := 1..h;                   # indice k (nivel)

param p{CAJAS}, integer, >= 1;          # prioridad de cada caja
param w{CAJAS}, integer, >= 0;         # peso de cada caja (gramos)
param y{CAJAS}, integer, >= 0;           # capacidad de cada caja (g)

param pmax := max{c in CAJAS} p[c];     # mayor numero de prioridad

/* Numero maximo de pallets que puede usar una solucion optima. Colocando l cajas por
        pallet, todas en la fila l (la del acceso) del nivel 1, ninguna caja tiene nada
        delante ni encima: la solucion es siempre factible y su coste es P * ceil(n/l).
        Cualquier solucion con mas pallets cuesta al menos P * (ceil(n/l) + 1), luego
        nunca es mejor. Por eso basta con M = ceil(n/l) pallets candidatos.*/
param M := ceil(n / l);
set PALLETS := 1..M;                # indice m de cada pallet

/* Ruptura de simetrias: los pallets son intercambiables, asi que se numeran segun la
        menor caja que contienen. Entonces la caja c solo puede ir en los pallets 1..c
        (la caja 1 siempre va en el pallet 1), por lo que x solo se define para m <= c.*/

# ------------------------ Variables de decision --------------------
/* x[c,i,j,k,m] = 1 si la caja c se coloca en la fila i, columna j y nivel k del pallet
        m; 0 si no */

var x{c in CAJAS, i in FILAS, j in COLUMNAS, k in NIVELES, m in PALLETS: m <= c}, binary;

# z[m] = 1 si el pallet m se monta (contiene al menos una caja).

var z{m in PALLETS}, binary;

/* u[i,j,k,m] = coste de la posicion (i,j,k) del pallet m: suma de las prioridades de
        las cajas que hay por delante en su columna y nivel si la posicion esta
        ocupada, y 0 si esta vacia. La fila l nunca tiene cajas por delante, por lo que
        no necesita variable.*/

var u{i in 1..l-1, j in COLUMNAS, k in NIVELES, m in PALLETS}, >= 0;

# --------------------------- Funcion objetivo -----------------------
/* Coste total = coste de todas las cajas + P por cada pallet montado. Al minimizar, u
        toma el valor mas pequeno que permite la restriccion (7), es decir, exactamente
        el coste de la caja.*/

minimize coste_total:
    sum{i in 1..l-1, j in COLUMNAS, k in NIVELES, m in PALLETS} u[i,j,k,m]
    + P * sum{m in PALLETS} z[m];

# ----------------------------- Restricciones ------------------------

#(1) Cada caja se coloca exactamente en una posicion de un pallet

s.t. una_posicion_por_caja{c in CAJAS}:
    sum{m in PALLETS, i in FILAS, j in COLUMNAS, k in NIVELES: m <= c} x[c,i,j,k,m] = 1;

/* (2) Cada posicion contiene como maximo una caja, y solo si el pallet se monta: si
        z[m] = 0 el pallet m no puede contener ninguna caja. Asi, montar un pallet
        obliga a pagar su coste P.*/

s.t. como_mucho_una_caja{i in FILAS, j in COLUMNAS, k in NIVELES, m in PALLETS}:
    sum{c in CAJAS: m <= c} x[c,i,j,k,m] <= z[m];

/* (3) Orden de prioridad en cada columna, nivel y pallet. Una posicion vacia tiene
        prioridad +infinito, representada con pmax + 1: las posiciones vacias quedan
        siempre al fondo. */

s.t. orden_prioridad{i in 1..l-1, j in COLUMNAS, k in NIVELES, m in PALLETS}:
    sum{c in CAJAS: m <= c} p[c] * x[c,i+1,j,k,m]
        + (pmax + 1) * (1 - sum{c in CAJAS: m <= c} x[c,i+1,j,k,m])
    <= sum{c in CAJAS: m <= c} p[c] * x[c,i,j,k,m]
        + (pmax + 1) * (1 - sum{c in CAJAS: m <= c} x[c,i,j,k,m]);

/* (4) Capacidad: la caja en (i,j,k) del pallet m debe soportar el peso de todas las
        cajas apiladas encima de ella en ese mismo pallet. Ningun pallet tiene mas de h
        niveles porque el indice k solo toma los valores 1..h.*/

s.t. capacidad{i in FILAS, j in COLUMNAS, k in 1..h-1, m in PALLETS}:
    sum{c in CAJAS: m <= c} y[c] * x[c,i,j,k,m]
        >= sum{kk in k+1..h, c in CAJAS: m <= c} w[c] * x[c,i,j,kk,m];

/* (5) No se pueden disponer cajas sobre una posicion vacia: en cada pallet, la
        ocupacion del nivel k+1 no puede superar la del k.*/

s.t. nada_sobre_vacio{i in FILAS, j in COLUMNAS, k in 1..h-1, m in PALLETS}:
    sum{c in CAJAS: m <= c} x[c,i,j,k+1,m] <= sum{c in CAJAS: m <= c} x[c,i,j,k,m];

/* (6) Coste de cada posicion. Si esta ocupada, u es al menos la suma de prioridades de
        las cajas que tiene delante en su columna, nivel y pallet. Si esta vacia,
        (l-i)*pmax es una cota superior de esa suma y la restriccion se relaja, de modo
        que u puede valer 0. */

s.t. coste_posicion{i in 1..l-1, j in COLUMNAS, k in NIVELES, m in PALLETS}:
    u[i,j,k,m] >= sum{ii in i+1..l, c in CAJAS: m <= c} p[c] * x[c,ii,j,k,m]
                  - (l - i) * pmax * (1 - sum{c in CAJAS: m <= c} x[c,i,j,k,m]);


/* (7) Ruptura de simetrias: los pallets se usan en orden, solo se monta el pallet m+1
        si se ha montado el  m */

s.t. pallets_en_orden{m in 1..M-1}:
    z[m+1] <= z[m];


solve;

#------------------- Volcado de la solucion para el script ---------
printf "OBJ %.10g\n", coste_total;
printf "PALLETS %d\n", sum{m in PALLETS} z[m];
printf{c in CAJAS, i in FILAS, j in COLUMNAS, k in NIVELES, m in PALLETS:
       m <= c and x[c,i,j,k,m] > 0.5}
    "SOL %d %d %d %d %d\n", c, i, j, k, m;

end;
