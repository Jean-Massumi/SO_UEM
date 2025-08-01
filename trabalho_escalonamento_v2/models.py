from dataclasses import dataclass

@dataclass
class TempoExecucao:
    '''
        Representa informações de tempo de execução de uma thread.
    '''

    tempo_total: int
    tempo_restante: int


@dataclass
class TipoPrioridade:
    '''
        Gerencia as prioridades estática e dinâmica de uma thread.
    
        Usado pelos algoritmos de escalonamento baseados em prioridade.
        Valores menores indicam maior prioridade.
    '''

    prio_e: int
    prio_d: int


@dataclass
class Thread:
    '''
        Representa uma thread/processo a ser escalonado pelo sistema.
        
        Contém todas as informações necessárias para o escalonamento,
        incluindo tempo de chegada, duração prevista e prioridades.  
    '''

    id: str
    tempo_ingresso: int
    duracao_prevista: TempoExecucao
    prioridade: TipoPrioridade

    @classmethod
    def from_dict(cls, data):
        '''
            Cria uma instância de Thread a partir de um dicionário
        '''

        duracao = data['duracao_prevista']
        prioridade = data['prioridade']

        return cls(
            id=data['id'],
            tempo_ingresso=data['tempo_ingresso'],
            duracao_prevista= TempoExecucao(
                tempo_total=duracao,
                tempo_restante=duracao),
            prioridade= TipoPrioridade(
                prio_e=prioridade,
                prio_d=prioridade)
        )


@dataclass
class Tarefa_Finalizada:
    '''
        Armazena informações de uma tarefa que foi concluída
    '''

    ID: str
    clock_de_ingresso: int
    clock_de_finalizacao: int
    turn_around_time: int
    waiting_time: int