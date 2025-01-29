
from query import consulta_socios_alvo
from query import consulta_embeddings_universo
from query import consulta_nodes
from query import compara_empresa
from query import consulta_embeddings
from query import consulta_relacao_societaria
from query import consulta_socios_em_comum
from query import consulta_detalhes_socios_comuns

from sqlalchemy import create_engine
import pandas as pd
import re

DEBUG=True


string_conexao='postgresql+psycopg2://postgres:postgres@prata04.cnj.jus.br:5432/MDM'
symilarity_threshold = .9

# Calcula sililariedade de nome
def similariedade(df_sim, id_localizados, ids_alvos):
    # Filtrar o DataFrame df_sim pelos valores desejados de id_localizados e ids_alvos
    filtro = (df_sim['ids_localizados'] == id_localizados) & (df_sim['ids_alvos'] == ids_alvos)
    valor_sim_filtrado = df_sim.loc[filtro, 'valor_sim']

    # Verificar se há valores encontrados
    if not valor_sim_filtrado.empty:
        # Se houver valores encontrados, formatar como porcentagem
        valor_formatado = f"{valor_sim_filtrado.iloc[0] * 100:.2f}%"  # Considerando apenas o primeiro valor encontrado
        return valor_formatado
    else:
        return '-'

# Calcula sililariedade de nome
def similariedade_total(matriz, df_vert, df_hori, nome_chave_id, id_vert, id_hori):
    try:
        ordenada = df_vert[df_vert[nome_chave_id] == id_vert].index[0]
        abscissa = df_hori[df_hori[nome_chave_id] == id_hori].index[0]
        valor_sim = matriz[ordenada, abscissa]
        valor_formatado = f"{valor_sim * 100:.2f}%"  # Considerando apenas o primeiro valor encontrado
    except (IndexError, KeyError, ValueError):
        valor_formatado = '-' 
    return valor_formatado

