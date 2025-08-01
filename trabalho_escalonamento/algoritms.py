from abc import ABC
from models import Tarefa_Finalizada
from diagrama_Gantt import grafico_tarefas_escalonadas

class BaseAlgorithm(ABC):
    '''
        Classe base para todos os algoritmos de escalonamento

        Fornece funcionalidades comuns para execução de tarefas, controle de conclusão
        e finalização de algoritmos entre diferentes estratégias de escalonam
    '''
    
    def __init__(self):
        self.tarefa_em_execucao = False
        self.old_clock = None
        self.tarefa_no_momento = None
        self.tarefas_concluidas = []


    def _start_new_task(self, scheduler):
        '''
            Inicia uma nova tarefa no processador.
        '''

        self.tarefa_no_momento = scheduler.ready_threads.pop()
        print(f"Thread: {self.tarefa_no_momento.id} escalonada no tempo de clock {scheduler.current_clock}\n")
        self.tarefa_em_execucao = True


    def _task_switching(self, scheduler):
        '''
            Realiza a troca de contexto entre tarefas em algoritmos preemptivos.
            
            Move a tarefa atual de volta para a fila de prontos e escalona a próxima tarefa.
            A estratégia de inserção depende do tipo de algoritmo (duração vs prioridade).    
        '''
        
        print(f"Thread: {self.tarefa_no_momento.id} retornou a fila de tarefas prontas no clock {scheduler.current_clock}\n")
        nova_tarefa = scheduler.ready_threads.pop()

        if scheduler.algoritmo_de_insercao == "duração":
            scheduler.insert_by_shortest_time(self.tarefa_no_momento)
        
        elif scheduler.algoritmo_de_insercao == "prioridade":
            scheduler.insert_by_priority(self.tarefa_no_momento)

        self.tarefa_no_momento = nova_tarefa
        print(f"Thread: {self.tarefa_no_momento.id} escalonada no tempo de clock {scheduler.current_clock}\n")


    def _complete_task(self, scheduler):
        '''
            Completa uma tarefa.
        '''
        
        id_tarefa = self.tarefa_no_momento.id
        tempo_ingresso = self.tarefa_no_momento.tempo_ingresso
        tempo_finalizacao = int(scheduler.current_clock)
        turnaround_time = tempo_finalizacao - tempo_ingresso
        waiting_time = turnaround_time - self.tarefa_no_momento.duracao_prevista.tempo_total

        self.tarefas_concluidas.append(Tarefa_Finalizada(
            id_tarefa, tempo_ingresso, tempo_finalizacao,
            turnaround_time, waiting_time
        ))
        
        print(f"Thread: {id_tarefa} finalizada no clock {tempo_finalizacao}\n")
        self.tarefa_em_execucao = False


    def _finalize_execution(self, scheduler):
        '''
            Finaliza a execução do algoritmo
        '''
        
        print("Tarefas concluídas!")
        scheduler.file_writer.write_final_statistics(self.tarefas_concluidas)
        scheduler.communication_clock()
        scheduler.communication_emitter()
        scheduler.close_server()
        grafico_tarefas_escalonadas(scheduler.file_writer.output_file)
        print("ESCALONADOR ENCERRADO POR COMPLETO!")


class NonPreemptiveAlgorithm(BaseAlgorithm):
    '''
        Classe base para algoritmos não-preemptivos (FCFS, SJF e PRIOc)
        A diferença entre eles é apenas a política de inserção na fila
    '''
    
    def execute(self, scheduler):
        '''
            Executa algoritmos não-preemptivos (FCFS, SJF ou PRIOc)
            A fila já vem ordenada conforme a política escolhida
        '''

        # Loop principal do escalonador
        while not (scheduler.emitter_completed and len(scheduler.ready_threads) == 0 and not self.tarefa_em_execucao):
            
            scheduler.check_messages()

            if self.old_clock != scheduler.current_clock and scheduler.current_clock is not None:
                print(f"Clock: {scheduler.current_clock}, Threads prontas: {len(scheduler.ready_threads)}")

                # Iniciar nova tarefa se não há nenhuma em execução
                if not self.tarefa_em_execucao and len(scheduler.ready_threads) > 0:
                    self._start_new_task(scheduler)

                # Processar tarefa em execução
                if self.tarefa_em_execucao:
                    
                    # Verificar se a tarefa foi concluída
                    if self.tarefa_no_momento.duracao_prevista.tempo_restante == 0:
                        self._complete_task(scheduler)
                        continue
                    
                    # Escrever no arquivo de saída
                    scheduler.file_writer.write_thread_execution(self.tarefa_no_momento.id)
                    
                    # Decrementar a duração da tarefa
                    self.tarefa_no_momento.duracao_prevista.tempo_restante -= 1
                    
                self.old_clock = scheduler.current_clock

        self._finalize_execution(scheduler)


