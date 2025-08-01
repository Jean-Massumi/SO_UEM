import math
import os
from models import Tarefa_Finalizada


class FileWriter:
    '''
        Classe responsável por todas as operações de escrita em arquivo do escalonador.
        
        Gerencia a criação e escrita de arquivos de saída contendo:
        - Sequência de execução das threads (timeline de escalonamento)
        - Estatísticas individuais de cada thread concluída
        - Médias de turnaround time e waiting time
    '''
    

    def __init__(self, algorithm_name: str):
        '''
            Inicializa o FileWriter para um algoritmo específico.
        '''

        # Criar pasta se não existir
        os.makedirs("arquivo_saidas", exist_ok=True)

        self.output_file = f"arquivo_saidas/algoritmo_{algorithm_name}.txt"
        self.initialize_file()
    

    def initialize_file(self):
        '''
            Inicializa o arquivo de saída, limpando conteúdo anterior

            Cria um arquivo vazio no diretório arquivo_saidas. Se o arquivo
            já existir, todo conteúdo anterior é removido para garantir
            dados limpos para a nova execução do escalonador.
        '''

        try:
            with open(self.output_file, "w") as f:
                f.write("")

        except Exception as e:
            print(f"Erro ao inicializar arquivo: {e}")

    
    def write_thread_execution(self, thread_id: str):
        '''
            Registra a execução de uma thread no timeline de escalonamento.
    
            Adiciona o ID da thread ao arquivo, seguido de ponto e vírgula.
            Este método é chamado a cada ciclo de clock em que uma thread
            está sendo executada, criando um histórico completo do escalonamento.
        '''

        try:
            with open(self.output_file, "a") as f:
                f.write(f"{thread_id};")

        except Exception as e:
            print(f"Erro ao escrever execução da thread: {e}")
    

    def write_final_statistics(self, tarefas_concluidas: list[Tarefa_Finalizada]):
        '''
            Escreve as estatísticas finais de todas as threads concluídas.
            
            Gera um relatório completo contendo:
            1. Dados individuais de cada thread (ordenados por ID)
            2. Médias de turnaround time e waiting time
            
            Formato de saída por linha:
            - Thread: ID;clock_ingresso;clock_finalização;turnaround_time;waiting_time
            - Médias: média_turnaround;média_waiting (arredondadas para cima)  
        '''
        
        try:
            with open(self.output_file, "a") as f:
                f.write("\n")  # Nova linha após a sequência de execução
                
                # Ordenar tarefas por ID
                tarefas_concluidas.sort(key=lambda tarefa: tarefa.ID)
                
                # Variáveis para acumular as somas
                total_turnaround = 0
                total_waiting = 0

                # Escrever informações de cada tarefa
                for tarefa in tarefas_concluidas:
                    f.write(f"{tarefa.ID};{tarefa.clock_de_ingresso};{tarefa.clock_de_finalizacao};"
                           f"{tarefa.turn_around_time};{tarefa.waiting_time}\n")

                    # Acumular para o cálculo das médias
                    total_turnaround += tarefa.turn_around_time
                    total_waiting += tarefa.waiting_time

                # Calcular e escrever médias
                if tarefas_concluidas:
                    num_tarefas = len(tarefas_concluidas)
                    media_turnaround = total_turnaround / num_tarefas
                    media_waiting = total_waiting / num_tarefas
                        
                    # Arredondar para cima com 1 casa decimal
                    media_turnaround_rounded = math.ceil(media_turnaround * 10) / 10
                    media_waiting_rounded = math.ceil(media_waiting * 10) / 10
                    
                    f.write(f"{media_turnaround_rounded:.1f};{media_waiting_rounded:.1f}\n")

                else:
                    f.write("0.0;0.0\n")
                    
        except Exception as e:
            print(f"Erro ao escrever estatísticas finais: {e}")