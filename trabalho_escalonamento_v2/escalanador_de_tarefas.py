import socket
from dataclasses import dataclass
from collections import deque
import json
import sys
import math


@dataclass
class Thread:
    id: str
    tempo_ingresso: int
    duracao_prevista: int
    prioridade: int

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data['id'],
            tempo_ingresso=data['tempo_ingresso'],
            duracao_prevista=data['duracao_prevista'],
            prioridade=data['prioridade']
        )
    

@dataclass
class Tarefa_Finalizada:
    ID: str
    clock_de_ingresso: int
    clock_de_finalizacao: int
    turn_around_time: int
    waiting_time: int


class ESCALONADOR:
    
    def __init__(self, host: str, clock_port: int, emitter_port: int, scheduler_port: int, algoritmo: str):
        self.host: str = host                           # Host do computador
        self.clock_port: int = clock_port               # Porta de escuta/comunicação do clocks
        self.emitter_port: int = emitter_port           # Porta de escuta/comunicação do emissor
        self.scheduler_port: int = scheduler_port       # Porta de escuta/comunicação do escalonador
        self.servidor = None

        self.emitter_completed = False                  # Booleano para saber quando o emissor terminou todas as tarefas
        self.current_clock = None

        self.algoritmo = algoritmo

        # Fila de threads prontas local ao escalonador
        self.ready_threads: deque[Thread] = deque()

        # self.tarefas_finalizadas :list[Tarefa] = [] #Tarefas Finalizadas
        # self.tarefa_em_execução: Tarefa = None #Tarefa em Execução
        # self.porta :int = 4002 # Porta estrutura/comunicação

        # Nome do arquivo de saída
        self.output_file = f"algoritmo_{algoritmo}.txt"
        

    def create_server(self):
        '''
            Cria e configura o servidor TCP do emissor para receber conexões
            de outros processos (clock e escalonador) na porta especificada
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
            Verifica se há mensagens recebidas (não bloqueia)
        '''
       
        try:
            # Aceitar conexão
            cliente, endereco = self.servidor.accept()
            
            # Receber dados
            message = cliente.recv(1024).decode('utf-8')
            #print(f"Mensagem recebida: {message}")    
            
            # Fechar conexão
            cliente.close()

            # Processar mensagem
            try:
                # Tentar parsear como JSON
                data = json.loads(message)
                
                if data.get('type') == 'NEW_THREAD':
                    # Receber nova thread do emissor
                    thread = Thread.from_dict(data['thread'])
                    self.ready_threads.appendleft(thread)

                    print(f"Nova thread recebida: {thread.id} \n")
                    
                elif data.get('type') == 'TAREFAS_FINALIZADAS':
                    self.emitter_completed = True

                    print("Comando TAREFAS FINALIZADAS PELO EMISSOR recebido! \n ")
                    
            except json.JSONDecodeError:
                # Mensagem não é JSON, processar como string
                if message.startswith("CLOCK: "):
                    self.current_clock = message[7:]

        except socket.timeout:
            # Normal - não havia mensagem
            pass
                
        except Exception as e:
            print(f"Erro no servidor: {e}")


    def close_server(self):
        '''
            Fecha o servidor do emissor
        '''
        print("Encerrando o servidor do escalonador!")

        if self.servidor:
            self.servidor.close()

        print("Servidor do escalonador encerrado com sucesso! \n")


    def communication_clock(self):
        '''
            Comunica com o clock
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
            Comunica com o emissor de tarefas
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



    def fcfs(self):
        tarefa_em_execucao = False
        old_clock = -1
        tarefa_no_momento: Thread
        tarefas_concluidas: list[Tarefa_Finalizada] = []

        # Lista para armazenar o log de execução
        execution_log = []

        while not (self.emitter_completed and len(self.ready_threads) == 0 and not tarefa_em_execucao):
            
            # Verificar mensagens (incluindo novas threads)
            self.check_messages()
            
            if old_clock != self.current_clock and self.current_clock is not None:
                print(f"Clock: {self.current_clock}, Threads prontas: {len(self.ready_threads)}")

                # Verificar se há threads prontas para executar
                if not tarefa_em_execucao and len(self.ready_threads) > 0:
                    tarefa_no_momento = self.ready_threads.pop()    
                    inicio_da_execucao = int(self.current_clock)

                    print(f"Thread: {tarefa_no_momento.id} iniciada no tempo de ingresso {tarefa_no_momento.tempo_ingresso} no clock {self.current_clock}")

                    tarefa_em_execucao = True

                # Se há uma tarefa em execução, registrar no log e processar
                if tarefa_em_execucao:     
                    
                    # Verificar se a tarefa foi concluída
                    if tarefa_no_momento.duracao_prevista == 0:
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
                        
                        print(f"Thread: {id_tarefa} finalizada no clock {tempo_finalizacao}")
                        tarefa_em_execucao = False
                        continue

                    # Registrar a execução da tarefa neste clock
                    execution_log.append(tarefa_no_momento.id)
                    
                    # Escrever no arquivo de saída imediatamente
                    self.write_to_output_file(tarefa_no_momento.id)

                    # Decrementar a duração da tarefa
                    tarefa_no_momento.duracao_prevista -= 1
                    
                old_clock = self.current_clock

        print("Tarefas concluídas:")
        for tarefa in tarefas_concluidas:
            print(f"ID: {tarefa.ID}, Ingresso: {tarefa.clock_de_ingresso}, Finalização: {tarefa.clock_de_finalizacao}, Turnaround: {tarefa.turn_around_time}, Waiting: {tarefa.waiting_time}")

        # Escrever estatísticas finais no arquivo
        self.write_final_statistics(tarefas_concluidas)
        
        self.communication_clock()
        self.communication_emitter()
        self.close_server()

        


    # def fcfs(self, fila_de_tarefas: list[Tarefa]):
        
    #     clock = 0
    #     fila_de_tarefas_prontas = []
    #     contador = 0
    #     while True:
            
    #         if len(fila_de_tarefas_prontas) == 0 or contador < len(fila_de_tarefas):
    #             if contador <  len(fila_de_tarefas):
    #                 while contador < len(fila_de_tarefas) and clock >= fila_de_tarefas[contador].clock_de_ingresso:
    #                     fila_de_tarefas_prontas.append(fila_de_tarefas[contador])
    #                     contador += 1
    #             else:
    #                 break
                
    #         if len(ready_threads) > 0:

    #             '''
    #             while fila_de_tarefas_prontas[0].clock_de_ingresso > clock:
    #                 time.sleep(1)
    #                 clock += 1
    #                 clock_de_ingresso = clock
    #             '''
    #             if self.tarefa_em_execução == None:
    #                 clock_de_ingresso = clock     
    #                 self.tarefa_em_execução = fila_de_tarefas_prontas.pop(0)
    #                 print(f"Tarefa de ID {self.tarefa_em_execução.ID} recebida no escalonador no clock {clock}, aguardou-se {clock - self.tarefa_em_execução.clock_de_ingresso} clocks para iniciar sua execução.")
    #                 print(f"Características da tarefa: entrou na lista de tarefas prontas no clock {self.tarefa_em_execução.clock_de_ingresso}, tem duração prevista de {self.tarefa_em_execução.duracao_prevista} e prioridade {self.tarefa_em_execução.prioridade}")
    #                 print()
                
    #             if clock >= clock_de_ingresso + self.tarefa_em_execução.duracao_prevista:
    #                 print(f"Tarefa de ID {self.tarefa_em_execução.ID} teve seu processamento finalizado no clock {clock}")
    #                 print()
    #                 self.tarefas_finalizadas.append(Tarefa_Finalizada(self.tarefa_em_execução.ID, self.tarefa_em_execução.clock_de_ingresso, clock, clock - self.tarefa_em_execução.clock_de_ingresso, clock_de_ingresso - self.tarefa_em_execução.clock_de_ingresso))
    #                 self.tarefa_em_execução = None
            
                
    #         clock+=1
    #         time.sleep(1)
        
# teste = ESCALONADOR()
# lista_de_tarefas_prontas = [Tarefa('t0',0,6,2),Tarefa('t1',1,2,1),Tarefa('t2',2,8,3),Tarefa('t3',3,3,2),Tarefa('t4',5,4,1),Tarefa('t5',6,5,3)]
# teste.fcfs(lista_de_tarefas_prontas)       
    


    def start(self):
        '''
            Inicia o escalonador
        '''
        try:
            # Cria o servidor
            self.create_server()

            # Limpar o arquivo antes de iniciar
            with open("algoritmo_fcfs.txt", "w") as f:
                f.write("")

            # Algoritmo escolhido
            if self.algoritmo == "fcfs":
                self.fcfs()

            elif self.algoritmo == "rr":
                print("rr")

            elif self.algoritmo == "sjf":
                print("sjf")

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

    algoritmo = sys.argv[1]

    # Portas de comunicação
    clock_port = 4000
    emitter_port = 4001
    scheduler_port = 4002

    # Host local
    host = "localhost"

    escalonador = ESCALONADOR(host, clock_port, emitter_port, scheduler_port, algoritmo)

    escalonador.start()

















