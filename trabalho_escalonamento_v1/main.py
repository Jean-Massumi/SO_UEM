import sys
from multiprocessing import Process
from collections import deque

from clock import CLOCK
from emissor_de_tarefas import EMISSOR
from escalanador_de_tarefas import ESCALONADOR

host = "localhost"          # Host do computador
clock_port = 4000           # Porta de escuta do clock
emitter_port = 4001         # Porta de escuta do emissor
scheduler_port = 4002       # Porta de escuta do escalonador

ready_task = deque()






if __name__  == "__main__":

    if len(sys.argv) != 3:
        print("Erro: Você deve passar exatamente 3 argumentos!")

    arquivo_tarefas = sys.argv[1]
    algoritmo = sys.argv[2]


    if algoritmo == "fcfs":
        print("fcfs")

    elif algoritmo == "rr":
        print("rr")

    elif algoritmo == "sjf":
        print("sjf")

    elif algoritmo == "srtf":
        print("srtf")

    elif algoritmo == "prioc":
        print("prioc")

    elif algoritmo == "priop":
        print("priop")

    elif algoritmo == "priod":
        print("priod")

    else:
        print("Argumento de algoritmo inválido!")

    # Instância de cada estrutura dos arquivos (clock.py, emissor_de_tarefas.py
    # e escalonador_de_tarefas.py)
    clock = CLOCK(host, clock_port, emitter_port, scheduler_port)
    sender = EMISSOR(host, emitter_port, scheduler_port, threads_list)
    scheduler = ESCALONADOR(host, scheduler_port, clock_port, emitter_port)


    # Criar Processos
    processo_emissor = Process(target=...)
    processo_clock = Process(target=...)
    processo_escalonador = Process(target=...)

    # # Iniciar Processos
    # processo_clock.start()
    # processo_emissor.start()
    # processo_escalonador.start()
    
