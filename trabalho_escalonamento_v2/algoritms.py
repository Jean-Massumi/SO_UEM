from abc import ABC, abstractmethod
from models import Tarefa_Finalizada


class BaseAlgorithm(ABC):
    '''
        Classe base para todos os algoritmos de escalonamento
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
        Implementa o algoritmo Round Robin (RR)
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
    
    def execute(self, scheduler):
        '''
            Executa algoritmos o algoritmo 'SRTF'
            Este algoritmo sempre executa primeiro a tarefa com menor tempo restante na fila de espera, 
            Se uma tarefa da fila ter menor tempo restante que a tarefa em execução,
            ela toma a execução da tarefa executada, a qual retorna para a fila
        '''

        # Loop principal do escalonador
        while not (scheduler.emitter_completed and len(scheduler.ready_threads) == 0 and not self.tarefa_em_execucao):
            
            scheduler.check_messages()

            if self.old_clock != scheduler.current_clock and scheduler.current_clock is not None:
                print(f"Clock: {scheduler.current_clock}, Threads prontas: {len(scheduler.ready_threads)}")
                tamanho_fila = len(scheduler.ready_threads)
                
                # Iniciar nova tarefa se não há nenhuma em execução
                if not self.tarefa_em_execucao and tamanho_fila > 0:
                    self._start_new_task(scheduler)

                elif tamanho_fila > 0 and scheduler.ready_threads[tamanho_fila - 1].duracao_prevista.tempo_restante < self.tarefa_no_momento.duracao_prevista.tempo_restante:
                    
                    print(f"Thread: {self.tarefa_no_momento.id} retornou a fila de tarefas prontas no clock {scheduler.current_clock}\n")
                    nova_tarefa = scheduler.ready_threads.pop()
                    scheduler.ready_threads.append(self.tarefa_no_momento)
                    self.tarefa_no_momento = nova_tarefa
                    print(f"Thread: {self.tarefa_no_momento.id} escalonada no tempo de clock {scheduler.current_clock}\n")
                    
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


class PRIOp_Algorithm(BaseAlgorithm):
    
    def execute(self, scheduler):
        '''
            Executa algoritmos o algoritmo 'PRIOp'
            Este algoritmo sempre executa primeiro a tarefa com maior prioridade na fila de espera, 
            Se uma tarefa da fila ter maior prioridade que a tarefa em execução,
            ela toma a execução da tarefa executada, a qual retorna para a fila
        '''

        # Loop principal do escalonador
        while not (scheduler.emitter_completed and len(scheduler.ready_threads) == 0 and not self.tarefa_em_execucao):
            
            scheduler.check_messages()

            if self.old_clock != scheduler.current_clock and scheduler.current_clock is not None:
                print(f"Clock: {scheduler.current_clock}, Threads prontas: {len(scheduler.ready_threads)}")
                tamanho_fila = len(scheduler.ready_threads)
                
                # Iniciar nova tarefa se não há nenhuma em execução
                if not self.tarefa_em_execucao and tamanho_fila > 0:
                    self._start_new_task(scheduler)

                elif tamanho_fila > 0 and scheduler.ready_threads[tamanho_fila - 1].prioridade > self.tarefa_no_momento.prioridade:
                    
                    print(f"Thread: {self.tarefa_no_momento.id} retornou a fila de tarefas prontas no clock {scheduler.current_clock}")
                    nova_tarefa = scheduler.ready_threads.pop()
                    scheduler.ready_threads.append(self.tarefa_no_momento)
                    self.tarefa_no_momento = nova_tarefa
                    print(f"Thread: {self.tarefa_no_momento.id} escalonada no tempo de clock {scheduler.current_clock}\n")
                    
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
