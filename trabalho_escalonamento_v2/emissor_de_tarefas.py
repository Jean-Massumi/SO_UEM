import socket
from dataclasses import dataclass
import sys
import json

@dataclass
class Thread:
    '''
        Representa uma thread/tarefa no sistema de escalonamento.
    '''

    id: str
    tempo_ingresso: int
    duracao_prevista: int
    prioridade: int

    def to_dict(self):
        '''
            Converte a thread para formato dicionário.
        '''

        return {
            'id': self.id,
            'tempo_ingresso': self.tempo_ingresso,
            'duracao_prevista': self.duracao_prevista,
            'prioridade': self.prioridade
        }


class EMISSOR:
    '''
        Responsável pela emissão de tarefas
    
        O emissor lê tarefas de um arquivo e as envia para o escalonador
        no momento apropriado, baseado no clock.
    '''

    def __init__(self, host: str, clock_port: int, emitter_port: int, scheduler_port: int, arquivo):

        self.host: str = host                           # Endereço IP do servidor
        self.emitter_port: int = emitter_port           # Porta do servidor do EMISSOR
        self.clock_port: int = clock_port               # Porta de destino do CLOCK
        self.scheduler_port: int = scheduler_port       # Porta de destino do ESCALONADOR
        self.servidor = None                            # Socket Servidor 

        self.task_file = arquivo                        # Arquivo fonte das tarefas
        self.current_clock = None                       # Valor atual do clock recebido
        self.running = True                             # Flag de controle: sistema rodando/parado



    def create_server(self):
        '''
            Cria e configura o servidor do emissor.
            
            Estabelece um socket servidor que escuta na porta especificada,
            aguardando pulsos do clock e comandos do escalonador.
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
            Escuta e processa mensagens recebidas.
            
            Aceita conexões não-bloqueantes e processa os seguintes tipos:
            - "CLOCK: {valor}": Atualiza o clock atual do sistema
            - "ESCALONADOR: ENCERRADO": Para o sistema (running = False)        
        '''
       
        try:
            # Aceitar conexão
            cliente, endereco = self.servidor.accept()
            
            # Receber dados
            message = cliente.recv(1024).decode('utf-8')
            print(f"Mensagem recebida: {message}")    

            # Processar mensagem
            if message == "ESCALONADOR: ENCERRADO":
                self.running = False

            elif message.startswith("CLOCK: "):
                self.current_clock = message[7:]
            
            # Fechar conexão
            cliente.close() 

        except socket.timeout:
            # Normal - não havia mensagem
            pass
                
        except Exception as e:
            print(f"Erro no servidor: {e}")



    def close_server(self):
        '''
            Encerra o servidor do emissor de forma segura.
            
            Fecha o socket servidor, liberando recursos e a porta utilizada.
            Chamado automaticamente ao finalizar o sistema.        
        '''

        print("\nEncerrando o servidor do emissor!")

        if self.servidor:
            self.servidor.close()

        print("Servidor do emissor encerrado com sucesso!\n")



    def send_thread_to_scheduler(self, thread: Thread):
        '''
            Envia uma thread para o escalonador via socket.
            
            Serializa a thread em formato JSON e a envia para o escalonador
            com tipo 'NEW_THREAD' para identificação do protocolo.    
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
            Notifica o escalonador sobre finalização de tarefas.
            
            Envia mensagem JSON do tipo 'TAREFAS_FINALIZADAS' para informar
            que todas as tarefas foram emitidas e o sistema pode encerrar.
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
            Envia comando para iniciar o clock do sistema.
            
            Comunica ao clock que o emissor está pronto e o sistema
            pode começar a gerar pulsos temporais.      
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
            Loop principal que processa e emite tarefas baseado no clock.
            
            Executa o seguinte algoritmo:
            1. Inicializa o clock do sistema
            2. Lê arquivo de tarefas linha por linha
            3. Para cada pulso do clock, verifica se há tarefas a emitir
            4. Envia tarefas prontas para o escalonador
            5. Notifica finalização quando todas as tarefas foram emitidas
            
            Formato do arquivo de tarefas:
            id;tempo_ingresso;duracao_prevista;prioridade        
        '''

        # Sinaliza a inicialização do clock
        self.communication_clock()

        # Variável para detectar mudanças no clock
        old_clock = None

        try:

            with open(self.task_file, 'r') as arq:
                linhas = arq.readlines()

            # Índice da linha atual sendo processada
            i = 0
            while self.running:

                # Verifica se o servidor do emissor recebeu alguma mensagem
                self.check_messages()

                # Processa apenas qunado o clock avança
                if old_clock != self.current_clock and i < len(linhas):
                    # Remove os espaços em branco do inicio e fim da linha
                    linha = linhas[i].strip()

                    if linha:
                        # Armazena os dados da linha em um lista .
                        linha_atual = linha.split(';')

                        # Verifica se a tarefa deve ser emitida neste clock
                        if linha_atual[1] == self.current_clock:
                            thread = Thread(
                                    linha_atual[0],         # ID
                                    int(linha_atual[1]),    # Tempo de ingresso
                                    int(linha_atual[2]),    # Duração prevista
                                    int(linha_atual[3])     # Prioridade
                                )
                            print(f"Thread {thread.id} com tempo: {thread.tempo_ingresso} entrando no tempo de clock {self.current_clock} \n")
                            
                            # Enviar thread para o escalonador
                            self.send_thread_to_scheduler(thread)

                            # Verifica se a próxima linha também deve ser emitida no mesmo clock
                            if i + 1 < len(linhas):
                                proxima_linha = linhas[i + 1].strip().split(';')
                                
                                if proxima_linha[1] == self.current_clock:
                                    i += 1
                                    continue
                            
                        else:                    
                            old_clock = self.current_clock
                            continue

                    old_clock = self.current_clock
                    i += 1

                elif i == len(linhas):
                    self.communication_scheduler()
                    print("TODAS AS TAREDAS FORAM EMITIDAS! \n")
                    i += 1

            self.close_server()
            print("EMISSOR ENCERRADO POR COMPLETO!")

                        
        
        except FileNotFoundError:
            print(f"Arquivo não encontrado: {self.task_file}")

        except Exception as e:
            print(f"Erro ao processar tarefas: {e}")


    def start(self):
        '''
            Inicia o emissor de tarefas.
            
            Método principal que:
            1. Cria o servidor
            2. Inicia o processamento de tarefas
            3. Trata interrupções (Ctrl+C) de forma segura
            4. Garante encerramento limpo do servidor        
        '''
        
        try:
            # Cria o servidor
            self.create_server()

            # Inicia o processamento
            self.task_checker()
            
        except KeyboardInterrupt:
            print("Interrompido pelo usuário")
            self.running = False
            self.close_server()

        except Exception as e:
            print(f"Erro geral: {e}")
            self.close_server()
            


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Erro: Você deve passar exatamente 2 argumentos!")
        print("Uso: python3 emissor_de_tarefas.py <arquivo_tarefas>")

    arq_tarefas = sys.argv[1]

    # Portas de comunicação
    clock_port = 4000
    emitter_port = 4001
    scheduler_port = 4002

    # Host local
    host = "localhost"

    emissor = EMISSOR(host, clock_port, emitter_port, scheduler_port, arq_tarefas)

    emissor.start()