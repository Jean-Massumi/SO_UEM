import time
import socket
import emissor_de_tarefas
import escalanador_de_tarefas


class CLOCK:
    
    def __init__(self):
        self.current_clock: int = 0    
        self.porta: int = 4000


    def start_server(self):
        '''
            Inicia o servidor para receber mensagens do cliente
        '''
        
        # Criar socket
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        servidor.bind(("localhost", self.porta))
        servidor.listen(3)

        while True:
            # Aceitar conexão
            cliente, endereco = servidor.accept()
            print(f"Conexão de {endereco}")
            
            # Receber dados
            dados = cliente.recv(1024).decode('utf-8')
            print(f"Mensagem recebida: {dados}")
            
            # Enviar resposta
            resposta = f"Servidor recebeu: {dados}"
            cliente.send(resposta.encode('utf-8'))
            
            # Fechar conexão
            cliente.close()


    def clock_tick(self):
        '''
            Incrementa o *current_clock* em +1 a cada 100ms
        '''

        cliente_emissor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente_emissor.connect(('localhost', 4001))    

        while True:
            # Incrementa o clock
            self.current_clock += 1

            # Tempo de delay para o avanço da linha do tempo
            time.sleep(0.1)

            # Mensagem Envia
            cliente_emissor.send()
            time.sleep
            break

        cliente_emissor.close()



def comunicacao() -> None:
    # Criar socket
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    servidor.bind(("localhost", 4000))
    servidor.listen(3)





