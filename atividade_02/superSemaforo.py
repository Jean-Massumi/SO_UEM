import threading
import random
import time

arquivo_saida = "arquivo.txt"
total_linhas = 5
semaforo = threading.Semaphore(1)

def escrever_arquivo(i):
    time.sleep(random.uniform(0, 0.1))
    semaforo.acquire()
    
    for j in range(total_linhas):

        linha = f"[thread {i}] linha {j}\n"

        for caractere in linha:
            with open(arquivo_saida, "a") as f:
                f.write(caractere)

    semaforo.release()


# Função Principal
if __name__ == "__main__":
    
    # Limpar o arquivo antes de iniciar
    with open(arquivo_saida, "w") as f:
        f.write("")

    n_threads = 8
    threads = []
    
    for n in range(n_threads):
        t = threading.Thread(target=escrever_arquivo, args=(n,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
        

