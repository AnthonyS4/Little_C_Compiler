from sly import Lexer, Parser
from collections import defaultdict
import math
import os

#This method shows the error made in the input code and stops the compiler
def error(reason):
    print('error: ' + reason)
    exit(0)

#Fichero para escribir el codigo ensamblador
file = open('assembler.s','w')

#Variable para controlar cuando se ha usado eax previamente
primerFactor = True

#Variable para controlar si hay uso de referencias
referenciaOperador = False

#Numero de sentencia del codigo en C
numLine = 1

#Tipo de return de funciones funcion
nombreFuncion = ' '
tipoReturn = 'int'

#Tipo de una funcion que se usa como parte derecha de una asignacion
#self.functionReturntype = 'int'

#Nombres de funciones y tipos
tiposFunciones = {}
tiposFunciones.update({'printf':'int'})
tiposFunciones.update({'scanf':'int'})

#Nombres de funciones y argumentos
argumentosFunciones = {}

#Para las variables globales, tienen que estar al principio de la salida
variablesGlobales = []

#Numero de posicion en la pila
varPos = -4

#Contador de bucles while 
whileNum = 0

#Contador de secciones IF-ELSE
ifelseNum = 0

#En el caso de usar division modular
modulo = False

#Contador de variables de entrada para hacer el addl $X, %esp tras una llamada
N = 0

#Para las const char usaremos un contador global de cadenas stringNum y un diccionario de cadena e identificador, 
# ejemplo:  cadenas["Inserte un numero"] = '$s5'        stringNum = 6
cadenas = {}
stringNum = 0

##Para los relacionales, con cada operacion de un and/or se crea una region para el caso de ser falso el resultado.
contadorRelacional = 1

#Conjunto de variables de entrada en una funcion dada.
argumentos_entrada = {}
contador_entrada = 0

###Node Classes:

#Class Node generic.
class Node():
    def escribir(self):
        pass

#Class nodeIF for only IF sections.
class NodeIF():
    ###Example: if's in C code and assembler code generated
    # C code                                             assembler code generated
    #   ||                                                          ||
    #   ||                                                          ||
    #
    # if(expression){                                             if0:                                      
    #     //IF Block                                              movl $0, %ecx
    #}                                                            cmpl %eax, %ecx
    #                                                             je end_if0    
    #                                                             assembler code for the IF Block
    #                                                             end_if0:
    #                                                             ####End of IF0####

    # if(expression)                                              if0:                                      
    #     one instruction                                         movl $0, %ecx
    #                                                             cmpl %eax, %ecx
    #                                                             je end_if0    
    #                                                             assembler code for one instruction
    #                                                             end_if0:
    #                                                             ####End of IF0####
    ###

    #self.numberBeginIF: counter of if numbers, we need this for write the if's labels.
    #self.numberEndIF: counter of if numbers, we need this for write the end of if's labels.
    def __init__(self):
        self.numberBeginIF = 0

    ###Write begin of IF's sections in assembler(remember that we are storing the values in %eax)
    #1.Write the 'if0:' label in the output file.
    #2.We load $0 in %ecx for make the comparison with %eax and write it. 
    #3.Write the comparison between %eax and 0(%ecx).
    #4.Write 'je end_if', check %eax's values and 0, in the case both are equal then we jump to the end
    #   of IF block. 
    def writeBegin(self):
        global file
        ifLabel = str(self.numberBeginIF)
        file.write('if' + ifLabel + ':\n')
        file.write('movl $0, %ecx\n')
        file.write('cmpl %eax, %ecx\n')
        file.write('je end_if' + ifLabel + '\n')
    
    ###Write end of IF's sections in assembler.
    #1.Write the 'end_if0:' label in the output file.
    #2.Write a comment in the output file for make easier to find the end of the IF block in the assembler code.
    def writeEnd(self, num):
        global file
        endIfLabel = str(num)
        file.write('end_if' + endIfLabel + ':\n')
        file.write('####End of IF' + endIfLabel + '#####\n\n')


#Class nodeIF for only IF sections.
class NodeIFELSE():
    ###Example: if's in C code and assembler code generated
    # C code                                             assembler code generated
    #   ||                                                          ||
    #   ||                                                          ||
    # C code                                             assembler code generated
    #   ||                                                          ||
    #   ||                                                          ||
    #
    # if(expression){                                             if0:                                      
    #     //IF Block                                              movl $0, %ecx
    # }                                                           cmpl %eax, %ecx
    # else{						                                  je else0
    #     //ELSE Block 						                      assembler code for the IF Block
    # } 							                              jmp end_ifelse0
	# 							                                  else0:
	# 							                                  assembler code for the ELSE Block	
    # 								                              end_ifelse0:
	# 							                                  ####End of IFELSE0####

    # if(expression){                                             if0:                                      
    #     one instruction                                         movl $0, %ecx
    #                                                             cmpl %eax, %ecx
    # else{						                                  je else0
    #     one instruction 						                  assembler code for the one instruction
    # } 							                              jmp end_ifelse0
	# 							                                  else0:
	# 							                                  assembler code for the one instruction	
    # 								                              end_ifelse0:
	# 							                                  ####End of IFELSE0####                                                       ####End of IF0####
    ###

    #self.numberBeginIFELSE: counter of ifelse number, we need this for write the if's labels.
    #self.numberEndIFELSE: counter of ifelse number, we need this for write the end of if's labels.
    def __init__(self):
        self.numberBeginIFELSE = 0
        self.numberEndIFELSE = 0

    ###Write begin of IF's sections in assembler(remember that we are storing the values in %eax)
    #1.Write the 'if0:' label in the output file.
    #2.We load $0 in %ecx for make the comparison with %eax and write it. 
    #3.Write the comparison between %eax and 0(%ecx).
    #4.Write 'je end_if', check %eax's values and 0, in the case both are equal then we jump to the end
    #   of IF block. 
    def writeBegin(self):
        global file
        ifLabel = str(self.numberBeginIF)
        file.write('if' + ifLabel + ':\n')
        file.write('movl $0, %ecx\n')
        file.write('cmpl %eax, %ecx\n')
        file.write('je end_if' + ifLabel + '\n')
    
    ###Write end of IF's sections in assembler.
    #1.Write the 'end_if0:' label in the output file.
    #2.Write a comment in the output file for make easier to find the end of the IF block in the assembler code.
    def writeEnd(self, num):
        global file
        endIfLabel = str(self.numberEndELSE)
        file.write('end_if' + str(num) + ':\n')
        file.write('####End of IF' + str(self.numberEndELSE - 1) + '#####\n\n')

