import socket
from dataclasses import dataclass
from collections import deque
import json
import sys
import math

@dataclass
class TempoExecucao:
    tempo_total: int
    tempo_restante: int

    @classmethod
    def criar(cls, tempo):
        return cls(tempo_total=tempo, tempo_restante=tempo)


@dataclass
class Thread:
    '''
        Representa uma thread a ser escalonado        
    '''

    id: str
    tempo_ingresso: int
    duracao_prevista: TempoExecucao
    prioridade: int

    @classmethod
    def from_dict(cls, data):
        '''
            Cria uma instância de Thread a partir de um dicionário
        '''

        return cls(
            id=data['id'],
            tempo_ingresso=data['tempo_ingresso'],
            duracao_prevista= TempoExecucao.criar(data['duracao_prevista']),
            prioridade=data['prioridade']
        )


@dataclass
class Tarefa_Finalizada:
    '''
        Armazena informações de uma tarefa que foi concluída
    '''

    ID: str
    clock_de_ingresso: int
    clock_de_finalizacao: int
    turn_around_time: int
    waiting_time: int


class ESCALONADOR:
    '''
        Classe principal do escalonador que implementa diferentes algoritmos
        de escalonamento de threads
    '''
    
    def __init__(self, host: str, clock_port: int, emitter_port: int, scheduler_port: int, algoritmo: str):
        self.host: str = host                           # Endereço ID do servidor
        self.scheduler_port: int = scheduler_port       # Porta do servidor do ESCALONADOR
        self.clock_port: int = clock_port               # Porta de destino do CLOCK
        self.emitter_port: int = emitter_port           # Porta de destino do EMISSOR
        self.servidor = None                            # Socket servidor

        self.emitter_completed = False                  # Flag indicando se o emissor terminou
        self.current_clock = None                       # Valor atual do clock recebido
        self.algoritmo = algoritmo                      # Algoritmo de escalonamento escolhido
        

        # Fila de threads prontas para execução
        self.ready_threads: deque[Thread] = deque()
        
        # Determina a política de inserção de tarefas na fila de tarefas prontas
        self.algoritmo_de_insercao = None               

        # Nome do arquivo de saída
        self.output_file = f"algoritmo_{algoritmo}.txt"
        


    def create_server(self):
        '''
            Cria e configura o servidor do escalonador.
            
            Estabelece um socket servidor que escuta na porta especificada,
            aguardando pulsos do clock e comando do emissor de tareafas.
        '''
        
        print("Criando o servidor do escalonador!")

        # Criar socket
        self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.servidor.bind((self.host, self.scheduler_port))
        self.servidor.listen(3)
        self.servidor.settimeout(0.1)  # Timeout CURTO para não bloquear muito

        print("Servidor do escalonador criado com sucesso! \n")



    def check_messages(self):
        '''
            Escuta e processa mensagens recebidas.
            
            Aceita conexões não-bloqueantes e processa os seguintes tipos:
            - "CLOCK: {valor}": Atualiza o clock atual do sistema
            - "NEW THREAD": Adiciona a thread na fila de tarefas prontas
            - "TAREFAS FINALIZADAS": Avisa o escalador que o emissor já emitiu 
            todas as tarefas.          
        '''
       
        try:
            # Aceitar conexão
            cliente, endereco = self.servidor.accept()
            
            # Receber dados
            message = cliente.recv(1024).decode('utf-8')

            # Processar mensagem
            try:
                # Tentar parsear como JSON
                data = json.loads(message)
                
                if data.get('type') == 'NEW_THREAD':
                    # Receber nova thread do emissor
                    thread = Thread.from_dict(data['thread'])
                    
                    if self.algoritmo_de_insercao == "duração":
                        self.inserction_by_shortTime(thread)
                    else:
                        # fila de tarefas prontas sempre está em ordem crescente do tempo de ingresso das tarefas na fila
                        self.ready_threads.appendleft(thread)
                    
                elif data.get('type') == 'TAREFAS_FINALIZADAS':
                    self.emitter_completed = True

                    print("TAREFAS FINALIZADAS PELO EMISSOR recebido! \n ")
                    
            except json.JSONDecodeError:
                # Mensagem não é JSON, processar como string
                if message.startswith("CLOCK: "):
                    self.current_clock = message[7:]
            
            # Fechar conexão
            cliente.close()

        except socket.timeout:
            # Normal - não havia mensagem
            pass
                
        except Exception as e:
            print(f"Erro no servidor: {e}")



    def close_server(self):
        '''
            Encerra o servidor do escalonador de forma segura.
            
            Fecha o socket servidor, liberando recursos e a porta utilizada.
            Chamado automaticamente ao finalizar o sistema. 
        '''

        print("\nEncerrando o servidor do escalonador!")

        if self.servidor:
            self.servidor.close()

        print("Servidor do escalonador encerrado com sucesso! \n")



    def communication_clock(self):
        '''
            Envia mensagem de encerramento para o processo clock 
        '''
 
        try:            
            # Cliente do servidor do CLOCK
            cliente_clock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente_clock.settimeout(1.0)  # Timeout para conexão
            cliente_clock.connect((self.host, self.clock_port))

            # Mensagem Enviada ao CLOCK
            mensagem_clock = "ESCALONADOR: ENCERRADO"
            cliente_clock.send(mensagem_clock.encode())

            cliente_clock.close()
            
        except Exception as e:
            print(f"Erro ao comunicar com clock: {e}")



    def communication_emitter(self):
        '''
            Envia mensagem de encerramento para o processo emissor
        '''
        
        try:
            # Cliente do servidor do EMISSOR DE TAREFAS
            cliente_emissor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente_emissor.settimeout(1.0)  # Timeout para conexão
            cliente_emissor.connect((self.host, self.emitter_port))  

            # Mensagem Enviada ao EMISSOR DE TAREFAS
            mensagem_emissor = "ESCALONADOR: ENCERRADO"
            cliente_emissor.send(mensagem_emissor.encode())

            cliente_emissor.close()
            
        except ConnectionRefusedError:
            print(f"Emissor não está rodando na porta {self.emitter_port}")

        except Exception as e:
            print(f"Erro ao comunicar com emissor: {e}")



    def write_to_output_file(self, thread_id: str):
        '''
            Escreve o ID da thread em execução no arquivo de saída
        '''

        try:
            with open(self.output_file, "a") as f:
                f.write(f"{thread_id};")

        except Exception as e:
            print(f"Erro ao escrever no arquivo: {e}")



    def write_final_statistics(self, tarefas_concluidas: list[Tarefa_Finalizada]):
        '''
            Escreve as estatísticas finais no arquivo de saída
        '''

        try:
            with open(self.output_file, "a") as f:
                f.write("\n")  # Nova linha após a sequência de execução
                
                tarefas_concluidas.sort(key = lambda ordem: ordem.ID)
                
                # Escrever informações de cada tarefa
                for tarefa in tarefas_concluidas:
                    f.write(f"{tarefa.ID};{tarefa.clock_de_ingresso};{tarefa.clock_de_finalizacao};{tarefa.turn_around_time};{tarefa.waiting_time}\n")
                
                # Calcular médias
                if tarefas_concluidas:
                    media_turnaround = sum(t.turn_around_time for t in tarefas_concluidas) / len(tarefas_concluidas)
                    media_waiting = sum(t.waiting_time for t in tarefas_concluidas) / len(tarefas_concluidas)
                    
                    # Arredondar para cima com 1 casa decimal
                    media_turnaround_rounded = math.ceil(media_turnaround * 10) / 10
                    media_waiting_rounded = math.ceil(media_waiting * 10) / 10
                    
                    f.write(f"{media_turnaround_rounded:.1f};{media_waiting_rounded:.1f}\n")
                else:
                    f.write("0.0;0.0\n")
                    
        except Exception as e:
            print(f"Erro ao escrever estatísticas finais: {e}")


    def inserction_by_shortTime(self, tarefa: Thread):
        
        '''
            Política de inserção de tarefa na fila de tarefa prontas.
            Nesta politica a fila deve estar sempre em ordem crescente em relação ao tempo de duração prevista das tarefas
        '''

        pos_final = len(self.ready_threads) - 1
      
        if len(self.ready_threads) == 0:
            self.ready_threads.appendleft(tarefa)
            #print(f"Aqui: {self.ready_threads}")
        elif self.ready_threads[0].duracao_prevista.tempo_restante <= tarefa.duracao_prevista.tempo_restante:
            self.ready_threads.appendleft(tarefa)
            #print(f"Aqui 2: {self.ready_threads}")
        
        elif self.ready_threads[pos_final].duracao_prevista.tempo_restante >= tarefa.duracao_prevista.tempo_restante:
            self.ready_threads.append(tarefa)

        else:
            auxiliar = deque()
            b = True     
            
            while len(self.ready_threads) > 0:
                aux = self.ready_threads.pop()
                if aux.duracao_prevista.tempo_restante > tarefa.duracao_prevista.tempo_restante and b == True:
                    auxiliar.appendleft(tarefa)
                    b = False
                auxiliar.appendleft(aux)
            
            self.ready_threads = auxiliar
            
            
        

    def fcfs(self):
        '''
            Implementa o algoritmo First-Come First-Served (FCFS)
            Executa as threads na ordem de chegada
        '''

        tarefa_em_execucao = False
        old_clock = None
        tarefa_no_momento: Thread
        tarefas_concluidas: list[Tarefa_Finalizada] = []

        # Loop principal do escalonador
        while not (self.emitter_completed and len(self.ready_threads) == 0 and not tarefa_em_execucao):
            
            # Verificar mensagens (incluindo novas threads)
            self.check_messages()

            # Processar apenas quando o clock muda
            if old_clock != self.current_clock and self.current_clock is not None:
                print(f"Clock: {self.current_clock}, Threads prontas: {len(self.ready_threads)}")

                # Iniciar nova tarefa se não há nenhuma em execução
                if not tarefa_em_execucao and len(self.ready_threads) > 0:
                    tarefa_no_momento = self.ready_threads.pop()    
                    print(f"Thread: {tarefa_no_momento.id} escalonada no tempo de clock {self.current_clock}\n")
                    tarefa_em_execucao = True

                # Processar tarefa em execução
                if tarefa_em_execucao:     
                    
                    # Verificar se a tarefa foi concluída
                    if tarefa_no_momento.duracao_prevista.tempo_restante == 0:
                        id_tarefa = tarefa_no_momento.id
                        tempo_ingresso = tarefa_no_momento.tempo_ingresso
                        tempo_finalizacao = int(self.current_clock)
                        turnaround_time = tempo_finalizacao - tempo_ingresso
                        waiting_time = tempo_finalizacao - (tarefa_no_momento.duracao_prevista.tempo_total + tarefa_no_momento.tempo_ingresso)

                        tarefas_concluidas.append(Tarefa_Finalizada(
                            id_tarefa,
                            tempo_ingresso,
                            tempo_finalizacao, 
                            turnaround_time,
                            waiting_time
                        ))
                        
                        print(f"Thread: {id_tarefa} finalizada no clock {tempo_finalizacao}\n")
                        tarefa_em_execucao = False
                        continue
                    
                    # Escrever no arquivo de saída imediatamente
                    self.write_to_output_file(tarefa_no_momento.id)

                    # Decrementar a duração da tarefa
                    tarefa_no_momento.duracao_prevista.tempo_restante -= 1
                    
                old_clock = self.current_clock

        print("Tarefas concluídas!")
     
        # Escrever estatísticas finais no arquivo
        self.write_final_statistics(tarefas_concluidas)
        
        # Encerrar comunicação com outros processos
        self.communication_clock()
        self.communication_emitter()
        self.close_server()

        print("ESCALONADOR ENCERRADO POR COMPLETO!")
        
    def rr(self):
        
        '''
            Implementa o algoritmo Round Robin (RR).
            Executa as threads na ordem de chegada em um tempo(quantum) de 3 clocks.
            Se há tarefa não finalizou durante este tempo ela retorna para o fim da fila de tarefas prontas.
        '''
        
        quantum = 3 #Quantidade de clocks que uma tarefa permanece no escalonador antes de retornar para a fila de espera
        
        tarefa_em_execucao = False
        old_clock = None
        tarefa_no_momento: Thread
        tarefas_concluidas: list[Tarefa_Finalizada] = []

        
        quantum_da_tarefa = 0
        
        # Loop principal do escalonador
        while not (self.emitter_completed and len(self.ready_threads) == 0 and not tarefa_em_execucao):
            
            # Verificar mensagens (incluindo novas threads)
            self.check_messages()

            # Processar apenas quando o clock muda
            if old_clock != self.current_clock and self.current_clock is not None:
                print(f"Clock: {self.current_clock}, Threads prontas: {len(self.ready_threads)}")

                # Iniciar nova tarefa se não há nenhuma em execução
                if not tarefa_em_execucao and len(self.ready_threads) > 0:
                    tarefa_no_momento = self.ready_threads.pop()

                    print(f"Thread: {tarefa_no_momento.id} escalonada no tempo de clock {self.current_clock}\n")

                    quantum_da_tarefa = quantum
                    tarefa_em_execucao = True

                # Processar tarefa em execução
                if tarefa_em_execucao:
                    
                    
                    # Verificar se a tarefa foi concluída
                    if tarefa_no_momento.duracao_prevista.tempo_restante == 0:
                        id_tarefa = tarefa_no_momento.id
                        tempo_ingresso = tarefa_no_momento.tempo_ingresso
                        tempo_finalizacao = int(self.current_clock)
                        turnaround_time = tempo_finalizacao - tempo_ingresso
                        waiting_time = tempo_finalizacao - (tarefa_no_momento.duracao_prevista.tempo_total + tempo_ingresso)

                        tarefas_concluidas.append(Tarefa_Finalizada(
                            id_tarefa,
                            tempo_ingresso,
                            tempo_finalizacao, 
                            turnaround_time,
                            waiting_time
                        ))
                        
                        print(f"Thread: {id_tarefa} finalizada no clock {tempo_finalizacao}\n")
                        tarefa_em_execucao = False
                        continue

                    if (quantum_da_tarefa == 0 and len(self.ready_threads) > 0):
                        print(f"Thread: {tarefa_no_momento.id} retornou a fila de espera no clock {self.current_clock}\n")
                        self.ready_threads.appendleft(tarefa_no_momento)
                    
                        tarefa_em_execucao = False
                        continue
                    
                    # Escrever no arquivo de saída imediatamente
                    self.write_to_output_file(tarefa_no_momento.id)
                    
                        
                    tarefa_no_momento.duracao_prevista.tempo_restante -= 1
                    quantum_da_tarefa -= 1
                        
                old_clock = self.current_clock

        print("Tarefas concluídas!")
     
        # Escrever estatísticas finais no arquivo
        self.write_final_statistics(tarefas_concluidas)
        
        # Encerrar comunicação com outros processos
        self.communication_clock()
        self.communication_emitter()
        self.close_server()
        
    
    def sjf(self):
        '''
            Implementa o algoritmo Shortest Job First (SJF)
            Executa as threads na ordem de duração prevista da tarefa
        '''
        tarefa_em_execucao = False
        old_clock = None
        tarefa_no_momento: Thread
        tarefas_concluidas: list[Tarefa_Finalizada] = []

        # Loop principal do escalonador
        while not (self.emitter_completed and len(self.ready_threads) == 0 and not tarefa_em_execucao):
            
            # Verificar mensagens (incluindo novas threads)
            self.check_messages()

            # Processar apenas quando o clock muda
            if old_clock != self.current_clock and self.current_clock is not None:
                print(f"Clock: {self.current_clock}, Threads prontas: {len(self.ready_threads)}")

                # Iniciar nova tarefa se não há nenhuma em execução
                if not tarefa_em_execucao and len(self.ready_threads) > 0:
                    tarefa_no_momento = self.ready_threads.pop()    
                    inicio_da_execucao = int(self.current_clock)

                    print(f"Thread: {tarefa_no_momento.id} escalonada no tempo de clock {self.current_clock}\n")

                    tarefa_em_execucao = True

                # Processar tarefa em execução
                if tarefa_em_execucao:     
                    
                    # Verificar se a tarefa foi concluída
                    if tarefa_no_momento.duracao_prevista.tempo_restante == 0:
                        id_tarefa = tarefa_no_momento.id
                        tempo_ingresso = tarefa_no_momento.tempo_ingresso
                        tempo_finalizacao = int(self.current_clock)
                        turnaround_time = tempo_finalizacao - tempo_ingresso
                        waiting_time = inicio_da_execucao - tempo_ingresso

                        tarefas_concluidas.append(Tarefa_Finalizada(
                            id_tarefa,
                            tempo_ingresso,
                            tempo_finalizacao, 
                            turnaround_time,
                            waiting_time
                        ))
                        
                        print(f"Thread: {id_tarefa} finalizada no clock {tempo_finalizacao}\n")
                        tarefa_em_execucao = False
                        continue
                    
                    # Escrever no arquivo de saída imediatamente
                    self.write_to_output_file(tarefa_no_momento.id)

                    # Decrementar a duração da tarefa
                    tarefa_no_momento.duracao_prevista.tempo_restante -= 1
                    
                old_clock = self.current_clock

        print("Tarefas concluídas!")
     
        # Escrever estatísticas finais no arquivo
        self.write_final_statistics(tarefas_concluidas)
        
        # Encerrar comunicação com outros processos
        self.communication_clock()
        self.communication_emitter()
        self.close_server()

        print("ESCALONADOR ENCERRADO POR COMPLETO!")
        

    def start(self):
        '''
            Inicia o escalonador e executa o algoritmo selecionado
        '''

        try:
            # Cria o servidor
            self.create_server()

            # Limpar o arquivo de saída antes de iniciar
            with open(self.output_file, "w") as f:
                f.write("")

            # Algoritmo escolhido
            if self.algoritmo == "fcfs":
                self.fcfs()

            elif self.algoritmo == "rr":
                self.rr()

            elif self.algoritmo == "sjf":
                self.algoritmo_de_insercao = "duração"
                self.sjf()

            elif self.algoritmo == "srtf":
                print("srtf")

            elif self.algoritmo == "prioc":
                print("prioc")

            elif self.algoritmo == "priop":
                print("priop")

            elif self.algoritmo == "priod":
                print("priod")

            else:
                print("Argumento de algoritmo inválido!")
                self.close_server()
            
        except KeyboardInterrupt:
            print("Interrompido pelo usuário")
            self.close_server()

        except Exception as e:
            print(f"Erro geral: {e}")
            self.close_server()



if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Erro: Você deve passar exatamente 2 argumentos!")
        print("Uso: python3 escalonador_de_tarefas.py <algoritmo>!")

    algoritmo = sys.argv[1]

    # Portas de comunicação
    clock_port = 4000
    emitter_port = 4001
    scheduler_port = 4002

    # Host local
    host = "localhost"

    escalonador = ESCALONADOR(host, clock_port, emitter_port, scheduler_port, algoritmo)

    escalonador.start()


















