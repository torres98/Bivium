from bivium_class import BiviumSystem, is_contained
from file_handler import open_file, close_file

system = BiviumSystem()

f = open_file("matrix")
var_list = [f"x{i:02}" for i in range(1, 94)] + [f"y{i:02}" for i in range(1, 85)]

l = []
for i in range(2, 66, 3):
    l.append([1 if {var} in system.z[i][0] else 0 for var in var_list])
    
print(l)
close_file(f)