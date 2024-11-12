from sqlalchemy import create_engine
import pandas as pd

# Query para consultar todas embeddings de empresas por CEP
def monta_query_universo_embeddings(cep):
    cep_str = "', '".join(cep)
    query = f"""
    SELECT embeddings.id,
           embeddings.nomefantasia,
           embeddings.embeddings
    FROM embeddings
    INNER JOIN nodes ON embeddings.id = nodes.id
    WHERE nodes.CEP IN ('{cep_str}')
    """ 
    return query

# Query para consultar todas embeddings na lista de IDs
def monta_query_embeddings(ids):
    ids_str = "', '".join(ids)
    query = f"""
    SELECT embeddings.id,
           embeddings.nomefantasia,
           embeddings.embeddings
    FROM embeddings
    WHERE embeddings.id IN ('{ids_str}')
    """ 
    return query

def consulta_embeddings(ids, engine):
    df = pd.read_sql_query(monta_query_embeddings(ids), engine)
    return df
    
# Monta querys CNPJs Alvos
def monta_query_cnpj_alvo(cnpj_alvo):
    # Transformando a lista cnpj_alvo em uma string adequada para a cláusula IN
    cnpj_alvo_str = "', '".join(cnpj_alvo)
    query = f"""
    SELECT edges.src, edges.dst, 
           nodes_src.cep AS src_cep, 
           nodes_dst.cep AS dst_cep,
           nodes_dst.id_tipopessoa,
           nodes_src.id_tipopessoa AS src_id_tipopessoa,
           nodes_src.te_dados_es->>'nomeFantasia' AS src_nome,
           nodes_dst.te_dados_es->>'nomeFantasia' AS dst_nome,
           nodes_src.te_dados_em->>'nomeEmpresarial' AS src_nome_em,
           nodes_dst.te_dados_em->>'nomeEmpresarial' AS dst_nome_em
    FROM edges
    INNER JOIN nodes AS nodes_src ON nodes_src.id = edges.src
    INNER JOIN nodes AS nodes_dst ON nodes_dst.id = edges.dst
    WHERE edges.dst IN ('{cnpj_alvo_str}') OR edges.src IN ('{cnpj_alvo_str}');
    """
    return query

# Query para consultar todas empresas em um alista de ID
def monta_query_nodes(id):
    id_str = "', '".join(id)
    query = f"""
    SELECT *
    FROM nodes
    WHERE nodes.id IN ('{id_str}')
    """ 
    return query



def consulta_socios_alvo(cnpj_alvo, engine):
    # Separa sócios somente do tipo CNPJ, tanto na origem, como no destino
    socios_alvo = pd.read_sql_query(monta_query_cnpj_alvo(cnpj_alvo), engine)
    condicao_1 = socios_alvo[socios_alvo['src_id_tipopessoa'] == 1][['src', 'src_nome', 'src_cep', 'src_nome_em']].rename(columns={
        'src': 'id',
        'src_nome': 'nomeFantasia',
        'src_cep': 'cep',
        'src_nome_em': 'nomeEmpresarial'
    })
    condicao_2 = socios_alvo[socios_alvo['id_tipopessoa'] == 1][['dst', 'dst_nome', 'dst_cep', 'dst_nome_em']].rename(columns={
        'dst': 'id',
        'dst_nome': 'nomeFantasia',
        'dst_cep': 'cep',
        'dst_nome_em': 'nomeEmpresarial'
    })

    # Juntar as duas condições e remover linhas duplicadas
    socios_alvo_final = pd.concat([condicao_1, condicao_2]).drop_duplicates()
    return socios_alvo_final

def consulta_embeddings_universo(cep_distintos, engine):
    return pd.read_sql_query(monta_query_universo_embeddings(cep_distintos), engine)

def consulta_nodes(ids, engine):
    return pd.read_sql_query(monta_query_nodes(ids), engine)

def copara_empresa(ids, engine):
    df_emp = pd.read_sql_query(monta_query_nodes(ids), engine)
    if len(df_emp) == 0:
        return {}  
    elif len(df_emp) == 1:
        registro1_emp = df_emp.iloc[0]['te_dados_em']
        registro1_es = df_emp.iloc[0]['te_dados_es']
        registro2_emp = df_emp.iloc[0]['te_dados_em']
        registro2_es = df_emp.iloc[0]['te_dados_es']
    else:
        registro1_emp = df_emp.iloc[0]['te_dados_em']
        registro1_es = df_emp.iloc[0]['te_dados_es']
        registro2_emp = df_emp.iloc[1]['te_dados_em']
        registro2_es = df_emp.iloc[1]['te_dados_es']
    
    # Inicializa a estrutura que armazenará os campos lado a lado
    comparacao = {}
    
    # Coleta todas as chaves (campos) dos dicionários
    all_keys_emp = set(registro1_emp.keys()).union(set(registro2_emp.keys()))
    all_keys_es = set(registro1_es.keys()).union(set(registro2_es.keys()))

    # Para os campos de te_dados_emp
    comparacao['te_dados_em'] = {}
    for key in all_keys_emp:
        comparacao['te_dados_em'][key] = {
            'registro1': registro1_emp.get(key, 'N/A'),  # Valor do registro 1
            'registro2': registro2_emp.get(key, 'N/A')   # Valor do registro 2
        }
    
    # Para os campos de te_dados_es
    comparacao['te_dados_es'] = {}
    for key in all_keys_es:
        comparacao['te_dados_es'][key] = {
            'registro1': registro1_es.get(key, 'N/A'),  # Valor do registro 1
            'registro2': registro2_es.get(key, 'N/A')   # Valor do registro 2
        }
    
    return comparacao