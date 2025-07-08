import sys
from multiprocessing import Process
from dataclasses import dataclass

import clock
import emissor_de_tarefas
import escalanador_de_tarefas

@dataclass
class Thread:
    id: str
    tempo: int
    duracao: int
    prioridade: int



if __name__  == "__main__":
    tarefas = sys.argv[1]
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


    # Criar Processos
    processo_clock = Process(target=...)
    processo_emissor = Process(target=...)
    processo_escalonador = Process(target=...)

    # # Iniciar Processos
    # processo_clock.start()
    # processo_emissor.start()
    # processo_escalonador.start()
    
