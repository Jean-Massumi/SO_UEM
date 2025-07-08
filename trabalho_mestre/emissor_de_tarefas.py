import time
import socket
import escalanador_de_tarefas
import clock

class EMISSOR:

    def __init__(self):
        self.porta: int = 4001
        self.running: bool = False



    def start_server(self):
        '''
            Inicia o servidor para receber mensagens do cliente
        '''
        
        # Criar socket
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        servidor.bind(("localhost", self.porta))
        servidor.listen(3)
        self.running = True

        while self.running:
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


    




