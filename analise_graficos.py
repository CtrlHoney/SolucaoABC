import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configurações de estilo para os gráficos
sns.set_theme(style="whitegrid")
plt.rcParams.update({'figure.max_open_warning': 0}) # Evita avisos de muitas figuras abertas

PASTA_BASE = os.path.dirname(os.path.abspath(__file__))

def parse_resultados():
    """
    Varre as pastas geradas, lê os arquivos .txt e consolida os dados.
    """
    dados = []
    
    # Procura pelas pastas TPApp1 a TPApp5
    for app_dir in os.listdir(PASTA_BASE):
        if not app_dir.startswith("TPApp"):
            continue
            
        app_path = os.path.join(PASTA_BASE, app_dir)
        app_name = app_dir.replace("TPApp", "APP ")
        
        # Procura pelas variações (TPa, TPc, TPr, TPacr)
        for var_dir in os.listdir(app_path):
            if not var_dir.startswith("TP"):
                continue
                
            var_path = os.path.join(app_path, var_dir)
            variacao = var_dir.replace("TP", "")
            
            # Procura pelos cenários (Cenario1_Padrao, etc.)
            for cenario_dir in os.listdir(var_path):
                if not cenario_dir.startswith("Cenario"):
                    continue
                    
                cenario_path = os.path.join(var_path, cenario_dir)
                nome_cenario = cenario_dir.split("_", 1)[1] if "_" in cenario_dir else cenario_dir
                
                # Lê os Tempos de Execução
                tempos = []
                arq_tempo = [f for f in os.listdir(cenario_path) if f.startswith("executionTime")]
                if arq_tempo:
                    with open(os.path.join(cenario_path, arq_tempo[0]), 'r') as f:
                        for linha in f:
                            linha = linha.strip()
                            if linha.isdigit():
                                tempos.append(int(linha))
                
                tempo_medio = sum(tempos)/len(tempos) if tempos else 0
                
                # Lê os Resultados (Score, Cost, Ava, RT)
                arq_result = [f for f in os.listdir(cenario_path) if f.startswith("resultData")]
                scores, costs, avas, rts = [], [], [], []
                
                if arq_result:
                    with open(os.path.join(cenario_path, arq_result[0]), 'r') as f:
                        conteudo = f.read()
                        # Regex para capturar os dados da linha "APP Data: ..."
                        # Nota: o script original escrevia "Socre = " ao invés de "Score = "
                        padrao = r"APP Data:\s*Availability\s*=\s*([\d.]+).*?Response Time\s*=\s*([\d.]+).*?Cost\s*=\s*([\d.]+).*?Socre\s*=\s*([\d.]+)"
                        matches = re.findall(padrao, conteudo)
                        
                        for match in matches:
                            avas.append(float(match[0]))
                            rts.append(float(match[1]))
                            costs.append(float(match[2]))
                            scores.append(float(match[3]))
                
                # Registra a média das execuções para este cenário
                if scores:
                    dados.append({
                        "Aplicacao": app_name,
                        "Variacao": variacao,
                        "Cenario": nome_cenario,
                        "TempoMedio_ms": tempo_medio,
                        "ScoreMedio": sum(scores)/len(scores),
                        "CustoMedio": sum(costs)/len(costs),
                        "DispMedia": sum(avas)/len(avas),
                        "TempoRespMedio": sum(rts)/len(rts)
                    })

    return pd.DataFrame(dados)

