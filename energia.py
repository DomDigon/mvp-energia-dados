import pandas as pd

df = pd.read_csv('consumo_energia_eletrica_uf.csv', sep=',')

#df original tem 12960 Nan na coluna numero_consumidores
#print(df.isna().sum())

#38880 linhas no Dataframe. Coluna 'numero_consumidores' possui Nan
#df.info()

#Verificando quais tipo de consumo são Nan
#print(df[df['numero_consumidores'].isna()]['tipo_consumo'].value_counts())

quantidade_Total = (df['tipo_consumo'] == 'Total').sum()
#print(f'Quantidade de entrada "Total" em tipo_consumo: {quantidade_Total}')

nan_Consum = df['numero_consumidores'].isna().sum()
#print(f'Quantidade de Nan em tipo_consumo: {nan_Consum}')

qtd_Outros = (df['tipo_consumo'] == 'Outros').sum()
#print(f'Quantidade de entrada "Outros" em tipo_consumo: {qtd_Outros}')

qtd_Comercial = (df['tipo_consumo'] == 'Comercial').sum()
#print(f'Quantidade de entradas "Comercial" em tipo_consumo: {qtd_Comercial}')

#Dataset está perfeitamente balanceado. Todos os tipo de consumo foram contabilizados por todas as 27 UF, mensalmente por 20 anos.
#print(df['tipo_consumo'].value_counts())

"""
Gabarito:


Tipo_Consumo

Total: É a soma agregada de todas as categorias. Se você somar os valores das outras linhas (Residencial, Comercial, Industrial, Outros, etc.) para o mesmo mês/estado, vai bater com o valor de Total. Cuidado!
Ao fazer um gráfico de soma ou uma média geral do estado, precisa filtrar para tirar o Total, senão vai duplicar a energia duas vezes (contando as categorias individuais e somando o Total junto).

Outros: Agrupa classes menores que não entram nas grandes categorias tradicionais, como Poder Público, Iluminação Pública, Consumo Próprio da concessionária, Iluminação Pública e Serviço Público (como tração elétrica/metrô).

Cativo: Consumidores que são obrigados a contratar o serviço de uma distribuidora específica, como Light, Enel.

Residencial, Comercial e Industrial: Auto explicativos

"""

#Testando Total com Groupby. Acredito que o consumo Total deve bater com a soma dos consumos dos tipo Residencial, Comercial, Industrial e Outros.

categorias = ['Residencial' , 'Industrial' , 'Comercial' , 'Outros']

df_total = (
    df[df['tipo_consumo'] == 'Total']
    .groupby(['sigla_uf' , 'ano' , 'mes'])['consumo']
    .sum()
    .reset_index(name='total_oficial')
)

df_categorias = (
    df[df['tipo_consumo'].isin(categorias)]
    .groupby(['sigla_uf', 'ano' , 'mes'])['consumo']
    .sum()
    .reset_index(name='soma_categorias')
)

auditoria = pd.merge(df_total, df_categorias, on=['sigla_uf', 'ano' , 'mes'])
auditoria['diferença'] = auditoria['total_oficial'] - auditoria['soma_categorias']

erros = auditoria[auditoria['diferença'].abs() > 2]

#print(f"Total de meses/estados auditados: {len(auditoria)}")
#print(f"Total de inconsistências reais encontradas: {len(erros)}")


#Após testar com groupby e filtros, constatei que há diferença de poucas unidades entre o consumo Total e o consumo das 4 categorias. Entao a coluna Total pode ser excluída do dataframe para evitar duplicidade de entrada. 
# Agora vou testar a mesma coisa para a coluna Cativo. Suspeito que seja a soma de Residencial, Comercial e Industrial. 

categorias_1 = ['Residencial', 'Comercial' , 'Industrial']

df_Cativo = (
    df[df['tipo_consumo'] == 'Cativo']
    .groupby(['sigla_uf' , 'mes' , 'ano'])['consumo']
    .sum()
    .reset_index(name='total_cativos')
    )

df_categorias_1 = (
    df[df['tipo_consumo'].isin(categorias_1)]
    .groupby(['sigla_uf' , 'mes' , 'ano'])['consumo']
    .sum()
    .reset_index(name='soma_categorias1')
)

auditoria_Cativos = pd.merge(df_Cativo, df_categorias_1, on=['sigla_uf' , 'mes' , 'ano'])
auditoria_Cativos['diferença'] = auditoria_Cativos['total_cativos'] - auditoria_Cativos['soma_categorias1']

erros_Cativos = auditoria_Cativos[auditoria_Cativos['diferença'].abs() > 2]

#print(f"Total de meses/estados auditados: {len(auditoria_Cativos)}")
#print(f"Total de inconsistências reais encontradas: {len(erros_Cativos)}")

#Após testar o groupby, encontrei nenhuma relação direta entre Cativos e os atributos Residencial, Comercial e Industrial. Consumidores Cativos são consumidores de energia que estão obrigados a uma distribuidora, como ENEL, LIGHT, etc. Enquanto consumidores livres podem contratar de qualquer distribuidora. Então, conclui-se que consumidores podem ser cativos ou não em todas as categorias. Exemplo: Um consumidor pode ser Comercial e Cativo enquanto outro Comercial e Livre. Contudo, não há essa distinção na tabela. Quando informa 'Cativo' não se informa é Residencial, Comercial ou Industrial. Cativo deveria estar numa coluna separada como Tipo_serviço, tendo Cativo e Livre como valores.

# Assim, vamos trabalhar com o dataframe sem os atributos Total e Cativo em tipo consumo.

remover = ['Total' , 'Cativo']
df_limpo = df[~df['tipo_consumo'].isin(remover)].copy()

#Para otimizar RAM, vamos converter as categorias sigla_uf e tipo_consumo para category

df_limpo['sigla_uf'] = df_limpo['sigla_uf'].astype('category')
df_limpo['tipo_consumo'] = df_limpo['tipo_consumo'].astype('category')

#vamos aproveitar e compactar numero_consumidores ano e mes
df_limpo['numero_consumidores'] = df_limpo['numero_consumidores'].astype('Int32')
df_limpo['ano'] = df_limpo['ano'].astype('Int16')
df_limpo['mes'] = df_limpo['mes'].astype('Int8')

#df original 1.8 MB. df_limpo 710.2 KB
#df_limpo.info()