#Clase nodo para While
class NodeWhile():
    def escribirInicio(self):
        global file, whileNum
        file.write('cmpl %eax, $0\n' + 'je fin_while' + str(whileNum - 1) + '\n')

    def escribirFinal(self, num):
        global file
        file.write('jmp while'+ str(num) + '\nfin_while' + str(num) + ':\n')

#Para los relacionales usaremos %ecx con valor 0 para hacer las comparaciones pertinentes.
#Clase nodo para AND
class NodeAND(Node):
    #Como los operandos de las operaciones estaran en eax y ebx, usaremos ecx para comparar con 0.
    def escribir(self):
        file.write('movl $0, %ecx' + 'cmpl %eax, %ecx\n' + 'je devolver_falso' + str(contadorRelacional - 1) + '\n' + 'cmpl %ebx, %ecx\n' + 'je devolver_falso' + str(contadorRelacional - 1) + '\n' + 'movl $1, %eax\n' + 'jmp final' + str(contadorRelacional - 1) + '\n' + 'devolver_falso' + str(contadorRelacional - 1) + ':\n' + 
            'movl $0, %eax\n' + 'final' + str(contadorRelacional - 1) + ':\n' )

#Clase nodo para NOT
class NodeNOT(Node):
    def escribir(self):
        file.write('movl $1, %ecx' + 'cmpl %eax, %ecx\n' + 'jge devolver_falso' + str(contadorRelacional - 1) + '\n' + 'movl $1, %eax\n' + 'jmp final' + str(contadorRelacional - 1) + '\n' + 'devolver_falso' + str(contadorRelacional - 1) + ':\n' + 
            'movl $0, %eax\n' + 'final' + str(contadorRelacional - 1) + ':\n' )

#Clase nodo para OR
class NodeOR(Node):
    def escribir(self):
        file.write('movl $1, %ecx'+'cmpl %eax, %ecx\n' + 'jge devolver_true' + str(contadorRelacional - 1) + '\n' + 'cmpl %ebx, %ecx\n' + 'jge devolver_true' + str(contadorRelacional - 1) + '\n' + 'movl $0, %eax\n' + 'jmp final' + str(contadorRelacional - 1) + '\n' + 'devolver_true' + str(contadorRelacional - 1) + ':\n' + 
            'movl $1, %eax\n' + 'final' + str(contadorRelacional) + ':\n' )

#Clase nodo para LESS
class NodeLESS(Node):
    #Como los operandos de las operaciones estaran en eax y ebx, usaremos ecx para comparar con 0.
    def escribir(self):
        file.write('cmpl %eax, %ebx\n' + 'jge devolver_falso' + str(contadorRelacional - 1) + '\n' + 'movl $1, %eax\n' + 'jmp final' + str(contadorRelacional - 1) + '\n' + 'devolver_falso' + str(contadorRelacional - 1) + ':\n' + 
            'movl $0, %eax\n' + 'final' + str(contadorRelacional - 1) + ':\n' )

#Clase nodo para GREATER
class NodeGREATER(Node):
    #Como los operandos de las operaciones estaran en eax y ebx, usaremos ecx para comparar con 0.
    def escribir(self):
        file.write('cmpl %eax, %ebx\n' + 'jle devolver_falso' + str(contadorRelacional - 1) + '\n' + 'movl $1, %eax\n' + 'jmp final' + str(contadorRelacional - 1) + '\n' + 'devolver_falso' + str(contadorRelacional - 1) + ':\n' + 
            'movl $0, %eax\n' + 'final' + str(contadorRelacional - 1) + ':\n' )

#Clase nodo para Not Equal
class NodeNotEqual(Node):
    #Como los operandos de las operaciones estaran en eax y ebx, usaremos ecx para comparar con 0.
    def escribir(self):
        file.write('cmpl %eax, %ebx\n' + 'je devolver_falso' + str(contadorRelacional - 1) + '\n' + 'movl $1, %eax\n' + 'jmp final' + str(contadorRelacional - 1) + '\n' + 'devolver_falso' + str(contadorRelacional - 1) + ':\n' + 
            'movl $0, %eax\n' + 'final' + str(contadorRelacional - 1) + ':\n' )

#Clase nodo para Equal
class NodeEqual(Node):
    #Como los operandos de las operaciones estaran en eax y ebx, usaremos ecx para comparar con 0.
    def escribir(self):
        file.write('cmpl %eax, %ebx\n' + 'jne devolver_falso' + str(contadorRelacional - 1) + '\n' + 'movl $1, %eax\n' + 'jmp final' + str(contadorRelacional - 1) + '\n' + 'devolver_falso' + str(contadorRelacional - 1) + ':\n' + 
            'movl $0, %eax\n' + 'final' + str(contadorRelacional - 1) + ':\n' )

#Clase nodo para Less Equal
class NodeLessEqual(Node):
    #Como los operandos de las operaciones estaran en eax y ebx, usaremos ecx para comparar con 0.
    def escribir(self):
        file.write('cmpl %eax, %ebx\n' + 'jg devolver_falso' + str(contadorRelacional - 1) + '\n' + 'movl $1, %eax\n' + 'jmp final' + str(contadorRelacional - 1) + '\n' + 'devolver_falso' + str(contadorRelacional - 1) + ':\n' + 
            'movl $0, %eax\n' + 'final' + str(contadorRelacional - 1) + ':\n' )

#Clase nodo para GREATER Equal
class NodeGreaterEqual(Node):
    #Como los operandos de las operaciones estaran en eax y ebx, usaremos ecx para comparar con 0.
    def escribir(self):
        file.write('cmpl %eax, %ebx\n' + 'jl devolver_falso' + str(contadorRelacional - 1) + '\n' + 'movl $1, %eax\n' + 'jmp final' + str(contadorRelacional - 1) + '\n' + 'devolver_falso' + str(contadorRelacional - 1) + ':\n' + 
            'movl $0, %eax\n' + 'final' + str(contadorRelacional - 1) + ':\n' )

#Clase nodo para la division
class NodeDiv(Node):
    def escribir(self):
        file.write('cdq\ndivl %ebx\n')

#Clase nodo para el producto
class NodeProd(Node):
    def escribir(self):
        file.write('mul ' + '%ebx' + ',' + '%eax\n')

#Clase nodo para el menos unario
class NodeUMinus(Node):
    def escribir(self):
        #Para cambiar el signo usamos la resta : 0 - valor y lo almacenamos en eax
        file.write('movl  $0, %ebx\nsubl %ebx, %eax\n')

#Clase nodo para la resta
class NodeResta(Node):
    def escribir(self):
        file.write('subl %eax, %ebx\nmovl %ebx, %eax\n')

