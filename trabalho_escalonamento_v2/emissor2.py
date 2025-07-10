import socket
from collections import deque
from dataclasses import dataclass
from trabalho_escalonamento_v2.main import ready_threads
from time import sleep


@dataclass
class Thread:
    id: str
    tempo: int
    duracao: int
    prioridade: int



class EMISSOR:

    def __init__(self, host: str, emitter_port: int, scheduler_port: int, arquivo):
        self.host: str = host                           # Host do computador
        self.emitter_port: int = emitter_port           # Porta de escuta/comunicação do emissor
        self.scheduler_port: int = scheduler_port       # Porta de escuta/comunicação do escalonador
        self.servidor = None

        self.running: bool = False                      # Booleando para rodar o servidor
        self.message = -2                               # Mensagem recebida através de algum processo 
        self.task_file = arquivo                        # Arquivo que contém as Threads
        self.current_clock = 0


    def create_server(self):
        '''
            Cria e configura o servidor TCP do emissor para receber conexões
            de outros processos (clock e escalonador) na porta especificada
        '''
        
        print("Criando o servidor do emissor!")

        # Criar socket
        self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.servidor.bind((self.host, self.emitter_port))
        self.servidor.listen(3)
        self.servidor.settimeout(0.1)  # Timeout CURTO para não bloquear muito

        print("Servidor do emissor criado com sucesso!")


    def check_messages(self):
        '''
            Verifica se há mensagens recebidas (não bloqueia)
        '''
       
        try:
            # Aceitar conexão
            cliente, endereco = self.servidor.accept()
            
            # Receber dados
            self.message = cliente.recv(1024).decode('utf-8')
            print(f"📨 Mensagem recebida: {self.message}")    
            
            # Fechar conexão
            cliente.close()

            # Processar mensagem
            if self.message == "FIM":
                print("🛑 Comando FIM recebido!")
                self.running = False

            else:
                try:
                    self.current_clock = int(self.message)

                except ValueError:
                    print(f"⚠️ Mensagem inválida recebida: {self.message}")

        except socket.timeout:
            # Normal - não havia mensagem
            pass
                
        except Exception as e:
            print(f"Erro no servidor: {e}")


    def close_server(self):
        '''
            Fecha o servidor do emissor
        '''
        print("Encerrando o servidor do emissor!")

        if self.servidor:
            self.servidor.close()

        print("Servidor do emissor encerrado com sucesso!")


    def communication_scheduler(self):
        '''
            Comunica com o escalonador
        '''

        try:
            # Cliente do servidor do ESCALONADOR
            cliente_escalonador = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente_escalonador.settimeout(1.0)  # Timeout para conexão
            cliente_escalonador.connect((self.host, self.scheduler_port))   

            # Mensagem Enviada ao ESCALONADOR
            mensagem_escalonador = "TAREAFAS FINALIZADAS"
            cliente_escalonador.send(mensagem_escalonador.encode())

            cliente_escalonador.close()
            
        except Exception as e:
            print(f"❌ Erro ao comunicar com escalonador: {e}")


    def communication_clock(self):
        '''
            Comunica com o clock
        '''
        try:
            cliente_clock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente_clock.settimeout(1.0)  # Timeout para conexão
            cliente_clock.connect((self.host, 4000))

            mensagem_clock = "INICIAR CLOCK"
            cliente_clock.send(mensagem_clock.encode())

            cliente_clock.close()
            
        except Exception as e:
            print(f"❌ Erro ao comunicar com clock: {e}")




    def task_checker(self):
        '''
            Informa ao escalonador, quais tarefas já estão prontas
        '''

        # Sinaliza a inicialização do clock
        self.communication_clock()

        print("Clock Inicializado")

        # Variavel para saber quando uma nova mensagem é recebida!
        old_clock = -1

        try:

            with open(self.task_file, 'r') as arq:
                linhas = arq.readlines()

            # Contador de linha
            i = 0
            while True:

                # Verifica se o servidor do emissor recebeu alguma mensagem
                self.check_messages()

                if old_clock != self.message and i < len(linhas):
                    # Remove os espaços em branco do inicio e fim da linha
                    linha = linhas[i].strip()

                    if linha:
                        # Armazena os dados da linha em um lista .
                        linha_atual = linha.split(';')

                        # Verifica se a Thread pode ser mandado naquele tempo de clock
                        # para a lista de tarefas prontas
                        # print(f"tempo {linha_atual[1]}") remover depois

                        # print(f"message {self.message}") remover depois

                        if linha_atual[1] == self.message:
                            thread = Thread(
                                    id = linha_atual[0],
                                    tempo = int(linha_atual[1]),
                                    duracao = int(linha_atual[2]),
                                    prioridade = int(linha_atual[3])
                                )
                            print(f"Thread com tempo: {linha_atual[1]} entrando no tempo de clock {self.message}")
                            
                            # Insere a(s) Thread(s) que estão pronta na lista
                            # de tarefas prontas.
                            ready_threads.appendleft(thread)

                            if i + 1 < len(linhas):
                                proxima_linha = linhas[i + 1].strip().split(';')
                                
                                if proxima_linha[1] == self.message:
                                    i += 1  # Incrementar i antes de continuar
                                    continue
                        else:
                            continue

                    old_clock = self.message
                    i += 1

                if i >= len(linhas):
                    print(f"Sequencia de tarefas prontas {ready_threads}")
                    cliente_clock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    cliente_clock.settimeout(1.0)  # Timeout para conexão
                    cliente_clock.connect((self.host, 4000))

                    mensagem_clock = "FIM"
                    cliente_clock.send(mensagem_clock.encode())

                    cliente_clock.close()
                    break

                if self.message == "FIM":
                    self.close_server()
                    break
                        
        
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {self.task_file}")

        except Exception as e:
            print(f"❌ Erro ao processar tarefas: {e}")


    def start(self):
        '''
            Inicia o emissor
        '''
        try:
            # Cria o servidor
            self.create_server()

            # Inicia o processamento
            self.task_checker()
            
        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")
            self.running = False
            self.close_server()
        except Exception as e:
            print(f"❌ Erro geral: {e}")
            self.close_server()
            


emissor = EMISSOR("localhost", 4001, 4002, "entrada00.txt")

emissor.start()

