import threading
import random
import time

arquivo_saida = "arquivo.txt"
total_linhas = 5
semaforo = threading.Semaphore(1)

def escrever_arquivo(i):
    for j in range(total_linhas):
        time.sleep(random.uniform(0, 0.1))

        linha = f"[thread {i}] linha {j}\n"
        semaforo.acquire()

        for caractere in linha:
            with open(arquivo_saida, "a") as f:
                f.write(caractere)

        semaforo.release()


# Função Principal
if __name__ == "__main__":
    
    # Limpar o arquivo antes de iniciar
    with open(arquivo_saida, "w") as f:
        f.write("")

    n_threads = 2
    threads = []
    
    for n in range(n_threads):
        t = threading.Thread(target=escrever_arquivo, args=(n,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
        