#Clase nodo para la suma
class NodeSuma(Node):
    def escribir(self):
        file.write('addl ' + '%ebx' + ', %eax\n')
   
#Clase nodo para la división modular
class NodeMod(Node):
    def escribir(self):
        global modulo
        file.write('cdq\ndivl %ebx\n')
        modulo = True

#Clase nodo para los IDs
class NodeId(Node):
    #Metodo para escribir el codigo ensamblador que generaria la carga del valor de una variable
    #Recibe: Una lista de variable que se tiene en el ambito local y global de una funcion dada.
    def escribir(self,variables):
        global primerFactor
        #Comprobar si una variable dada esta declarada previamente.
        if variables.get(self.id) != None:
            variable = variables[self.id]
            if primerFactor:
                primerFactor = False
                file.write('movl ' + str(variable) + '(%ebp)' +', %eax\n')
            else:
                file.write('movl ' + str(variable) + '(%ebp)' +', %ebx\n')
        else:
            print('Variable no declarada, se termina la compilacion')
            exit(0)

#Clase nodo para los numeros
class NodeNumero(Node):
    #Ctor. de la clase nodo de numeros
    def __init__(self, valor):
        self.valor = valor

    #Metodo para escribir el codigo ensamblador que generaria la carga del valor de un numero cte.
    def escribir(self):
        global primerFactor
        if primerFactor:
            primerFactor = False
            file.write('movl $' + str(self.valor) +', %eax\n')
        else:
            file.write('movl $' + str(self.valor) +', %ebx\n')

#Clase nodo para los returns
class NodeReturn(Node):
    def __init__(self, valor):
        self.valor = valor
    
    def escribir(self):
        file.write('movl %ebp, %esp\npopl %esp\nret\n')

#Clase nodo para los globales
class NodeGlobal(Node):
    def escribir(self, ID):
        global file, argumentosFunciones
        file.write('.text\n' + '.globl ' + ID + '\n.type ' + ID + ', @function\n\n')
        argumentosFunciones[ID] = []

    def escribirVariable(self, ID):
        global variablesGlobales
        variablesGlobales.append('.comm ' + ID + ', 4, 4\n\n')

    def escribirAcceso(self, ID):
        global file
        file.write('movl ' + ID + ', %eax\n')        

#Clase nodo para los Push
class NodePush(Node):
    def escribir(self, posicion):
        global file
        file.write('movl ' + str(posicion) + '(%ebp), %eax\n'  + 'pushl %eax\n')
    
    def escribirSoloPush(self):
        global file
        file.write('pushl %eax\n')

    def escribirCte(self, cte):
        global file
        file.write('pushl $' + cte + '\n')

    def escribirGlobal(self, ID):
        global file
        file.write('pushl $' + ID + '\n')
    
#Clese nodo para los Push de las referencias a variables
class NodePushRef(Node):
    def escribir(self, index):
        global file
        file.write('leal ' + str(index) + '(%ebp), %eax\n')        

#Clase nodo para los Push de las cadenas
class NodePushCadena(Node):
    def escribir(self, string):
        global cadenas, file
        file.write('movl $.LC' + str(cadenas[string]) + ', %edx\n' + 'pushl %edx \n')

#Clase nodo para las llamadas a las funciones
class NodeCall(Node):
    def escribir(self, p):
        global file, N
        file.write('call ' + p + '\n' + 'addl $' + str(4 * N) + ', %esp\n')

#Clase nodo para los inicios de la declaraciones a funciones
class NodeFunction(Node):
    def escribir(self, ID, argumentos_entrada):
        global file
        file.write(ID + ':\n' + 'pushl %ebp\n' + 'movl %esp, %ebp\n')

class NodeAsignarGlobal(Node):
    def escribir(self, ID):
        global file, modulo
        if modulo:
            file.write('movl %edx,'+ ID + '\n')
            modulo = False
        else:
            file.write('movl %eax,'+ ID + '\n')

class NodeLocalAssignment(Node):
    def escribir(self, varPos):
        global file, modulo
        if modulo:
            file.write('movl %edx,'+ str(varPos) + '(%ebp)\n')
            modulo = False
        else:
            file.write('movl %eax,'+ str(varPos) + '(%ebp)\n')

class NodeReference(Node):
    def obtainLocalReference(self, pos):
        global file
        file.write('leal ' + str(pos) + '(%ebp), %eax\n')

    def obtainGlobalReference(self, ID):
        global file
        file.write('leal ' + ID + ', %eax\n')

class NodeDeclaracion(Node):
    def escribir(self):
        global  file
        file.write('subl $4, %ebp\n')

class Lexical(Lexer):
    tokens = {CHECK,POINT, INT,FLOAT, AND, TIPO, ID, OR, EQUAL, LESS_EQ, GRE_EQ, NOT_EQ, R_ARROW, CADENA, RETURN, PRINTF, SCANF, WHILE, IF, ELSE} #, OPERATOR
    ignore = ' \t'
    literals = {'!', ';', '+', '-', '/', '*', '%', '(', ')',',','<','>','=','[',']', '{', '}', '&', '/'}
    
    POINT = r'\.'
    AND = r'&&'
    OR = r'\|\|'
    EQUAL = r'=='
    LESS_EQ = r'<='
    GRE_EQ = r'>='
    NOT_EQ = r'!='
    R_ARROW = r'->'
    PRINTF = r'printf'
    SCANF = r'scanf'    
    WHILE = r'while'
    IF = r'if'
    ELSE = r'else'
    ignore_comment = r'\/\/[\,\*\-\(\)a-zA-Z0-9 :\.]*'
    ignore_block = r'\/\*[\-\(\)a-zA-Z0-9 :\.\,\*\;\n]*\*\/'
    # Tokens
    @_(r'((((int\*|float)|char)|void)|int)')
    def TIPO(self, t):
        t.value = str(t.value)
        return t
    
    @_(r'check')
    def CHECK(self, t):
        t.value = str(t.value)
        return t
    

    @_(r'[0-9]+[\.][0-9]+')
    def FLOAT(self, t):
        t.value = math.floor(float(t.value))
        nodo = NodeNumero(t.value)
        nodo.escribir()
        return t
    
    @_(r'[0-9]+')
    def INT(self, t):
        t.value = int(t.value)
        nodo = NodeNumero(t.value)
        nodo.escribir()
        return t
     
    #Cuando se lee una cadena, se guarda en el diccionario 'cadenas' con el número del contador de cadenas, con eso sabremos el número respectivo a una cadena dada.
    @_(r'"([A-Za-z_0-9% :=|\\]|\\n)+"')
    def CADENA(self, t):
        global cadenas, stringNum
        t.value = str(t.value)
        if cadenas.get(t.value) == None:
            cadenas.update({t.value: stringNum})
            stringNum += 1
        return t

    @_(r'return')
    def RETURN(self, t):
        return t
    
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    ID = r'[A-Za-z_][A-Za-z_0-9]*'
    