class RR_Algorithm(BaseAlgorithm):
    '''
        Implementa o algoritmo Round Robin (RR).
        
        Algoritmo preemptivo que aloca um quantum de tempo fixo para cada tarefa.
        Quando o quantum expira, a tarefa volta para o final da fila de prontos
        e a próxima tarefa é escalonada.
    '''
    
    def __init__(self, quantum: int):
        super().__init__()
        self.quantum = quantum
    

    def execute(self, scheduler):
        '''
            Executa o algoritmo Round Robin no escalonador fornecido
        '''
        quantum_da_tarefa = 0
        
        while not (scheduler.emitter_completed and len(scheduler.ready_threads) == 0 and not self.tarefa_em_execucao):
            
            scheduler.check_messages()

            if self.old_clock != scheduler.current_clock and scheduler.current_clock is not None:
                print(f"Clock: {scheduler.current_clock}, Threads prontas: {len(scheduler.ready_threads)}")

                # Iniciar nova tarefa se não há nenhuma em execução
                if not self.tarefa_em_execucao and len(scheduler.ready_threads) > 0:
                    self._start_new_task(scheduler)  
                    quantum_da_tarefa = self.quantum

                # Processar tarefa em execução
                if self.tarefa_em_execucao:
                    
                    # Verificar se a tarefa foi concluída
                    if self.tarefa_no_momento.duracao_prevista.tempo_restante == 0:
                        self._complete_task(scheduler)
                        continue

                    # Verificar se quantum acabou e há outras tarefas
                    elif quantum_da_tarefa == 0 and len(scheduler.ready_threads) > 0:
                        print(f"Thread: {self.tarefa_no_momento.id} retornou a fila de espera no clock {scheduler.current_clock}\n")
                        scheduler.ready_threads.appendleft(self.tarefa_no_momento)
                        self.tarefa_em_execucao = False
                        continue
                    
                    # Escrever no arquivo de saída
                    scheduler.file_writer.write_thread_execution(self.tarefa_no_momento.id)
                        
                    self.tarefa_no_momento.duracao_prevista.tempo_restante -= 1
                    quantum_da_tarefa -= 1
                        
                self.old_clock = scheduler.current_clock

        self._finalize_execution(scheduler)


class SRTF_Algorithm(BaseAlgorithm):
    """
        Algoritmo de escalonamento Shortest Remaining Time First (SRTF).
    
        Algoritmo preemptivo que sempre executa a tarefa com o menor tempo
        restante de execução. Se uma nova tarefa chegar com tempo restante
        menor que a tarefa atual, ocorre preempção imediatamente.
    """
    
    def execute(self, scheduler):
        '''
            Executa o algoritmo Shortest Remaining Time First (SRTF).
        '''

        # Loop principal do escalonador
        while not (scheduler.emitter_completed and len(scheduler.ready_threads) == 0 and not self.tarefa_em_execucao):
            
            scheduler.check_messages()

            if self.old_clock != scheduler.current_clock and scheduler.current_clock is not None:
                print(f"Clock: {scheduler.current_clock}, Threads prontas: {len(scheduler.ready_threads)}")

                # Iniciar nova tarefa se não há nenhuma em execução
                if not self.tarefa_em_execucao and len(scheduler.ready_threads) > 0:
                    self._start_new_task(scheduler)
 
                # Processar tarefa em execução
                if self.tarefa_em_execucao:
                    
                    # Verificar se a tarefa foi concluída
                    if self.tarefa_no_momento.duracao_prevista.tempo_restante == 0:
                        self._complete_task(scheduler)
                        continue
                    
                    elif len(scheduler.ready_threads) > 0 and scheduler.ready_threads[-1].duracao_prevista.tempo_restante < self.tarefa_no_momento.duracao_prevista.tempo_restante:
                        self._task_switching(scheduler)
                    
                    # Escrever no arquivo de saída
                    scheduler.file_writer.write_thread_execution(self.tarefa_no_momento.id)
                    
                    # Decrementar a duração da tarefa
                    self.tarefa_no_momento.duracao_prevista.tempo_restante -= 1
                    
                self.old_clock = scheduler.current_clock

        self._finalize_execution(scheduler)


