# Módulo destinado a leitura, tratamento, e carga de data frames
# de empresas e sócios

from pyspark.sql.types import StructType, StructField, StringType
from pyspark.sql.functions import col, from_json, substring, when, length, split, lit
from graphframes import *


# Schema para Json Empresa
json_schema_em = StructType([
    StructField("porteEmpresa", StringType(), True),
    StructField("capitalSocial", StringType(), True),
    StructField("cpfResponsavel", StringType(), True),
    StructField("nomeEmpresarial", StringType(), True),
    StructField("naturezaJuridica", StringType(), True),
    StructField("qualificacaoResponsavel", StringType(), True)
])

# Schema para Json Estabelecimento
json_schema_es = StructType([
    StructField("uf", StringType(), True),
    StructField("cep", StringType(), True),
    StructField("ddd1", StringType(), True),
    StructField("ddd2", StringType(), True),
    StructField("pais", StringType(), True),
    StructField("email", StringType(), True),
    StructField("bairro", StringType(), True),
    StructField("numero", StringType(), True),
    StructField("municipio", StringType(), True),
    StructField("telefone1", StringType(), True),
    StructField("telefone2", StringType(), True),
    StructField("cnaeFiscal", StringType(), True),
    StructField("logradouro", StringType(), True),
    StructField("complemento", StringType(), True),
    StructField("dataCadastro", StringType(), True),
    StructField("nomeFantasia", StringType(), True),
    StructField("cidadeExterior", StringType(), True),
    StructField("tipoLogradouro", StringType(), True),
    StructField("cnaesSecundarias", StringType(), True),
    StructField("situacaoEspecial", StringType(), True),
    StructField("situacaoCadastral", StringType(), True),
    StructField("dataSituacaoEspecial", StringType(), True),
    StructField("dataSituacaoCadastral", StringType(), True),
    StructField("motivoSituacaoCadastral", StringType(), True),
    StructField("identificadorMatrizFilial", StringType(), True)
])

# Definindo o esquema para leitura do CSV
csv_schema_pj = StructType([
    StructField("id", StringType(), True),
    StructField("te_dados_em", StringType(), True),
    StructField("id_estabelecimento", StringType(), True),
    StructField("te_dados_es", StringType(), True)
])

# Schema para Json Socios
json_schema_sc = StructType([
    StructField("pais", StringType(), True),
    StructField("entradaSociedade", StringType(), True),
    StructField("socioEstrangeiro", StringType(), True),
    StructField("qualificacaoSocio", StringType(), True),
    StructField("identificadorSocio", StringType(), True),
    StructField("cpfRepresentanteLegal", StringType(), True),
    StructField("qualificacaoRepresentanteLegal", StringType(), True)
])

# Definindo o esquema para leitura do CSV
csv_schema_pf = StructType([
    StructField("nu_cnpj_raiz", StringType(), True),
    StructField("id_socio", StringType(), True),
    StructField("te_dados_sc", StringType(), True)
])


# Lê e carrega Dataframe Pessoa Física
def trata_empresa(nome_arquivo, spark):
    # Lendo o CSV com o esquema definido
    pj = spark.read \
        .option("delimiter", ",") \
        .option("multiline", "true") \
        .option("escape", "\"") \
        .csv(nome_arquivo, schema=csv_schema_pj, header=True)
    
    pj = pj.withColumn("te_dados_em", from_json(col("te_dados_em"), json_schema_em)) \
          .withColumn("te_dados_es", from_json(col("te_dados_es"), json_schema_es)) \
          .filter(substring(col("id_estabelecimento"), 0, 4) == '0001') 
    
    pj = pj.orderBy(col("id").asc()).dropDuplicates(['id'])

    return pj

def trata_socio(nome_arquivo, spark):
    socio = spark.read \
        .option("delimiter", ",") \
        .option("multiline", "true") \
        .option("escape", "\"") \
        .csv(nome_arquivo, schema=csv_schema_pf, header=True)

    # tratando o df socios
    # Tratamento 1: Expandir  colunas do campo contendo JSON
    socio = socio.withColumn("te_dados_sc", from_json(col("te_dados_sc"), json_schema_sc))
    # Recupera apenas 8 primerias posições do id_socio quando é PJ 
    socio = socio.withColumn("id_socio", when(socio["te_dados_sc"]["identificadorSocio"] == '1',
                                        socio["id_socio"].substr(1, 8))
                                    .otherwise(socio["id_socio"]))
    # Remomeia fonte e destino para compatibilizar com arestas de grafos
    # src = CNPJ da empresa
    # dst = socio (CPF ou CNPJ de pessoas sócias)
    socio = socio.withColumnRenamed("nu_cnpj_raiz", "src").withColumnRenamed("id_socio", "dst")
    # remove arestas dubplicadas
    socio = socio.orderBy(col("src").asc(), col("dst").asc()).dropDuplicates(['src', 'dst'])
    return socio

def monta_vertice(empresa, socio):
    # Cria df para vértices do tipo Pessoa Física:
    socio_pf = socio.filter(col("te_dados_sc.identificadorSocio") == '2').select(col("dst").alias("id")).distinct()
    
    cols_pj = [col_name for col_name in empresa.columns if col_name != 'id']
    for col_name in cols_pj:
        socio_pf = socio_pf.withColumn(col_name, lit(None))
    
    # cria tipo de pessoa na nos vértices
    empresa = empresa.withColumn("id_tipoPessoa", lit(1))
    socio_pf = socio_pf.withColumn("id_tipoPessoa", lit(2))
    
    vertex = empresa.union(socio_pf).orderBy("id")
    
    return vertex    

def monta_grafo(empresa, socio):
    vertex = monta_vertice(empresa, socio)
    g = GraphFrame(vertex, socio)
    
    return g