def gerar_graficos(df):
    """
    Gera e salva os gráficos de análise baseados no DataFrame
    """
    pasta_graficos = os.path.join(PASTA_BASE, "Graficos_Analise")
    if not os.path.exists(pasta_graficos):
        os.makedirs(pasta_graficos)
        
    print(f"\nGerando gráficos em: {pasta_graficos}...")

    # 1. Gráfico de Tempo de Execução por Cenário (Visão Geral)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x="Cenario", y="TempoMedio_ms", hue="Cenario", palette="viridis", legend=False)
    plt.title("Tempo Médio de Execução por Cenário ABC (ms)", fontsize=14)
    plt.ylabel("Tempo (ms)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(pasta_graficos, "1_Tempo_Execucao_Cenarios.png"))
    plt.close()

    # 2. Gráfico de Score por Cenário (Avaliando a Qualidade da Solução)
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df, x="Cenario", y="ScoreMedio", hue="Cenario", palette="magma", legend=False)
    plt.title("Distribuição do Score (Pontuação) por Cenário", fontsize=14)
    plt.ylabel("Score")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(pasta_graficos, "2_Score_Cenarios.png"))
    plt.close()

    # 3. Comparação de Custo e Tempo de Resposta (Trade-offs)
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x="CustoMedio", y="TempoRespMedio", hue="Cenario", style="Variacao", s=100, palette="deep")
    plt.title("Trade-off: Custo Médio vs Tempo de Resposta", fontsize=14)
    plt.xlabel("Custo Médio")
    plt.ylabel("Tempo de Resposta Médio (RT)")
    plt.tight_layout()
    plt.savefig(os.path.join(pasta_graficos, "3_Tradeoff_Custo_TempoResp.png"))
    plt.close()
    
    # 4. Impacto das Variações de Peso (Ability, Cost, RT, ACR) no Score
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x="Aplicacao", y="ScoreMedio", hue="Variacao", palette="pastel")
    plt.title("Score Médio por Aplicação e Variação de Pesos (Prioridades)", fontsize=14)
    plt.ylabel("Score")
    plt.legend(title="Variação (Pesos)")
    plt.tight_layout()
    plt.savefig(os.path.join(pasta_graficos, "4_Score_Variacoes_Prioridade.png"))
    plt.close()

    print("-> Gráficos gerados com sucesso!")

def gerar_explicacoes_texto(df):
    """
    Analisa os dados e gera um relatório textual de conclusões.
    """
    if df.empty:
        print("Nenhum dado encontrado para gerar explicações.")
        return

    print("\n" + "="*60)
    print(" 📊 RELATÓRIO DE ANÁLISE AUTOMATIZADA - ALGORITMO ABC")
    print("="*60)
    
    # Qual cenário é o mais rápido?
    cenario_mais_rapido = df.groupby('Cenario')['TempoMedio_ms'].mean().idxmin()
    tempo_min = df.groupby('Cenario')['TempoMedio_ms'].mean().min()
    print(f"\n⚡ DESEMPENHO COMPUTACIONAL (TEMPO):")
    print(f"O cenário mais rápido em média foi o '{cenario_mais_rapido}' ({tempo_min:.2f} ms).")
    print("-> Explicação: Isso geralmente ocorre nos cenários configurados com menor limite de iterações (iteMax) e menor número de abelhas (nBees), favorecendo a execução em tempo real em detrimento de uma exploração profunda do espaço de busca.")

    # Qual cenário tem o melhor Score?
    cenario_melhor_score = df.groupby('Cenario')['ScoreMedio'].mean().idxmax()
    score_max = df.groupby('Cenario')['ScoreMedio'].mean().max()
    print(f"\n🎯 QUALIDADE DA SOLUÇÃO (SCORE):")
    print(f"O cenário que encontrou as melhores combinações de serviços foi o '{cenario_melhor_score}' (Score médio: {score_max:.4f}).")
    print("-> Explicação: Cenários de 'Explotacao_Profunda' ou 'Enxame_Massivo' permitem que as abelhas observem os vizinhos por mais tempo e explorem mais fontes de alimento (microsserviços), evitando mínimos locais, mas custam mais tempo de processamento.")

    # Impacto das Variações
    var_melhor_disp = df.groupby('Variacao')['DispMedia'].mean().idxmax()
    print(f"\n⚖️ IMPACTO DOS PESOS (VARIAÇÕES a, c, r, acr):")
    print(f"A variação '{var_melhor_disp}' foi a que obteve a maior Disponibilidade média.")
    print("-> Explicação: O método SAW dentro da função Fitness do algoritmo ABC direciona o enxame para otimizar as métricas de acordo com a prioridade (weights) definida nos arquivos JSON.")
    
    print("\n" + "="*60)
    print(f"✅ Os gráficos detalhados foram salvos na pasta 'Graficos_Analise'.")
    print("="*60 + "\n")

if __name__ == '__main__':
    print("Iniciando a extração dos dados...")
    df_resultados = parse_resultados()
    
    if df_resultados.empty:
        print("[ERRO] Nenhum dado foi encontrado. Verifique se os testes rodaram corretamente e se as pastas TPAppX existem.")
    else:
        print(f"Dados extraídos com sucesso! Foram encontradas {len(df_resultados)} instâncias de testes consolidadas.")
        
        # Opcional: Salva todos os dados em um CSV para você analisar no Excel se quiser
        df_resultados.to_csv(os.path.join(PASTA_BASE, "resultados_consolidados.csv"), index=False)
        print("-> Planilha 'resultados_consolidados.csv' salva.")
        
        gerar_graficos(df_resultados)
        gerar_explicacoes_texto(df_resultados)