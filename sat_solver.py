from pycryptosat import Solver

def solve(main_system, aux_system):
    sat = Solver()

    var_dict = {}
    var_index = 1

    for equation, const in main_system:
        xor_clause = []

        for var, in equation:
            if var not in var_dict:
                var_dict[var] = var_index
                xor_clause.append(var_index)
                var_index += 1
            else:
                xor_clause.append(var_dict[var])

        sat.add_xor_clause(xor_clause, const)

    for i in range(len(aux_system)):

        l = list(aux_system[i][0])
        
        if f"a{i + 1}" not in var_dict:
                var_dict[f"a{i + 1}"] = var_index
                var_index += 1
            
        for var in l:
            if var not in var_dict:
                var_dict[var] = var_index
                var_index += 1

        if len(l) == 2:
            sat.add_clauses([[-var_dict[f'a{i + 1}'], var_dict[l[0]]], [-var_dict[f'a{i + 1}'], var_dict[l[1]]], [var_dict[f'a{i + 1}'], -var_dict[l[0]], -var_dict[l[1]]]])
        elif len(l) == 3:
            sat.add_clauses([[-var_dict[f'a{i + 1}'], var_dict[l[0]]], [-var_dict[f'a{i + 1}'], var_dict[l[1]]], [-var_dict[f'a{i + 1}'], var_dict[l[2]]], [var_dict[f'a{i + 1}'], -var_dict[l[0]], -var_dict[l[1]], -var_dict[l[2]]]])
        else:
            raise ValueError(f"Variabile ausiliaria a{i + 1} troppo grande!")

    print(sat.solve())
    return var_dict