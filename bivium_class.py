from sympy import *
from file_handler import *
from copy import deepcopy
from random import getrandbits
from to_cnf_v3 import system_to_cnf
from sat_solver import solve
from bivium import bivium_registers, bivium_equations, clean_system

def is_linear(equation):
    return all(len(monomial) == 1 for monomial in equation)

def is_contained(container, content):
    return all(elements in container for elements in content)

def count_var(equation):
    variable_set = set()

    for monomial in equation:
        for variable in monomial:
            variable_set.add(variable)

    return len(variable_set)

def index_to_var(index):
    if index < 93:
        return f"x{index + 1}"
    else:
        return f"y{index - 92}"

def equation_to_string(equation, i):
    return f"k{i + 1}: {int(equation[1])} = {' + '.join([' * '.join(x) for x in equation[0]])}"

def linear_equation_to_sat_string(equation, i):
    return ("" if equation[1] else "-") + ' '.join([var for var, in equation[0]])

def equation_to_sat_string(equation, i):
    return ("" if equation[1] else "~") + f"Xor({', '.join(['&'.join(x) for x in equation[0]])})"

def equation_info(equation, global_occ, local_occ):
    info = "    | "
    local_sum = global_sum = 0
    
    for monomial in equation:
        for var in monomial:
            info += f"{var}:{global_occ[var]}/{local_occ[var]} "
            global_sum += global_occ[var]
            local_sum += local_occ[var]

    return f"{info} (tot: {global_sum}/{local_sum})\n"

