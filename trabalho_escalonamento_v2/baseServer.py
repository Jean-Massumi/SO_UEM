import socket
import json
from abc import ABC, abstractmethod

class BaseServer(ABC):
    """
    Classe base para servidores com funcionalidade comum de socket.
    
    Fornece implementação padrão para criação, gerenciamento e encerramento
    de servidores, deixando apenas o processamento de mensagens específico
    para as classes filhas implementarem.
    """
    
    def __init__(self, host, port, server_name):
        """
        Inicializa o servidor base.
        
        Args:
            host (str): Endereço IP do servidor
            port (int): Porta do servidor
            server_name (str): Nome do servidor para logs
        """
        self.host = host
        self.port = port
        self.server_name = server_name
        self.servidor = None
        
    
    def create_server(self):
        """
        Cria e configura o servidor.
        
        Estabelece um socket servidor que escuta na porta especificada,
        configurado com timeout curto para não bloquear o loop principal.
        """
        
        print(f"Criando o servidor do {self.server_name}!")

        # Criar socket
        self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servidor.bind((self.host, self.port))
        self.servidor.listen(3)
        self.servidor.settimeout(0.1)  # Timeout CURTO para não bloquear muito

        print(f"Servidor do {self.server_name} criado com sucesso! \n")
    

    def check_messages(self):
        """
        Escuta e processa mensagens recebidas.
        
        Aceita conexões não-bloqueantes e delega o processamento específico
        para o método process_message() implementado pelas classes filhas.
        """
       
        try:
            # Aceitar conexão
            cliente, endereco = self.servidor.accept()
            
            # Receber dados
            message = cliente.recv(1024).decode('utf-8')
            
            # Processar mensagem usando método específico da classe filha
            self.process_message(message)
            
            # Fechar conexão
            cliente.close()

        except socket.timeout:
            # Normal - não havia mensagem
            pass
                
        except Exception as e:
            print(f"Erro no servidor: {e}")
     

    @abstractmethod
    def process_message(self, message):
        """
        Processa mensagem recebida - deve ser implementado pelas classes filhas.
        
        Args:
            message (str): Mensagem recebida do cliente
        """
        pass
    

    def close_server(self):
        """
        Encerra o servidor de forma segura.
        
        Fecha o socket servidor, liberando recursos e a porta utilizada.
        Chamado automaticamente ao finalizar o sistema.
        """

        print(f"\nEncerrando o servidor do {self.server_name}!")

        if self.servidor:
            self.servidor.close()

        print(f"Servidor do {self.server_name} encerrado com sucesso! \n")
    
    
    def send_message(self, target_host, target_port, message):
        """
        Envia mensagem para outro servidor.
        
        Args:
            target_host (str): IP do servidor destino
            target_port (int): Porta do servidor destino  
            message (str): Mensagem a ser enviada
        """
        try:
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente.settimeout(1.0)  # Timeout para conexão
            cliente.connect((target_host, target_port))
            cliente.send(message.encode('utf-8'))
            cliente.close()
            
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
    
    
    def send_json_message(self, target_host, target_port, data):
        """
        Envia mensagem JSON para outro servidor.
        
        Args:
            target_host (str): IP do servidor destino
            target_port (int): Porta do servidor destino
            data (dict): Dados a serem enviados como JSON
        """
        try:
            message = json.dumps(data)
            self.send_message(target_host, target_port, message)
        except Exception as e:
            print(f"Erro ao enviar mensagem JSON: {e}")