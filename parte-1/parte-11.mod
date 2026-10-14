# Conjuntos
set CAJA;
set FILA;
set COLUMNA; 
set PRIORIDADES;

# Parámetros
param coste{CAJA};

# Variables
var x{CAJA, FILA, COLUMNA} binary;

# Función objetivo
minimize CosteTotal:
    sum{c in CAJAS, f in FILAS, k in COLUMNAS} coste[c] * x[c,f,k];

# Cada caja se coloca en exactamente una posición
s.t. UnaPosicionPorCaja{c in CAJAS}:
    sum{f in FILAS, k in COLUMNAS} x[c,f,k] = 1;

# En cada posición cabe como mucho una caja
s.t. UnaCajaPorPosicion{f in FILAS, k in COLUMNAS}:
    sum{c in CAJAS} x[c,f,k] <= 1;
solve;

printf "Coste total: %g\n", CosteTotal;
printf {i in TRABAJADORES, j in TAREAS: x[i,j] = 1}
    "%s -> %s (coste %g)\n", i, j, coste[i,j];

end;