class BiviumSystem:

    def __init__(self, len_keystream = 180, all_one = False):
        if all_one:
            self.kx = [True] * 93
            self.ky = [True] * 84
        else:
            self.kx = [bool(getrandbits(1)) for x in range(93)]
            self.ky = [bool(getrandbits(1)) for x in range(84)]

        self.keystream = bivium_registers(len_keystream, self.kx, self.ky)
        self.z = bivium_equations(self.keystream, [])
        self.z_free_bits = deepcopy(self.z)
        
        self.fixed = []
        self.free = []
        self.aux_system = []

        self.abs_global_var_occurrences = self.variable_occurrences()
        self.abs_first_var_occurrences = self.variable_occurrences(end = 66)

    def copy(self):
        return deepcopy(self)

    def var_value(self, var):
        return self.kx[int(var[1:]) - 1] if var[0] == "x" else self.ky[int(var[1:]) - 1]

    ###SYSTEM MATRIX OPERATIONS
    def reduced_echelon_form(self, begin = 0, end = 66, step = 1, nofb = False):

        z = self.z if nofb else self.z_free_bits

        selected_rows = []
       #monomial_list = []
        """
        for eq, _ in z:
            for monomial in eq:
                if len(monomial) > 1 and monomial not in monomial_list:
                    monomial_list.append(monomial)
        """
        for i in range(begin, end, step):
            matrix_row = [1 if {index_to_var(k)} in z[i][0] else 0 for k in range(177)]
            matrix_row.append(int(z[i][1]))
            #matrix_row += [1 if monomial in z[i][0] else 0 for monomial in monomial_list]
            selected_rows.append(matrix_row)

        reduced_echelon = Matrix(selected_rows).rref()[0].tolist()
        
        for i in range(begin, end, step):
            new_row = [{index_to_var(k)} for k in range(177) if reduced_echelon[(i - begin) // step][k] % 2]
            #new_row += [monomial_list[k] for k in range(len(monomial_list)) if reduced_echeleon[177 + k] == 1]
            z[i] = (new_row, bool(reduced_echelon[(i - begin) // step][177] % 2))

    ###SIMPLIFY SYSTEM
    def simplify(self, new_fixed_bits):
        
        self.substitute_bits(new_fixed_bits)
        self.substitute_bits(new_fixed_bits, True)

        self.find_free_bits()

        self.fixed.extend(new_fixed_bits)

    def substitute_bits(self, fixed_bits, nofb = False):

        z = self.z if nofb else self.z_free_bits

        for var in fixed_bits:
            for i in range(len(z)):
                expr, const = z[i]
                for monomial in expr.copy():
                    if var in monomial:
                        if self.var_value(var): #se la variabile vale 1...
                            if len(monomial) == 1: #se il monomio ha solo quella variabile, allora diventa una costante da sommare al termine noto
                                expr.remove(monomial)
                                const = not const
                                z[i] = (expr, const)

                            else: #altrimenti elimina semplicemente la variabile dal monomio
                                monomial.remove(var)

                        else: #se la variabile vale 0, rimuovi il monomio
                            expr.remove(monomial)

        clean_system(z)
        
    def find_free_bits(self, verbose = False):
        free_bit = []
        check = True
        
        while check:
            new_fix_bit = []

            for i in range(len(self.z_free_bits)):
                if len(self.z_free_bits[i][0]) == 1 and len(self.z_free_bits[i][0][0]) == 1:
                    var, = self.z_free_bits[i][0][0]
                    
                    if var not in free_bit:

                        if self.z_free_bits[i][1] != self.var_value(var):
                            raise RuntimeError()

                        new_fix_bit.append(var)
                        free_bit.append(var)

            check = bool(new_fix_bit)

            if check:
                self.substitute_bits(new_fix_bit)

        if verbose:
            print('FREE BIT OTTENUTI:') if len(free_bit) > 0 else print('NESSUN FREE BIT OTTENUTO')

            for var, val in free_bit:
                print(f"{var} -> {int(val)}")

        clean_system(self.z_free_bits)

        self.free.extend(free_bit)

    #OCCURRENCES
    def variable_occurrences(self, begin = 0, end = None, nofb = False): #conta le occorrenze di ogni variabile nel range di equazioni del sistema
        var_occurrences = {(f"x{n}" if n < 94 else f"y{(n - 93)}"): 0 for n in range(1, 178)}

        z = self.z if nofb else self.z_free_bits

        for expr, _ in z[begin:end]:
            for monomial in expr:
                for variable in monomial:
                    var_occurrences[variable] += 1

        return var_occurrences

    def monomial_occurrences(self, begin = 0, end = None, nofb = False): #conta le occorrenze di ogni monomio nel sistema
        monomial_list = []
        occ_list = []

        z = self.z if nofb else self.z_free_bits

        for expr, _ in z[begin:end]:
            for monomial in expr:
                if monomial in monomial_list:
                    occ_list[monomial_list.index(monomial)] += 1
                else:
                    monomial_list.append(monomial)
                    occ_list.append(1)

        return sorted([(monomial_list[i], occ_list[i]) for i in range(len(occ_list))], key = lambda x: x[1], reverse = True)

    ###HISTORY
    def print_history(self, fixed_or_free = True):

        history_list = self.fixed if fixed_or_free else self.free

        print(f"{len(history_list)} variabili")
        sum = 0

        for var in history_list:
            sum += self.abs_global_var_occurrences[var]
            print(var, end = "    ")

        print(f"\nOccorrenze globali: {sum}\n")

    ###AUX
    def add_aux(self, aux_expr):

        count = 0

        for equation, _ in self.z_free_bits:
            if is_contained(equation, aux_expr):
                count += 1

        if count > 0:
            for equation, _ in self.z_free_bits:
                if is_contained(equation, aux_expr):
                    for monomial in aux_expr:
                        equation.remove(monomial)

                    equation.append({f"a{len(self.aux_system) + 1}"})

            print(f"Inserimento avvenuto con successo ({count} volte).", end = '\n\n')
            self.aux_system.append(aux_expr)

        else:
            print("L'equazione ausiliaria non compare mai nel sistema.", end = '\n\n')

    def create_simple_nonlinear_aux(self):

        for i in range(len(self.z_free_bits)):

            while not is_linear(self.z_free_bits[i][0]):
                
                for monomial in self.z_free_bits[i][0]:
                    
                    if len(monomial) > 1:
                        self.aux_system.append([monomial])

                        for equation, _ in self.z_free_bits:
                            if monomial in equation:
                                equation.append({f"a{len(self.aux_system)}"})
                                equation.remove(monomial)

                        break

    def create_nonlinear_aux(self):

        for i in range(len(self.z_free_bits)):
            while not is_linear(self.z_free_bits[i][0]):

                aux_expression = list(filter(lambda x: len(x) > 1, self.z_free_bits[i][0]))
                k = 0

                while count_var(aux_expression[k:]) > 2:
                    k += 1
                    if k >= len(aux_expression):
                        k -= 1
                        break

                aux_expression = aux_expression[k:]

                for equation, _ in self.z_free_bits:
                    if is_contained(equation, aux_expression):
                        for monomial in aux_expression:
                            equation.remove(monomial)

                        equation.append({f"a{len(self.aux_system) + 1}"})

                for aux_equation in self.aux_system:
                    if is_contained(aux_equation, aux_expression):
                        for monomial in aux_expression:
                            aux_equation.remove(monomial)

                            aux_equation.append({f"a{len(self.aux_system) + 1}"})

                self.aux_system.append(aux_expression)

    ###SOLVE
    def sat_solve(self, nofb = False):
        z = self.z if nofb else self.z_free_bits

        non_linear_equations = []
        linear_equations = []

        for i in range(len(z)):
            if z[i][0] != []:
                if is_linear(z[i][0]):
                    linear_equations.append(z[i])
                else:
                    non_linear_equations.append(equation_to_sat_string(z[i], i))

        #for i in range(len(self.aux_system)):
        #    non_linear_equations.append(f"~Xor(a{i + 1},{', '.join(['&'.join(x) for x in self.aux_system[i]])})")

        return solve(linear_equations, self.aux_system)

    ###PRINT
    def print(self, nofb = False):

        z = self.z if nofb else self.z_free_bits

        for i in range(len(z)):
            print(equation_to_string(z[i], i), end = "\n\n")

    def print_smaller(self, nofb = False):
        
        z = self.z if nofb else self.z_free_bits

        for i in range(66):
            if 0 < len(z[i][0]) < 4:
                print(f"{equation_to_string(z[i], i)} {equation_info(z[i][0], self.abs_global_var_occurrences, self.abs_first_var_occurrences)}")

    def print_info(self, nofb = False):

        z = self.z if nofb else self.z_free_bits

        for i in range(66):
            if i < 66 and z[i][0] != []:
                print(f"{equation_to_string(z[i], i)} {equation_info(z[i][0], self.abs_global_var_occurrences, self.abs_first_var_occurrences)}")
            else:
                print(equation_to_string(z[i], i), end = "\n\n")

    def print_sympy(self, nofb = False):

        z = self.z if nofb else self.z_free_bits

        for i in range(len(z)):
            if z[i][0] != []:
                print(equation_to_sat_string(z[i], i))

        for i in range(len(self.aux_system)):
            print(f"Xor(a{i + 1},{', '.join(['&'.join(x) for x in self.aux_system[i]])})", end = "\n\n")

    def print_sage(self, nofb = False):

        result = "["
        z = self.z if nofb else self.z_free_bits

        for i in range(len(z)):
            if z[i][0] != []:
                result += f"{' + '.join([' * '.join(x) for x in z[i][0]])}"
                if z[i][1]:
                    result += " + 1,"
                else:
                    result += ","    

        print(f"{result[:-1]}]")

    def print_cnf(self, nofb = False):

        z = self.z if nofb else self.z_free_bits

        non_linear_equations = []
        linear_equations = []

        for i in range(len(z)):
            if z[i][0] != []:
                if is_linear(z[i][0]):
                    linear_equations.append(z[i])
                else:
                    non_linear_equations.append(equation_to_sat_string(z[i], i))

        #for i in range(len(self.aux_system)):
        #    non_linear_equations.append(f"~Xor(a{i + 1},{', '.join(['&'.join(x) for x in self.aux_system[i]])})")

        return system_to_cnf(linear_equations, self.aux_system)

    def print_aux(self):
        for i in range(len(self.aux_system)):
            print(f"a{i + 1} = {' + '.join([' * '.join(x) for x in self.aux_system[i]])}", end = "\n\n")
