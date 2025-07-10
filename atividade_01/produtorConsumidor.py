from multiprocessing import Process, Pipe
import time
import random

# Marca o tempo inicial para cálculo dos tempos relativos
inicio = time.time()

def produtor(conn):
    """
    Função do produtor que gera itens e os envia para o consumidor.
    
    Args:
        conn: Conexão Pipe para enviar dados ao consumidor
    """
    for i in range(3):
        # Produz um item
        send_start = time.time()
        print(f"[{send_start - inicio:.4f} s] Produtor - Iniciou a produção do item {i} \n")
        
        # Simula tempo variável de produção
        time.sleep(random.uniform(1, 2))
        
        # Envia o item produzido
        send_end = time.time()
        print(f"[{send_end - inicio:.4f} s] Produtor - Finalizou a produção do item {i}. Enviando para o consumidor... \n")
        conn.send(i)
    
    # Envia sinal de finalização
    send_finalizacao = time.time()
    print(f"[{send_finalizacao - inicio:.4f} s] Produtor - Sinal de finalização")
    conn.send("Fim")
    conn.close()
    
    
def consumidor(conn):
    """
    Função do consumidor que recebe e processa itens do produtor.
    
    Args:
        conn: Conexão Pipe para receber dados do produtor
    """
    while True:
        # Recebe um item ou sinal de finalização
        produto = conn.recv()
        
        # Verifica se é o sinal de finalização
        if produto == "Fim":
            recv_finalizacao = time.time()
            print(f"[{recv_finalizacao - inicio:.4f} s] Consumidor - Sinal de finalização recebido")
            break
        
        # Processa o item recebido
        recv_recepcao = time.time()
        print(f"[{recv_recepcao - inicio:.4f} s] Consumidor - Recebeu produto {produto}. \n")
        
        # Simula tempo variável de consumo
        time.sleep(random.uniform(1, 2))
    
        # Confirma o consumo do item
        recv_consumacao = time.time()
        print(f"[{recv_consumacao - inicio:.4f} s] Consumidor - Consumiu produto {produto}. \n")
    

if __name__ == "__main__":
    # Cria os dois lados da Pipe (produtor e consumidor)
    prod_conn, cons_conn = Pipe()
    
    # Cria os processos
    proc_prod = Process(target=produtor, args=(prod_conn,))
    proc_cons = Process(target=consumidor, args=(cons_conn,))

    print("\n")

    # Inicia os processos
    proc_prod.start()
    proc_cons.start()
    
    # Aguarda a finalização dos processos
    proc_prod.join()
    proc_cons.join()  # Corrigido: estava proc_prod.join() duas vezes
    
    print("\n")
