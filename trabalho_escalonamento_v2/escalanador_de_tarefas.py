from baseServer import BaseServer
from models import Thread
from algoritms import NonPreemptiveAlgorithm, RR_Algorithm
from file_writer import FileWriter
from collections import deque
import sys
import json

class ESCALONADOR(BaseServer):
    '''
        Classe principal do escalonador que implementa diferentes algoritmos
        de escalonamento de threads. Herda funcionalidade de servidor da BaseServer.
    '''
    
    def __init__(self, host: str, clock_port: int, emitter_port: int, scheduler_port: int, algoritmo: str):
        
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
        
        # Determina a política de inserção de tarefas na fila de tarefas prontas
        self.algoritmo_de_insercao = None               

        # Gerenciador de arquivos
        self.file_writer = FileWriter(algoritmo)
        
        # Algoritmos disponíveis
        self.algorithms = {
            "fcfs": NonPreemptiveAlgorithm(),
            "rr": RR_Algorithm(quantum=3),
            "sjf": NonPreemptiveAlgorithm(),
            # Adicionar outros conforme implementar
        }


    def process_message(self, message):
        '''
            Implementação do método abstrato da BaseServer.
            Processa mensagens recebidas do clock e emissor.
            
            Args:
                message (str): Mensagem recebida do cliente
        '''
        
        try:
            # Tentar parsear como JSON
            data = json.loads(message)
            
            if data.get('type') == 'NEW_THREAD':
                # Receber nova thread do emissor
                thread = Thread.from_dict(data['thread'])
                
                if self.algoritmo_de_insercao == "duração":
                    self.insert_by_shortest_time(thread)

                else:
                    # fila de tarefas prontas sempre está em ordem crescente do tempo de ingresso das tarefas na fila
                    self.ready_threads.appendleft(thread)
                
            elif data.get('type') == 'TAREFAS_FINALIZADAS':
                self.emitter_completed = True
                print("TAREFAS FINALIZADAS PELO EMISSOR recebido! \n ")
                
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
            Política de inserção para algoritmo SJF (Shortest Job First).
            
            Mantém a fila de threads prontas ordenada em ordem DECRESCENTE de duração restante.
            A thread com menor tempo será sempre a última da fila (ready_threads[-1]),
            permitindo que pop() retire sempre a thread mais curta primeiro.

            Exemplo: [11, 5, 3, 1] - pop() retira 1 (menor tempo)

            Complexidade: O(n) no pior caso, O(1) nos casos otimizados
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
        elif duracao_nova <= self.ready_threads[-1].duracao_prevista.tempo_restante:
            self.ready_threads.append(tarefa)

        # Inserção no meio
        else:
            # Procura da direita para esquerda
            for i in range(len(self.ready_threads) - 1, -1, -1):
                if self.ready_threads[i].duracao_prevista.tempo_restante >= duracao_nova:
                    temp_list = list(self.ready_threads)
                    temp_list.insert(i + 1, tarefa)
                    self.ready_threads = deque(temp_list)
                    return        


    def start(self):
        '''
            Inicia o escalonador e executa o algoritmo selecionado
        '''

        try:
            # Cria o servidor
            self.create_server()

            # Configurar política de inserção se necessário
            if self.algoritmo == "sjf":
                self.algoritmo_de_insercao = "duração"

            # Executar algoritmo
            if self.algoritmo in self.algorithms:
                self.algorithms[self.algoritmo].execute(self)

            else:
                print("Algoritmo inválido!")
                print("Algoritmos disponíveis: fcfs, rr, sjf")
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


















