from sqlalchemy import create_engine
from sqlalchemy import text
import pandas as pd

DEBUG=False

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

# Query para consultar todas empresas em uma lista de ID
def monta_query_nodes(ids):
    placeholders = ", ".join([f":id{i}" for i in range(len(ids))])  # Cria placeholders nomeados
    query = text(f"""
    SELECT *
    FROM nodes
    WHERE nodes.id IN ({placeholders})
    """)

    params = {f"id{i}": id_ for i, id_ in enumerate(ids)}  # Mapeia os IDs para os placeholders
    return query, params

# Query para verficar relação societária
def monta_query_relacao_societaria(p1, p2):
    query = text("""
        SELECT COUNT(*) 
        FROM edges
        WHERE (edges.src = :p1 AND edges.dst = :p2) OR 
              (edges.dst = :p1 AND edges.src = :p2)
    """)
    params = {"p1": p1, "p2": p2}
    return query, params

def consulta_relacao_societaria(p1, p2, engine):
    # Se forem a mesma pessoa, retorna 2
    if p1 == p2:
        return 2

    # Monta a query para verificar relação societária
    query, params = monta_query_relacao_societaria(p1, p2)
        
    with engine.connect() as conn:
        result = conn.execute(query, params).scalar()

    if(DEBUG):
        print(f"Parâmetros: {params}", flush=True)
        print(f"Resultado : {result}", flush=True)

    # Retorna 1 se forem sócios, 0 caso contrário
    return 1 if result > 0 else 0

def monta_query_socios_comuns(s1, s2):
    query = text("""
        SELECT COUNT(*) AS total_interseccao
        FROM (
            SELECT DISTINCT e1.socios
            FROM (
                SELECT edges.src AS socios
                FROM edges
                WHERE edges.dst = :s1
                UNION ALL
                SELECT edges.dst AS socios
                FROM edges
                WHERE edges.src = :s1
            ) e1
            INNER JOIN (
                SELECT edges.src AS socios
                FROM edges
                WHERE edges.dst = :s2
                UNION ALL
                SELECT edges.dst AS socios
                FROM edges
                WHERE edges.src = :s2
            ) e2
            ON e1.socios = e2.socios
        ) AS interseccao
    """)
    
    params = {"s1": s1, "s2": s2}
    return query, params

def consulta_socios_em_comum(s1, s2, engine):

    if s1 == s2:
        return True
    # Monta a query para verificar sócios em comum
    query, params = monta_query_socios_comuns(s1, s2)

    with engine.connect() as conn:
        result = conn.execute(query, params).scalar()

    if DEBUG:
        print(f"Parâmetros: {params}")
        print(f"Resultado: {result}")

    # Retorna True se houver pelo menos um sócio em comum, False caso contrário
    return result > 0

def consulta_socios_alvo(cnpj_alvo, engine, cpf_alvo=None):
    socios_lista = cnpj_alvo  
    # Se cpf_alvo for fornecido como lista, adicioná-lo à cópia de cnpj_alvo
    if cpf_alvo:
        socios_lista.extend(cpf_alvo) 

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

def monta_query_detalhes_socios_comuns(s1, s2):
    query = text("""
        SELECT DISTINCT e1.socios, e1.tp_socio
        FROM (
            SELECT edges.src AS socios, te_dados_sc->>'identificadorSocio' AS tp_socio
            FROM edges
            WHERE edges.dst = :s1
            UNION ALL
            SELECT edges.dst AS socios, te_dados_sc->>'identificadorSocio' AS tp_socio
            FROM edges
            WHERE edges.src = :s1
        ) e1
        INNER JOIN (
            SELECT edges.src AS socios, te_dados_sc->>'identificadorSocio' AS tp_socio
            FROM edges
            WHERE edges.dst = :s2
            UNION ALL
            SELECT edges.dst AS socios, te_dados_sc->>'identificadorSocio' AS tp_socio
            FROM edges
            WHERE edges.src = :s2
        ) e2
        ON e1.socios = e2.socios
        ORDER BY e1.tp_socio
    """)
    
    params = {"s1": s1, "s2": s2}
    return query, params

def consulta_detalhes_socios_comuns(s1, s2, engine):
    # Se forem a mesma PJ, retorna uma lista vazia, pois não há interseção relevante
    if s1 == s2:
        return []

    # Monta a query para buscar os sócios em comum
    query, params = monta_query_detalhes_socios_comuns(s1, s2)

    with engine.connect() as conn:
        result = conn.execute(query, params).fetchall()

    if DEBUG:
        print(f"Parâmetros: {params}")
        print(f"Resultado: {result}")

    # Retorna uma lista de dicionários com os sócios em comum
    return [{"socios": row[0], "tp_socio": row[1]} for row in result]

def consulta_embeddings_universo(cep_distintos, engine):
    return pd.read_sql_query(monta_query_universo_embeddings(cep_distintos), engine)

def consulta_nodes(ids, engine):
    query, params = monta_query_nodes(ids)
    with engine.connect() as conn:
        df_emp = pd.read_sql_query(query, conn, params=params)
    return df_emp

def compara_empresa(ids, engine):
    query, params = monta_query_nodes(ids)  # Obtém a consulta segura e os parâmetros

    with engine.connect() as conn:
        df_emp = pd.read_sql_query(query, conn, params=params)  # Executa a query com segurança

    if len(df_emp) == 0:
        return {}  

    elif len(df_emp) == 1:
        registro1_emp = df_emp.iloc[0]['te_dados_em']
        registro1_es = df_emp.iloc[0]['te_dados_es']
        registro2_emp = df_emp.iloc[0]['te_dados_em']
        registro2_es = df_emp.iloc[0]['te_dados_es']
    else:
        # Reordenar os resultados de acordo com a ordem dos IDs fornecidos
        df_emp["id_order"] = pd.Categorical(df_emp["id"], categories=ids, ordered=True)
        df_emp = df_emp.sort_values("id_order")  # Garante a ordem original da lista

        registro1_emp = df_emp.iloc[0]['te_dados_em']
        registro1_es = df_emp.iloc[0]['te_dados_es']
        registro2_emp = df_emp.iloc[1]['te_dados_em']
        registro2_es = df_emp.iloc[1]['te_dados_es']

    # Inicializa a estrutura que armazenará os campos lado a lado
    comparacao = {}

    # Coleta todas as chaves (campos) dos dicionários
    all_keys_emp = set(registro1_emp.keys()).union(set(registro2_emp.keys()))
    all_keys_es = set(registro1_es.keys()).union(set(registro2_es.keys()))

    # Para os campos de te_dados_em
    comparacao['te_dados_em'] = {}
    for key in all_keys_emp:
        comparacao['te_dados_em'][key] = {
            'registro1': registro1_emp.get(key, 'N/A'),
            'registro2': registro2_emp.get(key, 'N/A')
        }

    # Para os campos de te_dados_es
    comparacao['te_dados_es'] = {}
    for key in all_keys_es:
        comparacao['te_dados_es'][key] = {
            'registro1': registro1_es.get(key, 'N/A'),
            'registro2': registro2_es.get(key, 'N/A')
        }

    return comparacao