import math
from models import Tarefa_Finalizada

class FileWriter:
    '''
        Classe responsável por todas as operações de escrita em arquivo
    '''
    
    def __init__(self, algorithm_name: str):
        self.output_file = f"arquivo_saidas/algoritmo_{algorithm_name}.txt"
        self.initialize_file()
    

    def initialize_file(self):
        '''
            Inicializa o arquivo de saída, limpando conteúdo anterior
        '''

        try:
            with open(self.output_file, "w") as f:
                f.write("")

        except Exception as e:
            print(f"Erro ao inicializar arquivo: {e}")

    
    def write_thread_execution(self, thread_id: str):
        '''
            Escreve o ID da thread em execução no arquivo de saída
        '''

        try:
            with open(self.output_file, "a") as f:
                f.write(f"{thread_id};")

        except Exception as e:
            print(f"Erro ao escrever execução da thread: {e}")
    

    def write_final_statistics(self, tarefas_concluidas: list[Tarefa_Finalizada]):
        '''
            Escreve as estatísticas finais no arquivo de saída
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