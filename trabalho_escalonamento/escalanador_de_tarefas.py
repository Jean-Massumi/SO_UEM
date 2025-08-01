from baseServer import BaseServer
from models import Thread
from algoritms import NonPreemptiveAlgorithm, RR_Algorithm, SRTF_Algorithm, PRIOp_Algorithm, PRIOd_Algorithm
from file_writer import FileWriter
from collections import deque
import sys
import json

class ESCALONADOR(BaseServer):
    '''
        Escalonador principal que implementa diferentes algoritmos de escalonamento de CPU.
    
        Esta classe gerencia a comunicação com outros componentes do sistema (Clock e Emissor)
        e executa algoritmos de escalonamento de threads em tempo real. Herda funcionalidades
        de servidor da BaseServer para comunicação via sockets.
    '''
    
    def __init__(self, host: str, clock_port: int, emitter_port: int, scheduler_port: int, algoritmo: str):
        '''
            Inicializa o escalonador com configurações de rede e algoritmo.
        '''

        # Inicializar classe pai com informações do servidor
        super().__init__(host, scheduler_port, "escalonador")
        
        # Portas de destino para comunicação
        self.clock_port: int = clock_port               # Porta de destino do CLOCK
        self.emitter_port: int = emitter_port           # Porta de destino do EMISSOR

        # Atributos específicos do escalonador
        self.emitter_completed = False                  # Flag indicando se o emissor terminou
        self.current_clock = None                       # Valor atual do clock recebido
        self.algoritmo = algoritmo                      # Algoritmo de escalonamento escolhido
        
        # Fila de threads prontas para execução
        self.ready_threads: deque[Thread] = deque()
        
        # Gerenciador de arquivos de saída
        self.file_writer = FileWriter(algoritmo)

        # Serve para verificar se foi emitido uma nova tarefa no algoritmo PRIOd
        self.new_emiiter = False

        # Determina a política de inserção de tarefas na fila de tarefas prontas
        self.algoritmo_de_insercao = None               

        # Algoritmos disponíveis
        self.algorithms = {
            "fcfs": NonPreemptiveAlgorithm(),
            "rr": RR_Algorithm(quantum=3),
            "sjf": NonPreemptiveAlgorithm(),
            "srtf": SRTF_Algorithm(),
            "prioc": NonPreemptiveAlgorithm(),
            "priop": PRIOp_Algorithm(),
            "priod": PRIOd_Algorithm()
        }


    def process_message(self, message):
        '''
            Processa mensagens recebidas do Clock e Emissor via socket.
            
            Implementa o protocolo de comunicação do sistema, interpretando
            dois tipos de mensagens:
            
            1. Mensagens JSON do Emissor:
                - NEW_THREAD: Nova thread para escalonamento
                - TAREFAS_FINALIZADAS: Sinalização de fim das emissões
            
            2. Mensagens String do Clock:
                - "CLOCK: <valor>": Atualização do tempo do sistema
        '''
        
        try:
            # Tentar interpretar como mensagem JSON do Emissor
            data = json.loads(message)
            
            if data.get('type') == 'NEW_THREAD':
                # Nova thread chegou - inserir na fila conforme algoritmo
                thread = Thread.from_dict(data['thread'])
                
                # Aplicar política de inserção baseada no algoritmo ativo
                if self.algoritmo_de_insercao == "duração":
                    self.insert_by_shortest_time(thread)

                elif self.algoritmo_de_insercao == "prioridade":
                    self.insert_by_priority(thread)

                else:
                    # FCFS e RR usam inserção simples (FIFO)
                    self.ready_threads.appendleft(thread)

                self.new_emiiter = True     # Sinalizar para aging no PRIOd
                
            elif data.get('type') == 'TAREFAS_FINALIZADAS':
                # Emissor terminou de enviar threads
                self.emitter_completed = True
                print(f"TAREFAS FINALIZADAS PELO EMISSOR recebido no clock {self.current_clock}! \n")  
                              
        except json.JSONDecodeError:
            # Mensagem não é JSON, processar como string
            if message.startswith("CLOCK: "):
                self.current_clock = message[7:]


    def communication_clock(self):
        '''
            Envia mensagem de encerramento para o processo clock 
        '''
        try:
            mensagem_clock = "ESCALONADOR: ENCERRADO"
            self.send_message(self.host, self.clock_port, mensagem_clock)
            
        except Exception as e:
            print(f"Erro ao comunicar com clock: {e}")


    def communication_emitter(self):
        '''
            Envia mensagem de encerramento para o processo emissor
        '''
        try:
            mensagem_emissor = "ESCALONADOR: ENCERRADO"
            self.send_message(self.host, self.emitter_port, mensagem_emissor)
            
        except Exception as e:
            print(f"Erro ao comunicar com emissor: {e}")


    def insert_by_shortest_time(self, tarefa: Thread):
        '''
            Insere thread mantendo fila ordenada por tempo restante (para SJF/SRTF).
            
            Estratégia: Fila ordenada DECRESCENTEMENTE por tempo restante.
            Estrutura: [maior_tempo, ..., menor_tempo]
            Operação: pop() sempre retira o menor tempo (final da fila)
            
            Esta organização permite:
            - pop() em O(1) para obter thread mais curta
            - append() em O(1) para threads muito longas ou muito curtas
            - Inserção no meio apenas quando necessário
        '''

        # Fila vazia
        if not self.ready_threads:
            self.ready_threads.appendleft(tarefa)
            return

        duracao_nova = tarefa.duracao_prevista.tempo_restante

        # Maior que o primeiro (vai para o início)
        if duracao_nova >= self.ready_threads[0].duracao_prevista.tempo_restante:
            self.ready_threads.appendleft(tarefa)
        
        # Menor que o último (vai para o final)
        elif duracao_nova < self.ready_threads[-1].duracao_prevista.tempo_restante:
            self.ready_threads.append(tarefa)

        # Inserção no meio
        else:
            # Procura da direita para esquerda
            for i in range(len(self.ready_threads) - 1, -1, -1):
                if self.ready_threads[i].duracao_prevista.tempo_restante > duracao_nova:
                    temp_list = list(self.ready_threads)
                    temp_list.insert(i + 1, tarefa)
                    self.ready_threads = deque(temp_list)
                    return        

                
    def insert_by_priority(self, tarefa: Thread):
        '''
            Política de inserção para algoritmo PRIOc e PRIOp.
            
            Mantém a fila de threads prontas ordenada em ordem DECRESCENTE de prioridade.
            A thread com menor prioridade será sempre a última da fila (ready_threads[-1]),
            permitindo que pop() retire sempre a thread mais prioridade primeiro.

            Exemplo: [3, 3, 2, 1] - pop() retira 1 (maior prioridade)

            Complexidade: O(n) no pior caso, O(1) nos casos otimizados
        '''

        # Fila vazia
        if not self.ready_threads:
            self.ready_threads.appendleft(tarefa)
            return

        nova_prioridade = tarefa.prioridade.prio_d

        # Maior que o primeiro (vai para o início)
        if nova_prioridade >= self.ready_threads[0].prioridade.prio_d:
            self.ready_threads.appendleft(tarefa)
        
        # Menor que o último (vai para o final)
        elif nova_prioridade < self.ready_threads[-1].prioridade.prio_d:
            self.ready_threads.append(tarefa)

        # Inserção no meio
        else:
            # Procura da direita para esquerda
            for i in range(len(self.ready_threads) - 1, -1, -1):
                if self.ready_threads[i].prioridade.prio_d > nova_prioridade:
                    prio_list = list(self.ready_threads)
                    prio_list.insert(i + 1, tarefa)
                    self.ready_threads = deque(prio_list)           
                    return
                

    def increment_priority(self):
        '''
            Implementa aging para algoritmo PRIOd - evita starvation.
    
            Decrementa a prioridade dinâmica (prio_d) de todas as threads na fila,
            melhorando suas chances de execução. Chamado periodicamente pelo
            algoritmo PRIOd quando new_emitter=True.
        '''

        for tarefas in self.ready_threads:
            tarefas.prioridade.prio_d -= 1


    def start(self):
        '''
            Inicia o escalonador e executa o algoritmo selecionado.
    
            Fluxo de execução:
            1. Cria servidor socket para comunicação
            2. Configura política de inserção baseada no algoritmo
            3. Executa o algoritmo de escalonamento escolhido

            Configurações de Política:
            - SJF/SRTF: Ordenação por "duração" 
            - PRIOc/PRIOp/PRIOd: Ordenação por "prioridade"
            - FCFS/RR: Sem ordenação especial (FIFO)
        '''

        try:
            # Cria o servidor
            self.create_server()

            # Configurar política de inserção conforme algoritmo
            if self.algoritmo in ["sjf", "srtf"]:
                self.algoritmo_de_insercao = "duração"

            elif self.algoritmo in ["prioc", "priop", "priod"]:
                self.algoritmo_de_insercao = "prioridade"
                
            # FCFS e RR não precisam de política especial

            # Executar algoritmo
            if self.algoritmo in self.algorithms:
                self.algorithms[self.algoritmo].execute(self)

            else:
                print("Algoritmo inválido!")
                print("Algoritmos disponíveis: fcfs, rr, sjf, strf, prioc")
                self.close_server()
            
        except KeyboardInterrupt:
            print("Interrompido pelo usuário")
            self.close_server()

        except Exception as e:
            print(f"Erro geral: {e}")
            self.close_server()


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Erro: Você deve passar exatamente 2 argumentos!")
        print("Uso: python3 escalonador_de_tarefas.py <algoritmo>!")

    algoritmo = sys.argv[1]

    # Portas de comunicação
    clock_port = 4000
    emitter_port = 4001
    scheduler_port = 4002

    # Host local
    host = "localhost"

    escalonador = ESCALONADOR(host, clock_port, emitter_port, scheduler_port, algoritmo)

    escalonador.start()
