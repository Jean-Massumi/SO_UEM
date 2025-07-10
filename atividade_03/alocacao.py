import sys

def lerMem(caminhoArq):
    with open(caminhoArq, 'r') as f:
        tamMemoria = int(f.readline())
        memoriaRepStr = f.readline() 
        memoria = [int(char) for char in memoriaRepStr]

    return tamMemoria, memoria


def encontrarBlocosLivres(memoria):
    blocosLivres = []
    i = 0

    while i < len(memoria):
        if memoria[i] == 0:
            inicio = i

            while i < len(memoria) and memoria[i] == 0:
                i += 1

            blocosLivres.append((inicio, i - inicio)) 
            # Tupla: 1º valor: indice do bloco livre, 2º valor: tamanho do bloco livre

        else:
            i += 1

    return blocosLivres


def firstFit(blocosLivres, tamAlocacao):
    for inicio, tam in blocosLivres:
        if tam >= tamAlocacao:
            return inicio
        
    return None


def bestFit(blocosLivres, tamAlocacao):
    melhor = None   # Armazena a tupla de bloco livre

    for inicio, tam in blocosLivres:
        if tam >= tamAlocacao:
            if melhor is None or tam < melhor[1]:
                melhor = (inicio, tam)

    return melhor[0] if melhor != None else None
        

def worstFit(blocosLivres, tamAlocacao):
    pior = None   # Armazena a tupla de bloco livre

    for inicio, tam in blocosLivres:
        if tam >= tamAlocacao:
            if pior is None or tam > pior[1]:
                pior = (inicio, tam)

    return pior[0] if pior != None else None


def alocar(memoria, indiceInicioAloc, tamAlocacao, pid):
    for i in range(indiceInicioAloc, indiceInicioAloc + tamAlocacao):
        memoria[i] = pid


if __name__ == "__main__":
    estrategia = sys.argv[1]
    caminhoArq = sys.argv[2]

    tamanhoMem, memoria = lerMem(caminhoArq)

    while True:
        tamAlocacao = int(input("Informe o tamanho da alocação (ou -1 para sair): "))

        if tamAlocacao == -1:
            break

        blocosLivres = encontrarBlocosLivres(memoria)


        if not blocosLivres:
            print("Não há mais memória livre para alocação!")
            break


        if estrategia == "first":
            indiceInicioAloc = firstFit(blocosLivres, tamAlocacao)
        
        elif estrategia == "best":
            indiceInicioAloc = bestFit(blocosLivres, tamAlocacao)

        elif estrategia == "worst":
            indiceInicioAloc = worstFit(blocosLivres, tamAlocacao)

        else:
            print("Argumento inválido!")
            break


        if indiceInicioAloc == None:
            print("Não há espaço de alocação. Tente um valor menor.")

        else:
            pid = max(memoria) + 1
            alocar(memoria, indiceInicioAloc, tamAlocacao, pid)

            print("Estado da memória depois da alocação:")
            print(memoria)
        print("\n")

    print("Alocações encerradas. \n")
    print("Estado final da memória: ")
    print(memoria)
