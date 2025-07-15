import socket
from dataclasses import dataclass
import sys
import json

@dataclass
class Thread:
    id: str
    tempo_ingresso: int
    duracao_prevista: int
    prioridade: int

    def to_dict(self):
        return {
            'id': self.id,
            'tempo_ingresso': self.tempo_ingresso,
            'duracao_prevista': self.duracao_prevista,
            'prioridade': self.prioridade
        }


class EMISSOR:

    def __init__(self, host: str, clock_port: int, emitter_port: int, scheduler_port: int, arquivo):
        self.host: str = host                           # Host do computador
        self.clock_port: int = clock_port               # Porta de escuta/comunicação do clock
        self.emitter_port: int = emitter_port           # Porta de escuta/comunicação do emissor
        self.scheduler_port: int = scheduler_port       # Porta de escuta/comunicação do escalonador
        self.servidor = None

        self.task_file = arquivo                        # Arquivo que contém as Threads
        self.current_clock = None                       # Contador de clock
        self.running = True                             # Flag para iniciar a fila de threads



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

        print("Servidor do emissor criado com sucesso! \n")



    def check_messages(self):
        '''
            Verifica se há mensagens recebidas (não bloqueia)
        '''
       
        try:
            # Aceitar conexão
            cliente, endereco = self.servidor.accept()
            
            # Receber dados
            message = cliente.recv(1024).decode('utf-8')
            print(f"Mensagem recebida: {message}")    
            
            # Fechar conexão
            cliente.close() 

            # Processar mensagem
            if message == "ESCALONADOR: ENCERRADO":
                self.running = False
                print("Comando FIM recebido! \n")

            elif message.startswith("CLOCK: "):
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
        print("Encerrando o servidor do emissor!")

        if self.servidor:
            self.servidor.close()

        print("Servidor do emissor encerrado com sucesso! \n")



    def send_thread_to_scheduler(self, thread: Thread):
        '''
            Envia uma thread para o escalonador via socket
        '''

        try:
            cliente_escalonador = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente_escalonador.settimeout(1.0)
            cliente_escalonador.connect((self.host, self.scheduler_port))
            
            # Enviar thread como JSON
            thread_data = {
                'type': 'NEW_THREAD',
                'thread': thread.to_dict()
            }

            mensagem = json.dumps(thread_data)
            cliente_escalonador.send(mensagem.encode())
            cliente_escalonador.close()
            
        except Exception as e:
            print(f"Erro ao enviar thread para escalonador: {e}")



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
            mensagem_escalonador = json.dumps({'type': 'TAREFAS_FINALIZADAS'})              
            cliente_escalonador.send(mensagem_escalonador.encode())

            cliente_escalonador.close()
            
        except Exception as e:
            print(f"Erro ao comunicar com escalonador: {e}")



    def communication_clock(self):
        '''
            Comunica com o clock
        '''
        try:
            cliente_clock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente_clock.settimeout(1.0)  # Timeout para conexão
            cliente_clock.connect((self.host, self.clock_port))

            mensagem_clock = "EMISSOR: INICIAR CLOCK"
            cliente_clock.send(mensagem_clock.encode())

            cliente_clock.close()
            
        except Exception as e:
            print(f"Erro ao comunicar com clock: {e}")



    def task_checker(self):
        '''
            Informa ao escalonador, quais tarefas já estão prontas
        '''

        # Sinaliza a inicialização do clock
        self.communication_clock()

        print("Clock Inicializado")

        # Variavel para diferenciar, quando o clock avança ou não.
        old_clock = None

        try:

            with open(self.task_file, 'r') as arq:
                linhas = arq.readlines()

            # Contador de linha
            i = 0
            while self.running:

                # Verifica se o servidor do emissor recebeu alguma mensagem
                self.check_messages()

                if old_clock != self.current_clock and i < len(linhas):
                    # Remove os espaços em branco do inicio e fim da linha
                    linha = linhas[i].strip()


                    if linha:
                        # Armazena os dados da linha em um lista .
                        linha_atual = linha.split(';')


                        if linha_atual[1] == self.current_clock:
                            thread = Thread(
                                    id = linha_atual[0],
                                    tempo_ingresso = int(linha_atual[1]),
                                    duracao_prevista = int(linha_atual[2]),
                                    prioridade = int(linha_atual[3])
                                )
                            print(f"Thread {thread.id} com tempo: {thread.tempo_ingresso} \
                                  entrando no tempo de clock {self.current_clock} \n")
                            
                            # Enviar thread para o escalonador
                            self.send_thread_to_scheduler(thread)

                            if i + 1 < len(linhas):
                                proxima_linha = linhas[i + 1].strip().split(';')
                                
                                if proxima_linha[1] == self.current_clock:
                                    i += 1  # Incrementar i antes de continuar
                                    continue
                            
                        else:                    
                            old_clock = self.current_clock
                            continue

                    old_clock = self.current_clock
                    i += 1

                # if i > len(linhas) - 1:
                #     print(f"Sequencia de tarefas prontas {ready_threads}")
                #     cliente_clock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                #     cliente_clock.settimeout(1.0)  # Timeout para conexão
                #     cliente_clock.connect((self.host, 4000))

                #     mensagem_clock = "ESCALONADOR: ENCERRADO"
                #     cliente_clock.send(mensagem_clock.encode())

                #     cliente_clock.close()
                #     break

                    if i == len(linhas):
                        self.communication_scheduler()


            self.close_server()
            print("EMISSOR ENCERRADO POR COMPLETO!")

                        
        
        except FileNotFoundError:
            print(f"Arquivo não encontrado: {self.task_file}")

        except Exception as e:
            print(f"Erro ao processar tarefas: {e}")


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
            print("Interrompido pelo usuário")
            self.close_server()

        except Exception as e:
            print(f"Erro geral: {e}")
            self.close_server()
            


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Erro: Você deve passar exatamente 2 argumentos!")

    arq_tarefas = sys.argv[1]

    # Portas de comunicação
    clock_port = 4000
    emitter_port = 4001
    scheduler_port = 4002

    # Host local
    host = "localhost"

    emissor = EMISSOR(host, clock_port, emitter_port, scheduler_port, arq_tarefas)

    emissor.start()