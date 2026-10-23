

# ---------------------------- Parametros ----------------------------
param l, integer, >= 1;                  # lado del pallet
param h, integer, >= 1;                 # numero maximo de niveles
param n, integer, >= 1, <= h * l * l;   # numero de cajas (n <= h*l^2)

set CAJAS    := 1..n;                   # indice c de cada caja
set FILAS    := 1..l;                   # indice i (fila)
set COLUMNAS := 1..l;                   # indice j (columna)
set NIVELES  := 1..h;                   # indice k (nivel)

param p{CAJAS}, integer, >= 1;          # prioridad de cada caja
param w{CAJAS}, integer, >= 0;         # peso de cada caja (gramos)
param y{CAJAS}, integer, >= 0;           # capacidad de cada caja (g)

param pmax := max{c in CAJAS} p[c];     # mayor numero de prioridad

# ----------------- variables de decision ---------------------
/* x[c,i,j,k] = 1 si la caja c se coloca en la fila i, columna j y nivel k; 0 si no.
        Una posicion esta vacia si sum_c x[c,i,j,k] = 0. */

var x{c in CAJAS, i in FILAS, j in COLUMNAS, k in NIVELES}, binary;

/* TENEMOS QUE UTILIZAR OTRO NOMBRE QUE NO SEA C*/
/*u[i,j,k] = coste de la posicion (i,j,k): suma de las prioridades de las cajas que hay
        por delante en su columna y nivel si la posicion esta ocupada, y 0 si esta
        vacia. La fila l nunca tiene cajas por delante, por lo que no necesita
        variable. */

var u{i in 1..l-1, j in COLUMNAS, k in NIVELES}, >= 0;

# --------------------------- Funcion objetivo -----------------------
/* Coste medio: suma de los costes de las posiciones, dividida entre el
 numero de cajas n. Al minimizar, u[i,j,k] toma el valor mas pequeno
 que permite la restriccion (6), es decir, exactamente el coste.*/

minimize coste_medio:
    (1 / n) * sum{i in 1..l-1, j in COLUMNAS, k in NIVELES} u[i,j,k];

# ----------------------------- Restricciones ------------------------
# (1) Cada caja se coloca exactamente en una posicion

s.t. una_posicion_por_caja{c in CAJAS}:
    sum{i in FILAS, j in COLUMNAS, k in NIVELES} x[c,i,j,k] = 1;

# (2) Cada posicion contiene como maximo una caja (puede quedar vacia)
s.t. como_mucho_una_caja{i in FILAS, j in COLUMNAS, k in NIVELES}:
    sum{c in CAJAS} x[c,i,j,k] <= 1;

/* (3) Orden de prioridad en cada columna y nivel. Una posicion vacia tiene prioridad
        +infinito (el numero mas alto posible), que se representa con pmax +
        1: ninguna caja real puede quedar detras de una posicion vacia, y las vacias
        van siempre al fondo. Aqui utilizamos el metodo de Big-M.*/

s.t. orden_prioridad{i in 1..l-1, j in COLUMNAS, k in NIVELES}:
    sum{c in CAJAS} p[c] * x[c,i+1,j,k] + (pmax + 1) * (1 - sum{c in CAJAS} x[c,i+1,j,k])
    <= sum{c in CAJAS} p[c] * x[c,i,j,k] + (pmax + 1) * (1 - sum{c in CAJAS} x[c,i,j,k]);


/* (4) Capacidad: la caja en (i,j,k) debe soportar el peso de todas las cajas apiladas
        encima de ella (niveles k+1..h). Una posicion vacia tiene capacidad 0 y peso 0,
        por lo que no aporta nada.*/

s.t. capacidad{i in FILAS, j in COLUMNAS, k in 1..h-1}:
    sum{c in CAJAS} y[c] * x[c,i,j,k] >= sum{c in CAJAS, kk in k+1..h} w[c] * x[c,i,j,kk];

/* (5) No se pueden disponer cajas sobre una posicion vacia: la ocupacion del nivel k+1
        no puede superar la del nivel k. Como ambas ocupaciones valen 0 o 1, no hace
        falta ninguna "M". */

s.t. nada_sobre_vacio{i in FILAS, j in COLUMNAS, k in 1..h-1}:
    sum{c in CAJAS} x[c,i,j,k+1] <= sum{c in CAJAS} x[c,i,j,k];

/* (6) Coste de cada posicion. Si esta ocupada (sum_c x = 1), u debe ser al menos la
        suma de prioridades de las cajas que tiene delante. Si esta vacia (sum_c x =
        0), el termino (l-i)*pmax es una cota superior de esa suma, de modo que la
        restriccion se relaja y u puede valer 0. */

s.t. coste_posicion{i in 1..l-1, j in COLUMNAS, k in NIVELES}:
    u[i,j,k] >= sum{c in CAJAS, ii in i+1..l} p[c] * x[c,ii,j,k]
                - (l - i) * pmax * (1 - sum{c in CAJAS} x[c,i,j,k]);

solve;

#------------------- Volcado de la solucion para el script ---------
printf "OBJ %.10g\n", coste_medio;
printf{c in CAJAS, i in FILAS, j in COLUMNAS, k in NIVELES: x[c,i,j,k] > 0.5}
    "SOL %d %d %d %d\n", c, i, j, k;

end;
