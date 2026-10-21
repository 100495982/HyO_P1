/* =====================================================================
 * Heuristica y Optimizacion - Practica 1 (Programacion Lineal)
 * Parte 2: Montaje volumetrico
 *
 * Problema de Programacion Lineal Entera (binaria): asignacion de
 * n = h * l^2 cajas a las h * l^2 posiciones (i,j,k) de un pallet de
 * lado l y h niveles. La fila l es la mas cercana al punto de acceso;
 * la fila 1 la mas alejada. (1,1) es la esquina inferior izquierda.
 * El nivel 1 es el inferior y el nivel h el superior.
 * ===================================================================== */

/* ---------------------------- Parametros ---------------------------- */
param l, integer, >= 1;                 /* lado del pallet               */
param h, integer, >= 1;                 /* numero de niveles             */
param n, integer, := h * l * l;         /* numero de cajas (n = h*l^2)   */

set CAJAS    := 1..n;                   /* indice c de cada caja         */
set FILAS    := 1..l;                   /* indice i (fila)               */
set COLUMNAS := 1..l;                   /* indice j (columna)            */
set NIVELES  := 1..h;                   /* indice k (nivel)              */

param p{CAJAS}, integer, >= 1;          /* prioridad de cada caja        */
param w{CAJAS}, integer, >= 0;          /* peso de cada caja (gramos)    */
param y{CAJAS}, integer, >= 0;          /* capacidad de cada caja (g)    */

/* ------------------------ Variables de decision --------------------- */
/* x[c,i,j,k] = 1 si la caja c se coloca en la fila i, columna j y
 * nivel k; 0 si no                                                      */
var x{c in CAJAS, i in FILAS, j in COLUMNAS, k in NIVELES}, binary;

/* --------------------------- Funcion objetivo ----------------------- */
/* Coste de una caja en (i,j,k): suma de prioridades de las cajas que
 * tiene por delante en su columna y en su mismo nivel (filas i+1..l).
 * No depende del nivel. Sumando para todas las cajas, la prioridad de
 * la caja en la fila i se cuenta (i-1) veces. Se minimiza el coste
 * medio (dividido entre el numero de cajas n = h*l^2).                */
minimize coste_medio:
    (1 / n) * sum{c in CAJAS, i in FILAS, j in COLUMNAS, k in NIVELES}
        (i - 1) * p[c] * x[c,i,j,k];

/* ----------------------------- Restricciones ------------------------ */
/* (1) Cada caja se coloca exactamente en una posicion */
s.t. una_posicion_por_caja{c in CAJAS}:
    sum{i in FILAS, j in COLUMNAS, k in NIVELES} x[c,i,j,k] = 1;

/* (2) Cada posicion contiene exactamente una caja (pallet lleno) */
s.t. una_caja_por_posicion{i in FILAS, j in COLUMNAS, k in NIVELES}:
    sum{c in CAJAS} x[c,i,j,k] = 1;

/* (3) Orden de prioridad en cada columna y en cada nivel: la caja de
 *     la fila i+1 (mas cerca del acceso) tiene prioridad igual o mayor
 *     (numero menor o igual) que la de la fila i. Los niveles no se
 *     afectan entre si.                                                */
s.t. orden_prioridad{i in 1..l-1, j in COLUMNAS, k in NIVELES}:
    sum{c in CAJAS} p[c] * x[c,i+1,j,k] <= sum{c in CAJAS} p[c] * x[c,i,j,k];

/* (4) Capacidad: la caja en (i,j,k) debe soportar el peso de todas las
 *     cajas apiladas encima de ella (niveles k+1..h) en la misma fila
 *     y columna. El nivel superior no soporta nada, por lo que la
 *     restriccion solo se plantea para k = 1..h-1.                    */
s.t. capacidad{i in FILAS, j in COLUMNAS, k in 1..h-1}:
    sum{c in CAJAS} y[c] * x[c,i,j,k]
        >= sum{c in CAJAS, kk in k+1..h} w[c] * x[c,i,j,kk];

solve;

/* ------------------- Volcado de la solucion (para sol-2.py) --------- */
printf "OBJ %.10g\n", coste_medio;
printf{c in CAJAS, i in FILAS, j in COLUMNAS, k in NIVELES: x[c,i,j,k] > 0.5}
    "SOL %d %d %d %d\n", c, i, j, k;

end;
