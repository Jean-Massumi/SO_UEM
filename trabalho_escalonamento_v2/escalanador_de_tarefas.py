import time
import socket
import threading
from dataclasses import dataclass

@dataclass
class Tarefa:
    ID: str
    clock_de_ingresso: int
    duracao_prevista: int
    prioridade: int
    
@dataclass
class Tarefa_Finalizada:
    ID: str
    clock_de_ingresso: int
    clock_de_finalizacao: int
    turn_around_time: int
    waiting_time: int

class Escalonador:
    
    def __init__(self):
        
        self.algoritmo_escalonador :str = None #Determina qual algoritmo está sendo utilizado
        self.tarefas_finalizadas :list[Tarefa] = [] #Tarefas Finalizadas
        self.tarefa_em_execução: Tarefa = None #Tarefa em Execução
        self.porta :int = 4002 # Porta estrutura/comunicação
        self.running :bool = False # Para sincronização segura
        self.dados :str = None
        
    def start_server(self):
        
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.bind(("localhost",self.porta))
        self.running = True
        
        while self.running:
            try:
                #Aceitar conexão
                cliente, endereco = servidor.accept()
                print(f"Conexão de {endereco}")
                
                #Receber dados
                self.dados = cliente.recv(1024).decode('utf-8')
                
            except Exception as e:
                print(f"Erro no servidor: {e}")
                break
        
        servidor.close()        

    def algoritmos(self, fila_de_tarefas_prontas):
        
        if self.algoritmo_escalonador == "fcfs":
            self.fcfs(fila_de_tarefas_prontas)
    '''
    def inserir_tarefa(self, fila_de_tarefas_prontas: list[Tarefa]):
        pass
    def escrever_tarefas(self):
        pass
    
    def finalizar_programa(self):
        pass
    
    '''
    def fcfs(self, fila_de_tarefas: list[Tarefa]):
        
        clock = 0
        fila_de_tarefas_prontas = []
        contador = 0
        while True:
            
            if len(fila_de_tarefas_prontas) == 0 or contador < len(fila_de_tarefas):
                if contador < len(fila_de_tarefas):
                    while contador < len(fila_de_tarefas) and clock >= fila_de_tarefas[contador].clock_de_ingresso:
                        fila_de_tarefas_prontas.append(fila_de_tarefas[contador])
                        contador += 1
                else:
                    break
                
            if len(fila_de_tarefas) > 0:

                '''
                while fila_de_tarefas_prontas[0].clock_de_ingresso > clock:
                    time.sleep(1)
                    clock += 1
                    clock_de_ingresso = clock
                '''
                if self.tarefa_em_execução == None:
                    clock_de_ingresso = clock     
                    self.tarefa_em_execução = fila_de_tarefas_prontas.pop(0)
                    print(f"Tarefa de ID {self.tarefa_em_execução.ID} recebida no escalonador no clock {clock}, aguardou-se {clock - self.tarefa_em_execução.clock_de_ingresso} clocks para iniciar sua execução.")
                    print(f"Características da tarefa: entrou na lista de tarefas prontas no clock {self.tarefa_em_execução.clock_de_ingresso}, tem duração prevista de {self.tarefa_em_execução.duracao_prevista} e prioridade {self.tarefa_em_execução.prioridade}")
                    print()
                
                if clock >= clock_de_ingresso + self.tarefa_em_execução.duracao_prevista:
                    print(f"Tarefa de ID {self.tarefa_em_execução.ID} teve seu processamento finalizado no clock {clock}")
                    print()
                    self.tarefas_finalizadas.append(Tarefa_Finalizada(self.tarefa_em_execução.ID, self.tarefa_em_execução.clock_de_ingresso, clock, clock - self.tarefa_em_execução.clock_de_ingresso, clock_de_ingresso - self.tarefa_em_execução.clock_de_ingresso))
                    self.tarefa_em_execução = None
            
                
            clock+=1
            time.sleep(1)
        
teste = Escalonador()
lista_de_tarefas_prontas = [Tarefa('t0',0,6,2),Tarefa('t1',1,2,1),Tarefa('t2',2,8,3),Tarefa('t3',3,3,2),Tarefa('t4',5,4,1),Tarefa('t5',6,5,3)]
teste.fcfs(lista_de_tarefas_prontas)       
    
