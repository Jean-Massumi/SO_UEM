import time
import socket
import threading

class CLOCK:
    
    def __init__(self, host: str, clock_port: int, emitter_port: int, scheduler_port: int):
        self.host: str = host                       # Host local
        self.clock_port: int = clock_port           # Porta de escuta/comunicação do clock
        self.emitter_port: int = emitter_port       # Porta de escuta/comunicação do emissor
        self.scheduler_port: int = scheduler_port   # Porta de escuta/comunicação do escalonador

        self.dados = None                           # Dado recebido através de algum processo 
        self.running: bool = False                  # Booleando para rodar o servidor
        self.current_clock: int = 0                 # Contador de clock


    def start_server(self):
        '''
            Inicia o servidor para receber mensagens do cliente
        '''
        
        # Criar socket
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        servidor.bind((self.host, self.clock_port))
        servidor.listen(3)
        self.running = True

        while self.running:
            try:
                # Aceitar conexão
                cliente, endereco = servidor.accept()
                print(f"Conexão de {endereco}")
                
                # Receber dados
                self.dados = cliente.recv(1024).decode('utf-8')
                                
                # Fechar conexão
                cliente.close()

                if self.dados == "FIM":
                    self.running = False
                    print("Servidor do Clock encerrado")
                    
            except Exception as e:
                print(f"Erro no servidor: {e}")
                break
        
        servidor.close()


    def clock_tick(self):
        '''
            Incrementa o *current_clock* em +1 a cada 100ms
        '''

        try:
            # Cliente do servidor do EMISSOR DE TAREFAS
            cliente_emissor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente_emissor.connect((self.host, self.emitter_port))  

            # Cliente do servidor do ESCALONADOR
            cliente_escalonador = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente_escalonador.connect((self.host, self.scheduler_port))  

            while True:
 
                # Mensagem Enviada ao EMISSOR DE TAREFAS
                mensagem_emissor = str(self.current_clock)
                cliente_emissor.send(mensagem_emissor.encode())

                # Tempo para o EMISSOR DE TAREFAS inserir as tarefas antes do 
                # ESCALONADOR tentar escalona-lás
                time.sleep(0.005)

                # Mensagem Enviada ao ESCALONADOR
                mensagem_escalonador = ...
                cliente_escalonador.send()

                # Incrementa o clock 
                self.current_clock += 1

                # Tempo de delay para o avanço da linha do tempo
                time.sleep(0.1)


                # Verifica se deve parar
                if self.dados == "FIM":
                    break

            cliente_emissor.close()
            cliente_escalonador.close()
            
        except Exception as e:
            print(f"Erro no clock_tick: {e}")


    def start(self):
        '''
            Inicia ambos os componentes (servidor e tick) em threads separadas
        '''

        # Thread para o servidor
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()

        # Thread para o clock
        clock_thread = threading.Thread(target=self.clock_tick)
        clock_thread.daemon = True
        clock_thread.start()

        # Aguarda a finalização das Threads
        server_thread.join()
        clock_thread.join()