class Syntactic(Parser):
    
    debugfile = 'parser.out'
    ###Use Lexical's token
    tokens = Lexical.tokens
    ###Precedence rules of our grammar
    precedence = (
        ('left', '+', '-'),
        ('left', '*', '/'),
        ('left', '<', '>'),
        ('left', '%',R_ARROW),
        ('nonassoc', GRE_EQ, LESS_EQ),
        ('nonassoc', EQUAL, NOT_EQ),
        )


    


    ###Ctor of our parser:
    # localVariables: dict(made of pairs of [variableId, variableType]) of local variables in a given function, it will contain identifiers and types.
    # functionReturntype: string that contains the type of data that a given function returns(int or int*)
    # assemblerPositions: dict(made of pairs of [variableId, positionInStack]) of local variables in a given function, it will contain identifiers and stack positions.
    # globalVariables:  dict(made of pairs of [variableId, variableType]) of global scope in the C code, it will contain identifiers and types.
    # functionInputVariables: list(made of strings) that contains the types of input parameters of a given function, we will need this for typechecking in calls.
    # nodeIf_Else 
    # nodeWhile_Loop 
    def __init__(self):
        self.localVariables = {}
        self.functionReturntype = 'int'
        self.assemblerPositions = {}
        self.globalVariables = {}
        self.functionInputVariables = []
        self.nodeIF = NodeIF()
        self.nodeIF_ELSE = NodeIFELSE()
        self.nodeWHILE_Loop = NodeWhile()

    #Epsilon rule.
    @_(' ')
    def ε(self, p):
        return " "
    

    ######Main rule
    #1.This production accepts a generic function implementation:   
    #   =>  int main(){...}
    @_('input function_body')
    def input(self, p):
        pass

    #2.This production accepts a global declaration:    
    #   =>  int a;  int b = 5;  //This is global scope
    @_('input globalDeclaration ";"')
    def input(self, p):
        return ' '

    #3.This production accepts the epsilon token:
    @_('ε')
    def input(self, p):
        print(p.ε)

    ######Global declaration
    #1.This production accepts a variable declaration:   
    #   =>  int a; //This is global scope
    @_('TIPO ID')
    def globalDeclaration(self, p):
        nodo = NodeGlobal()
        nodo.escribirVariable(p.ID)
        self.globalVariables[p.ID] = p.TIPO
        return p.ID

    #1.This production accepts a variable initialization:   
    #   =>  int a = 5; //This is global scope
    @_('TIPO ID "=" INT')
    def globalDeclaration(self, p):
        nodo = NodeGlobal()
        nodo.escribirVariable(p.ID)
        self.globalVariables[p.ID] = p.TIPO
        return p.ID


    ####Regla para la implementacion de funciones, de forma generíca
    @_('TIPO ID "(" args_list ")" empty1 "{"  instruction "}"')
    def function_body(self, p):
        global file, varPos
        nodo = NodeReturn(p.ID)
        nodo.escribir()
        file.write('#####FIN DE LA FUNCION ' + p.ID + ' ############\n\n')
        varPos = -4
        return 'funcion ' + p.ID + ' traducida'

    @_('TIPO ID "(" ")" empty_1 "{"  instruction "}"')
    def function_body(self, p):
        global file, varPos
        nodo = NodeReturn(p.ID)
        nodo.escribir()
        varPos = -4
        file.write('#####FIN DE LA FUNCION ' + p.ID + ' ############\n\n')
        return 'funcion ' + p.ID + ' traducida'

 #Con esta regla vacia lo que hacemos es escribir en ensamblador el comienzo de una funcion y adquirir las posiciones en pila de las variables de input de args_list.
    @_(' ')
    def empty_1(self, p):
        global contador_entrada, nombreFuncion, tipoReturn, argumentos_entrada, varPos, tiposFunciones, argumentosFunciones
        tipoReturn = p[-4]
        self.assemblerPositions = {}
        self.localVariables = {}
        nombreFuncion = p[-3]
        contador_entrada = 0
        nodo = NodeGlobal()
        nodo.escribir(p[-3])
        nodo = NodeFunction()
        nodo.escribir(p[-3], 0)
        tiposFunciones.update({p[-3] : p[-4]})
        
    #Con esta regla vacia lo que hacemos es escribir en ensamblador el comienzo de una funcion y adquirir las posiciones en pila de las variables de entrada de args_list.
    @_(' ')
    def empty1(self, p):
        global contador_entrada, nombreFuncion, tipoReturn, nombreFuncion, argumentos_entrada, varPos, argumentosFunciones
        varPos = -4
        tipoReturn = p[-5]
        nombreFuncion = p[-4]
        self.assemblerPositions = {}
        self.localVariables = {}
        contador_entrada = 0
        nodo = NodeGlobal()
        nodo.escribir(p[-4])
        self.functionInputVariables.reverse()
        argumentosFunciones[p[-4]] = self.functionInputVariables
        tiposFunciones.update({p[-4] : p[-5]})
        nodo = NodeFunction()
        contador_entrada = 1
        inputs = []
        if len(p[-2])>0: #Comprobar si args_list devuelve algun elemento
            i = 0
            while i < len(p[-2]): #Ir elemento por elemento que devuelve args_list, se crea una lista con los identificadores de los argumentos de entrada y su posicion en la pila.
                argumentos_entrada[p[-2][i + 1]] = contador_entrada * 4 + 4
                contador_entrada += 1
                i+=2
            nodo.escribir(p[-4], p[-2])
            self.assemblerPositions = dict(argumentos_entrada.items()) 
            i = 0
            while i < len(self.assemblerPositions.keys()):
                self.localVariables[list(self.assemblerPositions.keys())[i]] = ['int',0] #Dar valores por defecto para que no produzcan errores con las consultas implementadas en puntos anteriores de la practicas.
                i+=1
            
        else:
            nodo.escribir(p[-4], 0)
        self.functionInputVariables = []
    
    #Los argumentos de entrada pueden ser ninguno, uno o más de uno, para la devolucion de los mismos, iremos concatenando pares de elementos de la forma(siendo N el numero total de argumentos)
        #[N, ID0, N - 1, ID1, N - 2, ID2, ....]   
    @_('TIPO ID')
    def args_list(self, p):
        global argumentos_entrada, contador_entrada, argumentosFunciones
        self.functionInputVariables.append(p.TIPO)
        return [contador_entrada, p.ID]

    @_('TIPO ID "," args_list')
    def args_list(self, p):
        global contador_entrada, argumentos_entrada, argumentosFunciones
        self.functionInputVariables.append(p.TIPO)
        return [contador_entrada, p.ID] + p.args_list
        
    #####Reglas para instrucciones, puede ser que ninguna o no.
    @_('epsilon')
    def instruction(self, p):
        return ' '

    
    @_('instruction sentencia')
    def instruction(self, p):
        global numLine
        try:
            if not('while' in p.sentencia):
                if not('if' in p.sentencia):
                    file.write('#Fin de la linea ' + str(numLine) + '#\n\n')
        except TypeError:
            file.write('#Fin de la linea ' + str(numLine) + '#\n\n')
        numLine += 1
        return p.sentencia

    #####Reglas para sentencias.
    @_(' declaracion ";" ')
    def sentencia(self, p):
        global primerFactor, referenciaOperador
        primerFactor = True
        referenciaOperador = False
        return p.declaracion
    
    @_(' asignacion ";" ')
    def sentencia(self, p):
        global primerFactor, referenciaOperador
        primerFactor = True
        referenciaOperador = False
        return p.asignacion

    #En este caso contemplamos llamadas a funciones/procedimientos como printf, scanf, u otras.
    @_(' function ";" ')
    def sentencia(self, p):
        global primerFactor, referenciaOperador
        primerFactor = True
        referenciaOperador = False
        return p.function

    #Tambien puede ser un if/if-else/while.
    @_('IF empty9 "(" expresion empty10 ")" sentencia')
    def sentencia(self, p):
        global file, ifelseNum
        self.nodeIf_Else.writeEnd(p.empty9)
        file.write('####FIN DE IF_ELSE' + str(ifelseNum - 1) + '#####\n\n')
        global primerFactor
        primerFactor = True
        return 'if' + p.IF +' traducido'


    @_('IF empty9 "(" expresion empty10 ")" "{" instruction "}"')
    def sentencia(self, p):
        global file, ifelseNum
        nodo = NodeIF()
        nodo.escribirFinal(p.empty9)
        file.write('####FIN DE IF_ELSE' + str(ifelseNum - 1) + '#####\n\n')
        global primerFactor
        primerFactor = True
        return 'if' + p.IF +' traducido'

    @_('IF empty9 "(" expresion empty10 ")" "{" instruction "}" ELSE empty11 "{" instruction "}"')
    def sentencia(self, p):
        global file, ifelseNum
        nodo = NodeIF()
        nodo.escribirFinal(p.empty9)
        file.write('####FIN DE IF_ELSE' + str(ifelseNum - 1) + '#####\n\n')
        global primerFactor
        primerFactor = True
        return 'if' + p.IF +' traducido'
        
    #Este empty escribe la parte correspondiente al final de la seccion if de un if/else, 
    @_(' ')
    def empty11(self, p):
        global file, ifelseNum
        file.write('jmp fin_ifelse'+ str(p[-9]) + ':\n' + 'else' + str(p[-9]) + ':\n')
        return ifelseNum

    @_(' ')
    def empty9(self, p):
        global file,ifelseNum
        file.write('if' + str(ifelseNum) + ':\n')
        ifelseNum += 1
        return ifelseNum-1

    @_(' ')
    def empty10(self, p):
        global primerFactor
        nodo = NodeIF()
        nodo.escribirInicio()
        primerFactor = True


    @_('WHILE empty7 "(" expresion empty8 ")" "{" instruction "}"')
    def sentencia(self, p):
        global file, whileNum
        nodo = NodeWhile()
        nodo.escribirFinal(p.empty7)
        file.write('####FIN DE WHILE' + str(whileNum - 1) +'####\n\n')
        global primerFactor
        primerFactor = True
        return 'while ' + p.WHILE + ' traducido'

    @_('WHILE empty7 "(" expresion empty8 ")" sentencia')
    def sentencia(self, p):
        global file, whileNum
        nodo = NodeWhile()
        nodo.escribirFinal(p.empty7)
        file.write('####FIN DE WHILE' + str(whileNum - 1) +'####\n\n')
        global primerFactor
        primerFactor = True
        return 'while ' + p.WHILE + ' traducido'

    @_(' ')
    def empty7(self, p):
        global file,whileNum
        file.write('while' + str(whileNum) + ':\n')
        whileNum += 1
        return whileNum-1

    @_(' ')
    def empty8(self, p):
        global file, primerFactor
        nodo = NodeWhile()
        nodo.escribirInicio()
        primerFactor = True

    @_(' expresion ";" ')
    def sentencia(self, p):
        global primerFactor
        primerFactor = True
        return p.expresion    
    
    @_('devolver ";" ')
    def sentencia(self, p):
        global primerFactor
        primerFactor = True
        return p.devolver

    @_('RETURN "&" ID')
    def devolver(self, p):
        global tipoReturn
        nodo = NodeReference()
        if tipoReturn == 'int*':
            if p.ID in self.assemblerPositions:
                if self.localVariables[p.ID][0] != 'int':
                    print('Tipo incorrecto de return, se termina la traduccion')
                    exit(0)    
                nodo.obtainLocalReference(self.assemblerPositions[p.ID])
            elif p.ID in self.globalVariables:
                if self.globalVariables[p.ID][0] != 'int':
                    print('Tipo incorrecto de return, se termina la traduccion')
                    exit(0)
                nodo.obtainGlobalReference(p.ID)
        else:    
            print('Tipo incorrecto de return, se termina la traduccion')
            exit(0)
        return p.ID

    @_('RETURN expresion')
    def devolver(self, p):
        global primerFactor, tipoReturn 
        primerFactor = True
        if tipoReturn != 'int':
            print('Tipo incorrecto de return, se termina la traducción')
            exit(0)
        return p.expresion

    @_('RETURN ID')
    def devolver(self, p):
        global primerFactor, tipoReturn, nombreFuncion
        primerFactor = True
        #tipo = tiposFunciones[nombreFuncion]
        if p.ID in self.localVariables:
            tipo = self.localVariables[p.ID][0]
        elif p.ID in self.globalVariables:
            tipo = self.globalVariables[p.ID][0]
        if tipo != tipoReturn:
            print('Tipo incorrecto de return, se termina la traduccion')
            exit(0)
        return p.ID

    @_('RETURN function')
    def devolver(self, p):
        global primerFactor, tipoReturn, nombreFuncion
        primerFactor = True
        tipo1 = tiposFunciones[nombreFuncion]
        if tipo1 != self.functionReturntype:
            print('Tipo incorrecto de return, se termina la traduccion')
            exit(0)
        return p.function


    ######Reglas para una declaracion
    @_('TIPO ID')
    def declaracion(self,p):
        global varPos
        if not(p.ID in self.localVariables): #Guardar variable local.
            self.localVariables[p.ID] = [p.TIPO, 0]
            self.assemblerPositions[p.ID] = varPos        
            nodo = NodeDeclaracion()
            nodo.escribir()
        else:
            print('Variable ya declarada, se termina la traduccion')
            exit(0)
        if p.TIPO == 'int':
            self.localVariables[p.ID] = [p.TIPO, 0]
        self.assemblerPositions[p.ID] = varPos
        varPos-=4
        return p.ID

    #Inicializar
    @_('TIPO ID asignar')
    def declaracion(self,p):
        global varPos
        if not(p.ID in self.localVariables): #Guardar variable local.
            self.localVariables[p.ID] = [p.TIPO, 0]
            self.assemblerPositions[p.ID] = varPos        
            nodo = NodeDeclaracion()
            nodo.escribir()
        else:
            print('Variable ya declarada, se termina la traduccion')
            exit(0)
        if p.asignar == 'void':
            print('No se puede realizar una asignacion con un procedimiento, se termina la traduccion')
            exit(0)
        elif p.asignar == 'int' or p.asignar == 'int*':
            self.comprobarTiposFuncion(p.ID, p.asignar)
            self.cambiarValorFuncion(p.ID,p.asignar)
        else:
            self.comprobarTiposVariables(p.ID, p.asignar)
            self.cambiarValorVariables(p.ID, p.asignar)
        varPos-=4
        return "Declaracion bien"

    ######Regla para una asignacion
    @_('ID asignar')
    def asignacion(self,p):
        global modulo, variablesGlobales, tiposFunciones  
        #Seria poner la condicion de que p.asignar no sea void   
        if not(p.ID in self.globalVariables) and not(p.ID in self.localVariables):
            print("Variable no declarada, se termina la traduccion : " + ID)
            exit(0)
        if p.asignar == 'void':
            print('No se puede realizar una asignacion con un procedimiento, se termina la traduccion')
            exit(0)
        if p.asignar == 'int' or p.asignar == 'int*':
            self.comprobarTiposFuncion(p.ID, p.asignar)
            self.cambiarValorFuncion(p.ID,p.asignar)
        else:
            self.comprobarTiposVariables(p.ID, p.asignar)
            self.cambiarValorVariables(p.ID, p.asignar)
        return "Asignacion bien"

    def comprobarTiposVariables(self, id1, id2):
        global referenciaOperador
        try:
            if type(1) == type(int(id2)): #Comprobar si se trata de un numero ctr
                if self.localVariables[id1][0] != 'int':
                    print('Asignacion entre tipos distintos: ' + str(id1) + ' = ' + str(id2) + ' , son de tipos ' + self.localVariables[id1][0] + ' y  int, se termina la traduccion')
                    exit(0)
        except ValueError:
            if id2 in self.localVariables:
                tipo2 = self.localVariables[id2][0]
            elif id2 in self.globalVariables:
                tipo2 = self.globalVariables[id2][1]
            if id1 in self.localVariables:
                tipo1 = self.localVariables[id1][0]
            elif id1 in self.globalVariables:
                tipo1 = self.globalVariables[id1][1]            
            if referenciaOperador == True and tipo1 == 'int*':
                if tipo2 != 'int':
                    print('Asignacion entre tipos distintos: ' + id1 + ' = ' + id2 + ', son de tipos ' + self.localVariables[id1][0] + ' y ' + self.localVariables[id2][0] + '\nSe termina la traduccion')
                    exit(0)
            elif tipo1 != tipo2:
                print('Asignacion entre tipos distintos: ' + id1 + ' = ' + id2 + ', son de tipos ' + tipo1 + ' y ' + tipo2 + '\nSe termina la traduccion')
                exit(0)
        return 
    
    def comprobarTiposFuncion(self, id, tipo):
        if id in self.localVariables:
            if(self.localVariables[id][0] != tipo):
                print('Asignacion entre tipos distintos: ' + id + ' = ' + tipo + '\nSe termina la traduccion')
                exit(0)
        elif id in self.globalVariables:
            if self.globalVariables[id][1] != tipo:
                print('Asignacion entre tipos distintos: ' + id + ' = ' + tipo + '\nSe termina la traduccion')
                exit(0)
        return 

    def cambiarValorFuncion(self, ID, TIPO):
        if ID in self.localVariables:
            if self.localVariables[ID][0] != TIPO:
                print('Asignacion a ' + ID +' entre tipos distintos ' + self.localVariables[ID][0] + ' y ' + TIPO)
                exit(0)
            varPos = self.assemblerPositions[ID]
            nodo = NodeLocalAssignment()
            nodo.escribir(varPos)  
        elif ID in self.globalVariables:
            if self.globalVariables[ID][1] != TIPO:
                print('Asignacion entre tipos distintos: ' + str(ID) + ' = ' + str(TIPO) + '\nSe termina la traduccion')
                exit(0)
            nodo = NodeAsignarGlobal()
            nodo.escribir(ID)
        return

    def cambiarValorVariables(self, ID, valor):
        if self.checkID(ID):
            stackPosition = self.assemblerPositions[ID]
            node = NodeLocalAssignment()
            node.escribir(varPos)
        elif ID in self.globalVariables:
            node = NodeAsignarGlobal()
            node.escribir(ID)


    ######Asignaciones
    @_('"=" ID')
    def asignar(self, p):
        return p.ID #Ir a ID y a devolver su valor
    
    
    @_('"=" expresion')
    def asignar(self, p):
        return p.expresion

    @_('"=" unario')
    def asignar(self, p):
        return p.unario
    

    @_('"=" function')
    def asignar(self, p):
        return p.function

    
    @_('"=" "&" ID')
    def asignar(self, p):
        node = NodeReference()
        #Search in local variables of a function
        if p.ID in self.localVariables: #Check if the p.ID exists as local variable
            if self.localVariables[p.ID] == 'int':  #Check if the p.ID is int
                node.obtainLocalReference(self.assemblerPositions[p.ID]) #Write assembler instruction
            else:   #Error case
                error('Obtain the reference of a pointer variable is not supported')
        #Search in global variables of C code
        elif p.ID in self.globalVariables: #Check if the p.ID exists as global variable
            if self.globalVariables[p.ID] == 'int': #Check if the p.ID is int
                node.obtainGlobalReference(p.ID)  #Write assembler instruction
            else:   #Error case
                error('Obtain the reference of a pointer variable is not supported')
        else:
            error('\'' + p.ID + '\' undeclared')
        return 'int*'

    ######Regla para una funcion
    @_('PRINTF "(" CADENA resto ")" empty5')
    def function(self, p):
        global N, tiposFunciones
        self.functionReturntype = 'int'
        N = 0
        funcion = p.PRINTF + "(" + p.CADENA + str(p.resto) + ")"
        return 'int'
    
    @_('SCANF "(" CADENA scanf_args ")" empty6')
    def function(self, p):
        global N
        self.functionReturntype = 'int' 
        N = 0
        funcion = p.SCANF + "(" + p.CADENA + str(p.scanf_args) + ")"
        return 'int'

    @_('"," "&" ID scanf_args')
    def scanf_args(self, p):
        global N
        N+=1
        if p.ID != ' ':
            lista =  p.ID + ',' + p.scanf_args
        return lista

    @_('"," "&" ID')
    def scanf_args(self, p):
        global N
        N+=1
        lista = str(p.ID) 
        return lista

    @_(' ')
    def empty6(self, p):
        lista_args = p[-2]
        global file, N
        lista = p[-2].split(',')
        i = len(lista) - 1
        if p[-2][0] == ' ':
            i-=1
        while i >= 0:
            node = NodePush()
            if lista[i] in self.globalVariables:
                node.escribirGlobal(lista[i])
            elif lista[i] in self.assemblerPositions:
                pos = self.assemblerPositions[lista[i]]
                nodeP = NodePushRef()
                nodeP.escribir(pos)
            else:
                print('Error: variable no declarada, se termina la traduccion')
                exit(0)
            i-=1
        node = NodePushCadena()
        node.escribir(p[-3])
        N+=1
        node = NodeCall()
        node.escribir(p[-5])


    @_(' ')
    def resto(self, p):
        global N, stringNum, cadenas 
        N+=1
        return ' '

    @_('"," ID resto')
    def resto(self, p):
        global N
        N+=1
        lista = str(p.ID) 
        if p.resto != ' ':
            lista += (',' + p.resto)
        return lista

    @_('"," INT resto')
    def resto(self, p):
        global N
        N+=1
        lista = str(p.INT) 
        if p.resto != ' ':
            lista += (',' + p.resto)
        return lista

    @_('"," function resto')
    def resto(self, p):
        global N
        node = NodePush()
        node.escribirSoloPush()
        N+=1
        return ' '


    @_(' ')
    def empty5(self, p):
        lista_args = p[-2]
        global file, N
        lista = p[-2].split(',')
        i = len(lista) - 1
        if p[-2][0] == ' ':
            i-=1
        while i > -1:
            node = NodePush()
            if lista[i] in self.assemblerPositions:
                pos = self.assemblerPositions[lista[i]]
                node.escribir(pos)
            elif lista[i] in self.globalVariables:
                node.escribirCte(lista[i])
            else:
                print('Error: variable no declarada, se termina la traduccion')
                exit(0) 
            i-=1
        node = NodePushCadena()
        node.escribir(p[-3])
        node = NodeCall()
        node.escribir(p[-5])


        
    #####Reglas para funciones
    @_(' ID "(" argumentos ")" empty4') # quitara los parametros
    def function(self, p):
        global N, tiposFunciones
        N = 0
        funcion = p.ID + "(" + str(p.argumentos) + ")"
        try:
            resultado =  tiposFunciones[p.ID]
            self.functionReturntype = resultado
        except KeyError:
            error('\'' + p.ID + '\' undeclared')
        return resultado 
    
    @_(' ID "(" epsilon ")" ')
    def function(self, p):
        return p.ID + '(' + p.epsilon + ')'
    
    @_(' ')
    def empty4(self, p):
        global file, N, argumentosFunciones
        lista = p[-2].split(',')
        i = len(lista) - 1
        if p[-2] == ' ':
            i-=1
        while i > -1:
            nodo = NodePush()
            if lista[i] in self.assemblerPositions:
                if self.localVariables[lista[i]][0] == argumentosFunciones[p[-4]][i]:
                    pos = self.assemblerPositions[lista[i]]
                    nodo.escribir(pos)
                else:
                    print('Error en la llamada a ' + p[-4] + ', se esperaba un ' + argumentosFunciones[p[-4]][i] + ' no un ' + self.localVariables[lista[i]][0])
            elif lista[i] in self.globalVariables:
                if self.globalVariables[lista[i]][1] == argumentosFunciones[p[-4]][i]:
                    #pos = self.globalVariables[lista[i]]
                    #nodo.escribir(pos)
                    nodo.escribirCte(lista[i]) 
                else:
                    print('Error en la llamada a ' + str(p[-4]) + ', se esperaba un ' + argumentosFunciones[p[-4]][i] + ' no un ' + str(self.globalVariables[lista[i]][1]))
            i-=1
        nodo = NodeCall()
        nodo.escribir(p[-4])
        
        

    @_(' ')
    def empty3(self, p):
        global N
        N+=1
        #Meter en la pila segun los argumentos

    ######Reglas para listas de argumentos:
    @_('valores empty3 ')
    def argumentos(self, p):
        
        return str(p.valores)
    
    @_('valores "," empty3 argumentos')
    def argumentos(self, p):
        return str(p.valores) + "," + str(p.argumentos)
    
    
    ######Reglas para valores.
    @_('CADENA')
    def valores(self, p):
        return p.CADENA
    
    @_('ID')
    def valores(self, p):
        if p.ID in self.globalVariables:
            node = NodeGlobal()
            node.escribirAcceso(p.ID)
        elif p.ID in self.localVariables:
            nodo = NodeId()
            nodo.escribir(self.assemblerPositions)
        else:
            print('Variable no ' + p.ID +' declarada, se termina la traduccion\n')
            exit(0)
        return p.ID
    
    @_('unario')
    def valores(self, p):
        return p.unario
    
    @_('function')
    def valores(self, p):
        return p.function
    
    
