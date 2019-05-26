int* a; //Puntero global

int summation(int n, int* m){
    int* pointer = &n;
    int result = 0;
    int i = 1;
    a = &i; //Asignacion entre puntero y referencia.
    while(i <= n){
        result = result + i;
        i = i + 1;    
    }
    return result;  
}

