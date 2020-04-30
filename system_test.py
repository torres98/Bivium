from file_handler import open_file, close_file
from env import new_system, create_nonlinear_aux, system_to_cnf, substitute_bits, find_free_bits, fix_top

###TOP FIXED BIT
for i in range(8):

    aux_system = []
    aux_index = 1

    z, z_with_free_bit, z_no_free_bit, keystream, kx, ky, fixed_list, free_list = new_system()
    #variables = ["x65", "x63", "x66", "y67", "y66", "y68", "x64", "y76", "y69", "x68", "x62", "y65", "y74", "y72", "y77", "y71", "x67", "y70", "x69", "x91", "y73", "y64", "x61", "x72", "x75", "x88", "y75", "x76", "y63", "x71", "x78", "x80", "x82", "x84", "y78", "x60", "y56", "y58"]
    #fixed_bits = [(var, kx[int(var[1:]) - 1] if var[0] == "x" else ky[int(var[1:]) - 1]) for var in variables]
    fixed_bits = fix_top(z_with_free_bit, keystream, kx, ky, 38)

    substitute_bits(z_with_free_bit, keystream, fixed_bits)
    find_free_bits(z_with_free_bit, keystream)

    create_nonlinear_aux(z_with_free_bit, aux_system, aux_index)

    variable_map = system_to_cnf(z_with_free_bit, aux_system, keystream, f"test_cnf/top{i + 1}")

    file = open_file(f"test_output/var_sample", priviledges = "a")

    x_string = ""
    y_string = ""

    for var, _ in sorted(fixed_bits):
        if var[0] == "x":
            x_string += f"{var:4}"
        elif var[0] == "y":
            y_string += f"{var:4}"

    print(f"VARIABILI FISSATE:\n{x_string}\n\n{y_string}\n\n\n")

    file = open_file(f"test_output/top{i + 1}")

    x_string = ""
    y_string = ""
    a_string = ""

    for var in sorted(variable_map.keys()):
        if var[0] == "x":
            x_string += f"{var}: {variable_map[var]:4}"
        elif var[0] == "y":
            y_string += f"{var}: {variable_map[var]:4}"
        elif var[0] == "a":
            a_string += f"{var}: {variable_map[var]:4}"

    print(f"VARIABLE MAPPING:\n{x_string}\n\n{y_string}\n\n{a_string}\n")

    close_file(file)