def investiga(cnpjs):

    cnpjs_processado = processar_cnpjs(cnpjs) 
    cnpjs_list = cnpjs_processado.split(",")
    cnpj_alvo = [cnpj.strip() for cnpj in cnpjs_list if cnpj.strip()]

    # Cria uma string de conexão
    engine = create_engine(string_conexao)

    # consulta empresas alvo no banco de dados
    socios_alvo_final = consulta_socios_alvo(cnpj_alvo, engine)
    if socios_alvo_final.empty:
        raise ValueError(f"CNPJ(s) '{cnpjs}' não localizado(s).")

    cep_distintos = socios_alvo_final['cep'].drop_duplicates().tolist()
    embeddings_universo = consulta_embeddings_universo(cep_distintos, engine)

    # Recupera nomes Alvo para crusamento
    # ids_alvo = socios_alvo_final[socios_alvo_final['nomeFantasia'].str.strip() != '']['id'].tolist()
    ids_alvo = socios_alvo_final['id'].tolist()

    df_embeddings_alvo = consulta_embeddings(ids_alvo, engine)

    # Gera matriz de similiariedade com nomes localizados 
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    # Converter os embeddings para um formato compatível com o cosine_similarity
    embeddings = np.array(embeddings_universo['embeddings'])
    embeddings =  np.vstack(embeddings)
    embeddings_alvo = np.array(df_embeddings_alvo['embeddings'])
    embeddings_alvo = np.vstack(embeddings_alvo)

    # Calcular a matriz de similaridade usando cosine_similarity
    matriz_similaridade = cosine_similarity(embeddings_alvo, embeddings)

    # Aplica limite de Similaridade
    ordenadas, abscissas = np.where(matriz_similaridade > symilarity_threshold)

    # Obter os valores de similaridade a partir de matriz_similaridade utilizando as colunas ordenadas e abscissas
    valores_sim = matriz_similaridade[ordenadas, abscissas]
    ids_localizados = embeddings_universo.iloc[abscissas]['id'].values
    ids_alvos = df_embeddings_alvo.iloc[ordenadas]['id'].values

    # Criar o DataFrame df_sim
    df_sim = pd.DataFrame({
        'ids_localizados': ids_localizados,
        'ids_alvos': ids_alvos,
        'valor_sim': valores_sim
    })

    ids = df_sim['ids_localizados'].drop_duplicates().tolist()
    df_id_localizados = consulta_nodes (ids, engine)
    ids = df_sim['ids_alvos'].drop_duplicates().tolist()
    df_id_alvos = consulta_nodes (ids, engine)

    # Lista para armazenar os resultados de cada comparação
    resultados = {}

    # Iterar sobre cada linha de df_id_alvos
    for indice_alvos, linha_alvos in df_id_alvos.iterrows():
        id_alvo = linha_alvos['id']
        te_dados_es_alvos = linha_alvos['te_dados_es']
        te_dados_em_alvos = linha_alvos['te_dados_em']
        nome_alvo = te_dados_es_alvos['nomeFantasia']
        
        # DataFrame para armazenar os resultados desta linha de df_id_alvos
        df_resultado = {'id_alvo': [], 'id': [], 'cep': [], 'logradouro': [], 'cpfResponsavel': [], 'telefone1': [], 
                        'email': [], 'cnae': [], 'scomum': [], 'nomeSim': [], 'nomeFantasia': [], 'tp_socio': []}    
        # Iterar sobre cada linha de df_id_localizados para comparar com a linha atual de df_id_alvos
        for indice_localizados, linha_localizados in df_id_localizados.iterrows():
            id_localizados = linha_localizados['id']
            te_dados_es_localizados = linha_localizados['te_dados_es']
            te_dados_em_localizados = linha_localizados['te_dados_em']
            
            # Comparar os campos desejados
            resultado_cep = te_dados_es_alvos['cep'] == te_dados_es_localizados['cep']
            resultado_logradouro = te_dados_es_alvos['logradouro'] == te_dados_es_localizados['logradouro'] 
            resultado_cpf = te_dados_em_alvos['cpfResponsavel'] == te_dados_em_localizados['cpfResponsavel'] 
            resultado_telefone = te_dados_es_alvos['telefone1'] == te_dados_es_localizados['telefone1'] 
            resultado_email = te_dados_es_alvos['email'].upper() == te_dados_es_localizados['email'].upper() 
            resultado_cnae = te_dados_es_alvos['cnaeFiscal'] == te_dados_es_localizados['cnaeFiscal'] 
            resultado_scomum = consulta_socios_em_comum(id_alvo, id_localizados, engine)
            resultado_nomeSim = similariedade_total(matriz_similaridade, df_embeddings_alvo, embeddings_universo, 'id', id_alvo, id_localizados)
            resultado_nomeFantasia =  te_dados_es_localizados['nomeFantasia']
            
            # Adicionar resultados à lista
            df_resultado['id_alvo'].append(id_alvo)
            df_resultado['id'].append(id_localizados)
            df_resultado['cep'].append(resultado_cep)
            df_resultado['logradouro'].append(resultado_logradouro)
            df_resultado['cpfResponsavel'].append(resultado_cpf)
            df_resultado['telefone1'].append(resultado_telefone)
            df_resultado['email'].append(resultado_email)
            df_resultado['cnae'].append(resultado_cnae)
            df_resultado['scomum'].append(resultado_scomum)
            df_resultado['nomeSim'].append(resultado_nomeSim)
            df_resultado['nomeFantasia'].append(resultado_nomeFantasia)
            df_resultado['tp_socio'].append(consulta_relacao_societaria(id_alvo, id_localizados, engine))
        
        # Criar DataFrame com os resultados desta linha de df_id_alvos
        df_resultado = pd.DataFrame(df_resultado)
        
        # Adicionar à lista de resultados com o título correspondente
        titulo = f"Alvo = {id_alvo} - {nome_alvo}"
        resultados[titulo] = df_resultado.to_dict(orient='records')

    response_data = resultados

    return response_data

def compara(cnpjs):
    cnpjs_list = cnpjs.split(",")
    ids = [cnpj.strip() for cnpj in cnpjs_list if cnpj.strip()]

    # Cria uma string de conexão
    engine = create_engine(string_conexao)
    
    # Recupera detalhes da comparação
    response_data = compara_empresa(ids, engine)

    # Recupera lista de sócios comuns
    s1, s2 = ids
    socios_comuns = consulta_detalhes_socios_comuns(s1, s2, engine)
    response_data["socios_comuns"] = socios_comuns

    return response_data

def processar_cnpjs(cnpj_input):
    cnpjs_processados = [
        re.sub(r"\D", "", cnpj)[:8]  # Remove caracteres não numéricos e pega os 8 primeiros dígitos
        for cnpj in cnpj_input.split(",")
    ]
    return ",".join(cnpjs_processados)  # Junta os valores separados por vírgula
