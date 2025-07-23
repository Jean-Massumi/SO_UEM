from baseServer import BaseServer
import sys
import time

class EMISSOR(BaseServer):
    '''
        Responsável pela emissão de tarefas
    
        O emissor lê tarefas de um arquivo e as envia para o escalonador
        no momento apropriado, baseado no clock.
    '''

    def __init__(self, host: str, clock_port: int, emitter_port: int, scheduler_port: int, arquivo):

        # Inicializar classe pai com informações do servidor
        super().__init__(host, emitter_port, "emissor")

        # Portas de destino para comunicação
        self.clock_port: int = clock_port               # Porta de destino do CLOCK
        self.scheduler_port: int = scheduler_port       # Porta de destino do ESCALONADOR

        # Atributos específicos do emissor
        self.task_file = arquivo                        # Arquivo fonte das tarefas
        self.current_clock = None                       # Valor atual do clock recebido
        self.running = True  


    def process_message(self, message):
        '''
            Processa mensagens específicas do emissor.
            
            Processa os seguintes tipos:
            - "CLOCK: {valor}": Atualiza o clock atual do sistema
            - "ESCALONADOR: ENCERRADO": Para o sistema (running = False)
        '''
        
        print(f"Mensagem recebida: {message}")    

        # Processar mensagem
        if message == "ESCALONADOR: ENCERRADO":
            self.running = False

        elif message.startswith("CLOCK: "):
            self.current_clock = message[7:]


    def send_thread_to_scheduler(self, thread_info: list):
        '''
            Envia uma thread para o escalonador via socket.
            
            Recebe uma lista com os dados da thread e cria o dicionário
            para envio via JSON ao escalonador.
        '''
        
        try:
            # Print informativo
            print(f"Thread {thread_info[0]} com tempo: {thread_info[1]} entrando no tempo de clock {self.current_clock} \n")
            
            # Criar dicionário diretamente da lista
            thread_data = {
                'type': 'NEW_THREAD',
                'thread': {
                    'id': thread_info[0],
                    'tempo_ingresso': int(thread_info[1]),
                    'duracao_prevista': int(thread_info[2]),
                    'prioridade': int(thread_info[3])
                }
            }
            
            self.send_json_message(self.host, self.scheduler_port, thread_data)
            
        except Exception as e:
            print(f"Erro ao enviar thread para escalonador: {e}")


    def communication_scheduler(self):
        '''
            Notifica o escalonador sobre finalização de tarefas.
            
            Envia mensagem JSON do tipo 'TAREFAS_FINALIZADAS' para informar
            que todas as tarefas foram emitidas e o sistema pode encerrar.
        '''

        try:
            # Usar método herdado da BaseServer para envio JSON
            mensagem_data = {'type': 'TAREFAS_FINALIZADAS'}
            self.send_json_message(self.host, self.scheduler_port, mensagem_data)
            
        except Exception as e:
            print(f"Erro ao comunicar com escalonador: {e}")


    def communication_clock(self):
        '''
            Envia comando para iniciar o clock do sistema.
            
            Comunica ao clock que o emissor está pronto e o sistema
            pode começar a gerar pulsos temporais.      
        '''
        
        try:
            # Usar método herdado da BaseServer
            mensagem_clock = "EMISSOR: INICIAR CLOCK"
            self.send_message(self.host, self.clock_port, mensagem_clock)
            
        except Exception as e:
            print(f"Erro ao comunicar com clock: {e}")


    def _load_and_organize_tasks(self):
        '''
            Carrega o arquivo de tarefas e organiza por tempo de ingresso.
        '''

        tarefas_por_tempo = {}
        
        with open(self.task_file, 'r') as arq:
            for linha_num, linha in enumerate(arq, 1):
                linha = linha.strip()
                
                if not linha:  # Ignora linhas vazias
                    continue
                    
                try:
                    dados_tarefa = linha.split(';')
                    
                    if len(dados_tarefa) != 4:
                        print(f"Aviso: Linha {linha_num} com formato inválido: {linha}")
                        continue
                    
                    tempo_ingresso = dados_tarefa[1]
                    
                    # Organiza tarefas por tempo de ingresso
                    if tempo_ingresso not in tarefas_por_tempo:
                        tarefas_por_tempo[tempo_ingresso] = []
                        
                    tarefas_por_tempo[tempo_ingresso].append(dados_tarefa)
                    
                except Exception as e:
                    print(f"Erro ao processar linha {linha_num}: {e}")
                    continue
        
        return tarefas_por_tempo


    def _process_tasks_for_current_time(self, tarefas):
        '''
            Processa todas as tarefas para o tempo atual do clock.
            
            *tarefas* (list): Lista de tarefas a serem processadas
        '''
        
        print(f"Processando {len(tarefas)} tarefas para o tempo {self.current_clock}")
        
        for tarefa in tarefas:
            self.send_thread_to_scheduler(tarefa)


    def task_checker(self):
        '''
            Loop principal que processa e emite tarefas baseado no clock.
            
            Executa o seguinte algoritmo:
            1. Inicializa o clock do sistema
            2. Lê arquivo de tarefas e organiza por tempo de ingresso
            3. Para cada pulso do clock, verifica se há tarefas a emitir
            4. Envia tarefas prontas para o escalonador
            5. Notifica finalização quando todas as tarefas foram emitidas
            
            Formato do arquivo de tarefas:
            id;tempo_ingresso;duracao_prevista;prioridade        
        '''

        # Sinaliza a inicialização do clock
        self.communication_clock()

        try:
            # Carrega e organiza as tarefas por tempo de ingresso
            tarefas_por_tempo = self._load_and_organize_tasks()
            
            # Controle de estado
            last_processed_clock = None
            tasks_finished = False

            while self.running:
                # Verifica se o servidor do emissor recebeu alguma mensagem
                self.check_messages()

                # Processa apenas quando o clock avança
                if self.current_clock is not None and self.current_clock != last_processed_clock:
                    
                    # Processa tarefas do tempo atual
                    if self.current_clock in tarefas_por_tempo:
                        self._process_tasks_for_current_time(tarefas_por_tempo[self.current_clock])
                        del tarefas_por_tempo[self.current_clock]  # Remove tarefas já processadas
                    
                    # Verifica se todas as tarefas foram processadas
                    if not tasks_finished and len(tarefas_por_tempo) == 0:
                        print("TODAS AS TAREFAS FORAM EMITIDAS!\n")
                        tasks_finished = True
                        
                        # Pequeno delay para garantir que o escalonador processe o clock atual
                        time.sleep(0.05)  # 50ms de delay

                        # Envia a mensagem no mesmo clock que terminou de emitir
                        self.communication_scheduler()
                                        
                    last_processed_clock = self.current_clock

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