class PRIOp_Algorithm(BaseAlgorithm):
    """
        Algoritmo de Prioridade Preemptiva (PRIOp).
    
        Algoritmo preemptivo que sempre executa a tarefa com menor prioridade
        disponível na fila de prontos. Quando uma nova tarefa chega com prioridade
        menor que a tarefa atualmente em execução, ocorre preempção imediata.
    """

    def execute(self, scheduler):
        '''
            Executa o algoritmo Prioridade Preemptiva (PRIOp)
        '''

        # Loop principal do escalonador
        while not (scheduler.emitter_completed and len(scheduler.ready_threads) == 0 and not self.tarefa_em_execucao):
            
            scheduler.check_messages()

            if self.old_clock != scheduler.current_clock and scheduler.current_clock is not None:
                print(f"Clock: {scheduler.current_clock}, Threads prontas: {len(scheduler.ready_threads)}")

                # Iniciar nova tarefa se não há nenhuma em execução
                if not self.tarefa_em_execucao and len(scheduler.ready_threads) > 0:
                    self._start_new_task(scheduler)

                # Processar tarefa em execução
                if self.tarefa_em_execucao:
                    
                    # Verificar se a tarefa foi concluída
                    if self.tarefa_no_momento.duracao_prevista.tempo_restante == 0:
                        self._complete_task(scheduler)
                        continue
                    
                    elif len(scheduler.ready_threads) > 0 and scheduler.ready_threads[-1].prioridade.prio_d < self.tarefa_no_momento.prioridade.prio_d:
                        self._task_switching(scheduler)

                    # Escrever no arquivo de saída
                    scheduler.file_writer.write_thread_execution(self.tarefa_no_momento.id)
                    
                    # Decrementar a duração da tarefa
                    self.tarefa_no_momento.duracao_prevista.tempo_restante -= 1
                    
                self.old_clock = scheduler.current_clock

        self._finalize_execution(scheduler)



class PRIOd_Algorithm(BaseAlgorithm):
    """
        Algoritmo de Prioridade Dinâmica (PRIOd).
        
        Faz basicamente igual ao algoritmo PRIOp, só que implementa escalonamento
        baseado em prioridades que se ajustam dinamicamente durante a execução.
    """
    
    def execute(self, scheduler):
        '''
            Executa o algoritmo Prioridade Dinâmica (PRIOd).
        '''

        # Loop principal do escalonador
        while not (scheduler.emitter_completed and len(scheduler.ready_threads) == 0 and not self.tarefa_em_execucao):
            
            scheduler.check_messages()

            if self.old_clock != scheduler.current_clock and scheduler.current_clock is not None:
                print(f"Clock: {scheduler.current_clock}, Threads prontas: {len(scheduler.ready_threads)}")

                # Iniciar nova tarefa se não há nenhuma em execução
                if not self.tarefa_em_execucao and len(scheduler.ready_threads) > 0:
                    self._start_new_task(scheduler)
                    self.tarefa_no_momento.prioridade.prio_d = self.tarefa_no_momento.prioridade.prio_e
                
                elif len(scheduler.ready_threads) > 0 and scheduler.ready_threads[-1].prioridade.prio_d < self.tarefa_no_momento.prioridade.prio_d and \
                    self.tarefa_no_momento.duracao_prevista.tempo_restante != 0 and scheduler.new_emiiter:
                    
                    self._task_switching(scheduler)
                    self.tarefa_no_momento.prioridade.prio_d = self.tarefa_no_momento.prioridade.prio_e   
           
           
                # Processar tarefa em execução
                if self.tarefa_em_execucao:
                    
                    # Verificar se a tarefa foi concluída
                    if self.tarefa_no_momento.duracao_prevista.tempo_restante == 0:
                        self._complete_task(scheduler)
                        scheduler.new_emiiter = True
                        continue  

                    
                    # Escrever no arquivo de saída
                    scheduler.file_writer.write_thread_execution(self.tarefa_no_momento.id)
                    
                    # Decrementar a duração da tarefa
                    self.tarefa_no_momento.duracao_prevista.tempo_restante -= 1
                    

                if scheduler.new_emiiter:
                    scheduler.increment_priority()
                    scheduler.new_emiiter = False

                self.old_clock = scheduler.current_clock

        self._finalize_execution(scheduler)
