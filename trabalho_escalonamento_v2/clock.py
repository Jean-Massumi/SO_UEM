import time
import socket

class CLOCK:
    
    def __init__(self, host: str, clock_port: int, emitter_port: int, scheduler_port: int):
        self.host: str = host                       # Host do computador
        self.clock_port: int = clock_port           # Porta de escuta/comunicação do clock
        self.emitter_port: int = emitter_port       # Porta de escuta/comunicação do emissor
        self.scheduler_port: int = scheduler_port   # Porta de escuta/comunicação do escalonador

        self.servidor = None

        self.current_clock: int = 0                 # Contador de clock
        self.clock_started = False                  # Flag para iniciar o clock
        self.running = True                         # Flag para iniciar os ticks do clock


    def create_server(self):
        '''
            Cria e configura o servidor TCP do clock para receber conexões
            de outros processos (emissor e escalonador) na porta especificada
        '''
        
        print("Criando o servidor do clock!")

        # Criar socket
        self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.servidor.bind((self.host, self.clock_port))
        self.servidor.listen(3)
        self.servidor.settimeout(0.1)  # Timeout CURTO para não bloquear muito

        print("Servidor do clock criado com sucesso! \n")


    def check_messages(self):
        '''
            Escuta e processa mensagens recebidas de outros processos. 
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
            if message == "EMISSOR: INICIAR CLOCK":
                self.clock_started = True
                print("Clock iniciado! \n")

            elif message == "ESCALONADOR: ENCERRADO":
                self.running = False
                print("Comando FIM recebido! \n")
                            
        except socket.timeout:
            # Timeout é normal, não é erro
            pass
                
        except Exception as e:
            print(f"Erro no servidor: {e}")
        

    def close_server(self):
        '''
            Fecha o servidor do clock
        '''
        print("Encerrando o servidor do clock!")

        if self.servidor:
            self.servidor.close()

        print("Servidor do clock encerrado com sucesso! \n")


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
            mensagem_emissor = "CLOCK: " + str(self.current_clock)
            cliente_emissor.send(mensagem_emissor.encode())

            cliente_emissor.close()
            
        except ConnectionRefusedError:
            print(f"Emissor não está rodando na porta {self.emitter_port}")
        except Exception as e:
            print(f"Erro ao comunicar com emissor: {e}")


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
            mensagem_escalonador = "CLOCK: " +str(self.current_clock)
            cliente_escalonador.send(mensagem_escalonador.encode())

            cliente_escalonador.close()
            
        except Exception as e:
            print(f"Erro ao comunicar com escalonador: {e}")



    def clock_tick(self):
        '''
            Incrementa o *current_clock* em +1 a cada 100ms
        '''

        try:

            while self.running:

                # Se clock iniciado, faz o trabalho
                if self.clock_started:                    
                    print(f"Clock atual: {self.current_clock}")

                    # Comunicação com o Emissor
                    self.communication_emitter()

                    # Tempo para o EMISSOR DE TAREFAS inserir as tarefas antes do 
                    # ESCALONADOR tentar escalona-lás
                    time.sleep(0.005)

                    # Comunicação com o Escalonador
                    #self.communication_scheduler()

                    # Incrementa o clock 
                    self.current_clock += 1

                    # Tempo de delay para o avanço da linha do tempo
                    time.sleep(0.1)

                else:
                    # Evita uso excessivo de CPU
                    time.sleep(0.01)
                    
                # Verifica mensagens RAPIDAMENTE
                self.check_messages()

            self.close_server()
            print("CLOCK ENCERRADO POR COMPLETO!")

        except Exception as e:
            print(f"Erro no clock_tick: {e}")
            self.close_server()


    def start(self):
        '''
            Inicia o clock
        '''
        try:
            # Cria o servidor
            self.create_server()

            # Começa o clock
            self.clock_tick()
            
        except KeyboardInterrupt:
            print("Interrompido pelo usuário")
            self.running = False
            self.close_server()

        except Exception as e:
            print(f"Erro geral: {e}")
            self.close_server()



if __name__ == "__main__":

    # Portas de comunicação
    clock_port = 4000
    emitter_port = 4001
    scheduler_port = 4002

    # Host local
    host = "localhost"

    clock = CLOCK(host, clock_port, emitter_port, scheduler_port)
    clock.start()