####Operadores
    @_('or_ OR unario')
    def or_(self, p):
        nodo = NodeOR()
        nodo.escribir()
        return p.or_ or p.expresion
    
    #Caso de menor prioridad, solo un operando factor.
    @_('unario')
    def or_(self, p):
        return p.unario
    

    @_('and_ AND or_')
    def and_(self, p):
        nodo = NodeAND()
        nodo.escribir()
        return p.and_ and p.or_
    
    #Caso de menor prioridad, operacion or
    @_('or_')
    def and_(self, p):
        return  p.or_
    
    #Reglas compraing
    @_('comparing EQUAL and_')
    def comparing(self, p):
        nodo = NodeEqual()
        nodo.escribir()
        return p.comparing == p.and_
    
    @_('comparing NOT_EQ and_')
    def comparing(self, p):
        nodo = NodeNotEqual()
        nodo.escribir()
        return p.comparing != p.and_
    
    #Caso de menor prioridad, operacion and
    @_(' and_')
    def comparing(self, p):
        return  p.and_
    
    #Reglas logicas
    @_('logicos "<" comparing')
    def logicos(self, p):
        nodo = NodeLESS()
        nodo.escribir()
        return p.logicos < p.comparing
    
    @_('logicos ">" comparing')
    def logicos(self, p):
        nodo = NodeGREATER()
        nodo.escribir()
        return p.logicos > p.comparing
    
    @_('logicos GRE_EQ comparing')
    def logicos(self, p):
        nodo = NodeGreaterEqual()
        nodo.escribir()
        return p.logicos >= p.comparing
    
    @_('logicos LESS_EQ comparing')
    def logicos(self, p):
        nodo = NodeLessEqual()
        nodo.escribir()
        return p.logicos <= p.comparing
    
    #Caso de menor prioridad, comparaciones
    @_('comparing')
    def logicos(self, p):
        return p.comparing
    

    #Reglas para la suma y la resta
    @_('sum_res "+" logicos')
    def sum_res(self, p):
        nodo = NodeSuma()
        nodo.escribir()
        try:
            return p.sum_res + p.logicos
        except TypeError:
            return str(p.sum_res) + str(p.logicos)

    @_('sum_res "-" logicos')
    def sum_res(self, p):
        nodo = NodeResta()
        nodo.escribir()
        return p.sum_res - p.logicos
    
    #Caso de menor prioridad, comparaciones
    @_('logicos')
    def sum_res(self, p):
        return p.logicos
    
    #####Reglas para el producto, dision y el modulo
    @_('expresion "/" sum_res')
    def expresion(self, p):
        nodo = NodeDiv()
        nodo.escribir()
        return p.expresion / p.sum_res
    
    @_('expresion "%" sum_res')
    def expresion(self, p):
        nodo = NodeMod()
        nodo.escribir()
        return p.expresion % p.sum_res
    
    @_('expresion "*" sum_res')
    def expresion(self, p):
        nodo = NodeProd()
        nodo.escribir()
        return p.expresion * p.sum_res
    

    #Operaciones de menor prioridad, suma y resta
    @_('sum_res')
    def expresion(self, p):
        return p.sum_res
    
    #Reglas unarias
    @_('"-" unario')
    def unario(self, p):
        nodo = NodeUMinus(None)
        nodo.escribir()
        return -p.unario
    
    @_(' "!" unario ')
    def unario(self, p):
        nodo = NodeNOT()
        nodo.escribir()
        return not(p.unario)
    
    @_('factor')
    def unario(self, p):
        return p.factor

 
    ####Uso de IDs
    @_('ID')   
    def factor(self, p):
        if self.assemblerPositions.get(p.ID) != None:
            try:
                nodo = NodeId()
                nodo.escribir(self.assemblerPositions)
                return self.localVariables[p.ID][1]
            except IndexError:
                nodo = NodeId()
                nodo.escribir(self.assemblerPositions)
                return self.localVariables[p.ID]
        if not(p.ID in self.localVariables): #Comprobar la existencia del ID
            return("Variable no declarada, se cancelara esta instruccion")
        nodo = NodeId()
        nodo.escribir(self.assemblerPositions)
        return self.localVariables[p.ID][1] #Ir a ID y a devolver su valor([1])
     
    
    @_('INT')   
    def factor(self, p):
        return p.INT #Ir a ID y a devolver su valor([1])
    
    @_('FLOAT')   
    def factor(self, p):
        return p.FLOAT #Ir a ID y a devolver su valor([1])
    
    @_('"(" expresion ")"')
    def factor(self, p):
        return p.expresion

