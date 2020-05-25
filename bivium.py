from bitarray import bitarray

def bivium_equations(keystream, fixed_bit_reg):
    
    kx = [([{f"x{n}"}], False) for n in range(1, 94)]
    ky = [([{f"y{n}"}], False) for n in range(1, 85)]

    for var, val in fixed_bit_reg:
        if var[0] == "x":
            kx[int(var[1:]) - 1] = ([], bool(val))
        else:
            ky[int(var[1:]) - 1] = ([], bool(val))

    z = []

    for i in range(len(keystream)):
        t1 = add(kx[65], kx[92])
        t2 = add(ky[68], ky[83])
        z_i = add(t1, t2)
        clean_equation(z_i[0])
        z.append((z_i[0], z_i[1] ^ bool(keystream[i])))

        t1 = add(t1, ky[77])
        fact1 = mul(kx[90], kx[91])
        t1 = add(t1, fact1)

        t2 = add(t2, kx[68])
        fact2 = mul(ky[81], ky[82])
        t2 = add(t2, fact2)

        #rotation
        kx[1:93] = kx[0:92]
        ky[1:84] = ky[0:83]
        kx[0] = t2
        ky[0] = t1
    
    return z

###OPERAZIONI
def add(a, b): #calcola la somma tra due espressioni
    return (a[0] + b[0], a[1] ^ b[1])

def mul(a, b): #calcola il prodotto tra due espressioni
    fact = [x.union(y) for x in a[0] for y in b[0]]
        
    if a[1]:
        fact += b[0]
    if b[1]:
        fact += a[0]

    return (fact, a[1] and b[1])

def clean_equation(dirty_equation):
    monomial_list = []

    for monomial in dirty_equation:
        if monomial not in monomial_list:
            monomial_list.append(monomial)

    for monomial in monomial_list:
        monomial_occurrences = dirty_equation.count(monomial)
        for _ in range(monomial_occurrences - (monomial_occurrences % 2)):
            dirty_equation.remove(monomial)

def clean_system(z):
    for equation, _ in z:
        clean_equation(equation)

#Funzione che ruota i bit dei 2 registri, mettendone in testa i 2 bit
#(t1 e t2) appena generati, scartando quindi l'ultimo bit di ciascuno
def rotation(s, t1, t2):
    s[1:177] = s[0:176]
    s[0] = t2
    s[93] = t1

#Funzione che inizializza i 2 registri tramite key e iv, effettuando 4*177
#iterazioni dell'algoritmo, senza generare però bit di keystream
def init_internal_state(key, iv):
    s = bitarray()

    #s[1::93] = key + [0, 0, ..., 0] (tredici zeri)
    s.extend(key)
    s.extend([0]*13)

    #s[94::177] = iv + [0, 0, 0, 0] (anche se mi sembra strano non aggiungere degli '1'...)
    s.extend(iv)
    s.extend([0]*4)

    for i in range(708):
        t1 = s[65] ^ (s[90] & s[91]) ^ s[92] ^ s[170]
        t2 = s[161] ^ (s[174] & s[175]) ^ s[176] ^ s[68]
        rotation(s, t1, t2)
    
    return s

#Algoritmo identico al ciclo presente in 'init_internal_state', che in più genera
#i bit della keystream necessari
def keystream_gen(s, N):
    keystream = bitarray()

    for i in range(N):
        t1 = s[65] ^ s[92]
        t2 = s[161] ^ s[176]
        keystream.append(t1 ^ t2)
        t1 = t1 ^ (s[90] and s[91]) ^ s[170]
        t2 = t2 ^ (s[174] and s[175]) ^ s[68]
        rotation(s, t1, t2)

    return keystream

#Funzione di encryption che prende come input il messaggio e i 2 registri
#iniziali per trivium, senza che venga quindi fatta la inizializzazione con
#key e iv
def bivium_registers(msglen, kx, ky):
    s = bitarray()
    s.extend(kx)
    s.extend(ky)
    return keystream_gen(s, msglen).tolist()