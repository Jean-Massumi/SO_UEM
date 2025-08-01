import time
from baseServer import BaseServer

class CLOCK(BaseServer):
    '''
        Classe responsável por gerenciar o clock da CPU.
    
        O clock atua como coordenador temporal, enviando pulsos sincronizados
        para o emissor de tarefas e o escalonador a cada 100ms.
    '''
    
    def __init__(self, host: str, clock_port: int, emitter_port: int, scheduler_port: int):

        # Inicializar classe pai com informações do servidor
        super().__init__(host, clock_port, "clock")

        # Portas de destino para comunicação
        self.emitter_port: int = emitter_port       # Porta de destino do EMISSOR
        self.scheduler_port: int = scheduler_port   # Porta de destino do ESCALONADOR

        # Atributos específicos do clock
        self.current_clock: int = 0                 # Contador de clock (ticks)
        self.clock_started = False                  # Flag de controle: clock ativo/inativo
        self.running = True                         # Flag de controle: sistema rodando/parado


    def process_message(self, message):
        '''
            Processa mensagens específicas do clock.
            
            Processa os seguintes comandos:
            - "EMISSOR: INICIAR CLOCK": Ativa o clock (clock_started = True)
            - "ESCALONADOR: ENCERRADO": Para o sistema (running = False)
        '''
        
        print(f"Mensagem recebida: {message}")

        # Processar mensagem
        if message == "EMISSOR: INICIAR CLOCK":
            self.clock_started = True
            print("CLOCK INICIADO! \n")

        elif message == "ESCALONADOR: ENCERRADO":
            self.running = False


    def communication_emitter(self):
        '''
            Envia pulso de clock para o emissor de tarefas.
            
            Transmite o valor atual do clock para o emissor, permitindo
            que ele sincronize a geração de tarefas com o tempo do sistema.
            
            Formato da mensagem: "CLOCK: {valor_atual}"      
        '''
        
        message = f"CLOCK: {self.current_clock}"
        self.send_message(self.host, self.emitter_port, message)


    def communication_scheduler(self):
        '''
            Envia pulso de clock para o escalonador.
            
            Transmite o valor atual do clock para o escalonador, permitindo
            que ele execute o algoritmo de escalonamento sincronizado com
            o tempo do sistema.
            
            Formato da mensagem: "CLOCK: {valor_atual}"
        '''

        message = f"CLOCK: {self.current_clock}"
        self.send_message(self.host, self.scheduler_port, message)


    def clock_tick(self):
        '''
            Loop principal do clock - gera pulsos a cada 100ms.
            
            Executa o ciclo temporal do sistema:
            1. Verifica se o clock foi iniciado
            2. Envia pulso para o emissor de tarefas
            3. Aguarda 5ms (tempo para inserção de tarefas)
            4. Envia pulso para o escalonador
            5. Incrementa o contador de clock
            6. Aguarda 100ms (próximo ciclo)
            7. Verifica mensagens de controle
            
            O loop continua até que running seja False.      
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
                    self.communication_scheduler()

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
            Inicia o sistema de clock.
            
            Método principal que:
            1. Cria o servidor
            2. Inicia o loop de clock_tick()
            3. Trata interrupções (Ctrl+C) de forma segura
            4. Garante encerramento limpo do servidor
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