def preprocesar(codigo): #Terminar esto, hay que arreglar el orden de includes.
    lineas = codigo.split('\n')
    resultado = codigo
    repetir = False
    codigoInclude = ''
    for i in range(len(lineas) - 1):
        if '#include <' in lineas[i]: #Comprobar si la sintaxis esta correcta
            linea = lineas[i]
            del lineas[i]
            if linea.count('<') != 1 or linea.count('>') != 1: #Tiene que haber un '<' y un '>' exactamente            
                print('Uso incorrecto de #include, se termina el programa')
                exit(0)
            else:
                try:
                    repetir = True
                    inicio = linea.find('<') + 1
                    fin = linea.find('>')
                    #Quitar la linea del include
                    filename = linea[inicio:fin]
                    file = open(filename, 'r')
                    #Obtener el codigo del include
                    codigoInclude = file.read()
                    #Obtener el codigo original, quitando la linea del include incluido
                    codigo = '\n'.join(lineas)
                except FileNotFoundError:
                    print('Fichero de include no encontrado, se detiene la traduccion')
                    exit(0)
    if repetir:
        return codigoInclude + preprocesar(codigo)
    else:
        return resultado

#Begin of Program
if __name__ == '__main__':
    #Analyzer instances
    lexerAnalyzer = Lexical()
    parserAnalyzer = Syntactic()
    text = ""
    option = input('Write the file name to compile:')
    with open(option, 'r') as code:
            text =  code.read()
            text = preprocesar(text)
    try:
        if text:
            parserAnalyzer.parse(lexerAnalyzer.tokenize(text))
            file.write('###Fin del programa###')
            file.close()
            with open('assembler.s', 'r') as code:
                text = code.read()
                i = 0
                fileFinal = open('salida.s', 'w')
                fileFinal.write('.code32\n')
                if len(variablesGlobales) > 0:
                    while i < len(variablesGlobales):
                        fileFinal.write('   ' + variablesGlobales[i])
                        i+=1
                    fileFinal.write('   .section    .rodata\n')
                i = 0
                if len(cadenas.items())  > 0:
                    keys = list(cadenas.keys())
                    while i < len(cadenas.items()):
                        fileFinal.write('.LC' + str(i) + ':\n')
                        fileFinal.write('   .string ' + str(keys[i]) + '\n' + '   .section    .rodata\n')
                        i += 1
                fileFinal.write(text)
                fileFinal.close()
                print('Fin de la traduccion')
    except KeyboardInterrupt:
        print('Fin del programa')

    