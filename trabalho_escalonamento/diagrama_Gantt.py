import matplotlib
matplotlib.use('Agg')  # Backend para salvar arquivos
import matplotlib.pyplot as plt
import numpy as np
import os


def abrir_arquivo(nome_arquivo):
    '''
        Lê o arquivo de saida com os dados das tarefas escalonadas
    '''
    
    informacao = []
    matriz = []
    arq = open(nome_arquivo, 'r')
    informacao = arq.readlines()
    arq.close()

    for c in informacao:
        matriz.append(c[:-1].split(";"))

    return matriz


def analisar_matriz(matriz, nome_arquivo):
    '''
        Analisa a matriz de dados que representa os dados presentes no arquivo de saída.
        Gera a imagem de um gráfico de barras em relação aos dados das tarefas escalonadas
    '''
    
    categorias = []
    inicio = []
    largura = []
    cor = "white"
    
    for i in range(1, len(matriz)-1):
        categorias.append(matriz[i][0])
        inicio.append(int(matriz[i][1]))
        largura.append(int(matriz[i][2]) - int(matriz[i][1]))
    
    plt.figure(figsize=(12, 8))
    y = np.arange(len(categorias))
    plt.barh(y, largura, left=inicio, color=cor, edgecolor='black', alpha=0.3)
    
    cores = ["red", "blue", "green", "purple", "yellow", "orange", "brown"]
    sequencia = []
    labels_adicionados = set()  # Para evitar labels duplicados
    
    # Criar um mapeamento de thread para índice de cor
    threads_unicas = []
    for thread in matriz[0]:
        if thread not in threads_unicas:
            threads_unicas.append(thread)
    
    for i in range(len(matriz[0])- 1):
        thread = matriz[0][i]
        
        if len(sequencia) == 0:
            inicio_seq = i
            sequencia.append(thread)
            index_categoria = categorias.index(thread)

        elif sequencia[-1] == thread:
            sequencia.append(thread)

        else:
            # Usar o índice correto da thread para a cor
            indice_cor = threads_unicas.index(sequencia[0])
            
            # Adicionar label apenas uma vez por thread
            label = sequencia[0] if sequencia[0] not in labels_adicionados else ""
            if sequencia[0] not in labels_adicionados:
                labels_adicionados.add(sequencia[0])
            
            plt.barh(y[index_categoria], len(sequencia), left=inicio_seq, 
                    color=cores[indice_cor % len(cores)], edgecolor='black', label=label)
            
            inicio_seq = i
            index_categoria = categorias.index(thread)
            sequencia = []
            sequencia.append(thread)
    
    # Processar a última sequência
    if sequencia:
        indice_cor = threads_unicas.index(sequencia[0])
        label = sequencia[0] if sequencia[0] not in labels_adicionados else ""
        plt.barh(y[index_categoria], len(sequencia), left=inicio_seq, 
                color=cores[indice_cor % len(cores)], edgecolor='black', label=label)
    
    plt.yticks(y, categorias)
    
    # Configurar eixo X com mais detalhamento
    tempo_maximo = max([int(matriz[i][2]) for i in range(1, len(matriz)-1)])
    
    # Mostrar todos os números inteiros
    plt.xticks(range(0, tempo_maximo + 1, 1))
    
    # Adicionar grid para melhor visualização
    plt.grid(True, axis='x', alpha=0.3, linestyle='--')
    
    plt.xlabel('Tempo (Clock)')
    plt.title('Execução de Tarefas - Diagrama de Gantt')
    
    # Ordenar a legenda para ficar na ordem correta (t0, t1, t2, ...)
    handles, labels = plt.gca().get_legend_handles_labels()
    
    # Ordenar pelos labels
    sorted_pairs = sorted(zip(labels, handles))
    sorted_labels, sorted_handles = zip(*sorted_pairs)
    plt.legend(sorted_handles, sorted_labels)
    
    plt.tight_layout()
    
    # Criar pasta se não existir
    pasta_saida = "grafico_saidas"
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
        print(f"Pasta '{pasta_saida}' criada.")
    
    # Extrair nome do arquivo sem extensão e caminho
    nome_base = os.path.splitext(os.path.basename(nome_arquivo))[0]
    caminho_saida = os.path.join(pasta_saida, f"{nome_base}.png")
    
    # Salva o gráfico
    plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
    
def grafico_tarefas_escalonadas(nome_arquivo):
    analisar_matriz(abrir_arquivo(nome_arquivo), nome_arquivo)
    