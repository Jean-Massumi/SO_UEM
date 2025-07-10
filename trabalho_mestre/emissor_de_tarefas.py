import socket
import threading
from collections import deque
from dataclasses import dataclass


@dataclass
class Thread:
    id: str
    tempo: int
    duracao: int
    prioridade: int





class EMISSOR:

    def __init__(self, host: str, emitter_port: int, scheduler_port: int, arquivo: list):
        self.host: str = host                           # Host do computador
        self.emitter_port: int = emitter_port           # Porta de escuta/comunicação do emissor
        self.scheduler_port: int = scheduler_port       # Porta de escuta/comunicação do escalonador

        self.running: bool = False                      # Booleando para rodar o servidor
        self.message = None                             # Mensagem recebida através de algum processo 
        self.task_file = arquivo


    def start_server(self):
        '''
            Inicia o servidor para receber mensagens do cliente
        '''
        
        # Criar socket
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        servidor.bind((self.host, self.emitter_port))
        servidor.listen(3)
        self.running = True

        while self.running:
            try:
                # Aceitar conexão
                cliente, endereco = servidor.accept()
                print(f"Conexão de {endereco}")
                
                # Receber dados
                self.message = cliente.recv(1024).decode('utf-8')
                                
                # Fechar conexão
                cliente.close()

                if self.message == "FIM":
                    self.running = False
                    print("Servidor do Emissor encerrado")
                    
            except Exception as e:
                print(f"Erro no servidor: {e}")
                break


    def task_checker(self):
        '''
            Informa ao escalonador, quais tarefas já estão prontas
        '''

        # Variavel para saber quando uma nova mensagem é recebida!
        old_clock = None

        # Cliente do servidor do ESCALONADOR
        cliente_escalonador = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente_escalonador.connect((self.host, self.scheduler_port))  


        with open(self.task_file, 'r') as arq:
            linhas = arq.readlines()

            for i, linha in enumerate(linhas):
                linha = linha.strip()


                # funcao para verificar se foi recebido alguma mensagem do clock 
                # principalmente ou do escalonador quando acabar as tarefas de 
                # prontas completamente

                if linha:
                    dados = linha.split(';')

                    # o self.clock é o tempo que o clock está, ele serve para saber quais
                    # tarefas estão nesse tempo e poder adicionar em uma lista de prontas. 
                    if dados[1] == self.message:
                        thread = Thread(
                                id = dados[0],
                                tempo = int(dados[1]),
                                duracao = int(dados[2]),
                                prioridade = int(dados[3])
                            )
                        threads.append(thread)

                if i + 1 < len(linhas):
                    proxima_linha = linhas[i + 1].strip().split(';')
                
                    if proxima_linha[1] == self.message:
                        continue

                while True:
                    # serve para saber se o clock avancou, caso nao o loop fica rodando.
                    # não permite o for avancar ate que o clock seja avancado.
                    if old_clock != self.message:
                        break

            old_clock = self.message










        while True:

            if action_tick != self.mensagem:

                if self.mensagem == self.threads_list[]
                self.threads_list.popleft()




                action_tick = self.mensagem





                # Mensagem Enviada ao ESCALONADOR
                mensagem_escalonador = ...
                cliente_escalonador.send()









