from dataclasses import dataclass

@dataclass
class TempoExecucao:
    tempo_total: int
    tempo_restante: int


@dataclass
class Thread:
    '''
        Representa uma thread a ser escalonado        
    '''

    id: str
    tempo_ingresso: int
    duracao_prevista: TempoExecucao
    prioridade: int

    @classmethod
    def from_dict(cls, data):
        '''
            Cria uma instância de Thread a partir de um dicionário
        '''

        duracao = data['duracao_prevista']

        return cls(
            id=data['id'],
            tempo_ingresso=data['tempo_ingresso'],
            duracao_prevista= TempoExecucao(
                tempo_total=duracao,
                tempo_restante=duracao),
            prioridade=data['prioridade']
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