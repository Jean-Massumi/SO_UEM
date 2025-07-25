import string

totalSimbolos = 26

def load_task_frequency(caminho):
    ranking = []

    with open(caminho, 'r') as f:
        for linha in f:
            ranking.append(linha.strip())

    return ranking


def loads_figure_or_template(caminho, flagLinha):
    resul = []

    with open(caminho, 'r') as f:
        for linha in f:
            resul.append(linha.strip())

    if flagLinha:
        return resul
    
    else:
        return ["".join(resul)]


def calculaFrequencia(msg):
    contagem = {letra: 0 for letra in string.ascii_uppercase}

    for char in msg:
        contagem[char] += 1

    ranking = sorted(contagem.items(), key=lambda item:item[1], reverse=True)

    return ranking


def calcDesloc(charFreqCifra, charFreqIdioma):
    posCifra = ord(charFreqCifra) - ord('A')
    posIdioma = ord(charFreqIdioma) - ord('A')

    deslocD = (posIdioma - posCifra) % totalSimbolos
    deslocE = (posCifra - posIdioma) % totalSimbolos

    return deslocD, deslocE


def shift(char, deslocamento):
    posPartida = ord(char) - ord('A')
    posFim = (posPartida + deslocamento) % totalSimbolos

    return chr(posFim + ord('A'))


ranking_freq_idioma = load_task_frequency("ranking_freq_PTBR.txt")
cifras = loads_figure_or_template("cifras_por_linha.txt", 1)
gabarito = loads_figure_or_template("gabarito.txt", 1)


for i in range(len(cifras)):
    rankingFreqCifra = calculaFrequencia(cifras[i])
    charFreqCifra = rankingFreqCifra[0][0] # caractere maior freq

    for j in range(len(ranking_freq_idioma)):
        charFreqIdioma = ranking_freq_idioma[j]
        desloqD, deslocE = calcDesloc(charFreqCifra, charFreqIdioma)

        primeiroCharCifra = cifras[i][0]
        primeiroCharGabarito = gabarito[i][0]
        
        if shift(primeiroCharCifra, desloqD) == primeiroCharGabarito:
            print(f"Chave descoberta em {j+1}  tentativas!")
            print(f"Deslocamento de {desloqD} para a direita. \n")
            break

        elif shift(primeiroCharCifra, deslocE) == primeiroCharGabarito:
            print(f"Chave descoberta em {j+1}  tentativas!")
            print(f"Deslocamento de {deslocE} para a esquerda. \n")
            break


