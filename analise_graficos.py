import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuração de estilo dos gráficos
sns.set_theme(style="whitegrid")

def extrair_todos_dados_tp():
    """Varre todas as subpastas e extrai dados de TODAS as variações TP (TPa, TPc, TPr, TPacr)"""
    diretorio_base = Path.cwd()
    print(f"🔍 Iniciando varredura recursiva em: {diretorio_base}")
    
    dados = []
    
    # rglob encontra todos os arquivos resultData, em qualquer nível de subpasta
    for result_file in diretorio_base.rglob("resultData*.txt"):
        parts = result_file.parts
        
        # Identifica a qual App e Variação o arquivo pertence analisando o caminho
        try:
            idx_app = next(i for i, p in enumerate(parts) if p.startswith("TPApp"))
            app_name = parts[idx_app].replace("TPApp", "APP ")
            variacao = parts[idx_app + 1] # TPa, TPc, TPr, ou TPacr
            cenario_folder = parts[idx_app + 2]
            nome_cenario = cenario_folder.split("_", 1)[1] if "_" in cenario_folder else cenario_folder
        except StopIteration:
            continue

        # Lê os resultados extraindo o melhor consolidado da aplicação
        try:
            with open(result_file, 'r', encoding='utf-8', errors='ignore') as f:
                conteudo = f.read()
        except Exception:
            continue

        # Regex blindado (Suporta os typos do testes.py como 'Socre' e formatações instáveis)
        padrao = r"APP Data:\s*Availability\s*=\s*([\d.]+)\s*Response Time\s*=\s*([\d.]+)\s*Cost\s*=\s*([\d.]+)\s*(?:Socre|Score)\s*=\s*([\d.]+)"
        matches = re.findall(padrao, conteudo, re.IGNORECASE)
        
        if not matches:
            continue
            
        # Pega sempre a última linha de 'APP Data' do arquivo (o final da execução)
        ava, rt, cost, score = map(float, matches[-1])

        # Lê o arquivo de tempo (executionTime) associado
        exec_file_name = result_file.name.replace("resultData", "executionTime")
        exec_file_path = result_file.parent / exec_file_name
        
        tempo_medio = 0
        if exec_file_path.exists():
            try:
                with open(exec_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    tempos = [int(linha.strip()) for linha in f if linha.strip().isdigit()]
                    if tempos:
                        tempo_medio = sum(tempos) / len(tempos)
            except Exception:
                pass

        dados.append({
            "Aplicacao": app_name,
            "Variacao_TP": variacao,
            "Cenario": nome_cenario,
            "Tempo_Execucao_ms": tempo_medio,
            "Score": score,
            "Disponibilidade": ava,
            "Custo": cost,
            "Tempo_Resposta": rt
        })

    return pd.DataFrame(dados)

def gerar_graficos_analise():
    df = extrair_todos_dados_tp()
    
    if df.empty:
        print("❌ [ERRO] Nenhum dado encontrado. Verifique se as pastas TPAppX possuem arquivos de resultados.")
        return

    print(f"✅ Sucesso! {len(df)} instâncias de testes extraídas.")
    
    pasta_saida = Path.cwd() / "Resultados_Graficos_TP"
    pasta_saida.mkdir(exist_ok=True)
    
    print(f"📊 Gerando gráficos em: {pasta_saida.absolute()}")

    # 1. GRÁFICO DE ESFORÇO COMPUTACIONAL (TEMPO)
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=df, x="Cenario", y="Tempo_Execucao_ms", hue="Cenario", palette="magma", legend=False)
    plt.title("Tempo de Execução por Cenário ABC (Todas as Aplicações e TPs)", fontsize=14, weight='bold')
    plt.ylabel("Tempo Médio (ms)")
    plt.xlabel("")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(pasta_saida / "1_Tempo_Execucao_Geral.png")
    plt.close()

    # 2. GRÁFICO DE DESEMPENHO (SCORE) POR VARIAÇÃO TP
    plt.figure(figsize=(14, 7))
    sns.barplot(data=df, x="Variacao_TP", y="Score", hue="Cenario", palette="viridis", errorbar=None)
    plt.title("Comparação de Score Médio: Como os Cenários reagem a diferentes Pesos (TPs)", fontsize=14, weight='bold')
    plt.ylabel("Score Consolidado")
    plt.xlabel("Tipo de Variação (Pesos de Avaliação)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title="Cenário Algoritmo ABC")
    plt.tight_layout()
    plt.savefig(pasta_saida / "2_Score_Por_Variacao_TP.png")
    plt.close()

    # 3. MATRIZ DE DECISÃO (TRADE-OFF SCORE x TEMPO)
    df_tradeoff = df.groupby('Cenario')[['Tempo_Execucao_ms', 'Score']].mean().reset_index()
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_tradeoff, x="Tempo_Execucao_ms", y="Score", hue="Cenario", s=300, palette="Set1", edgecolor='black')
    
    # Rótulos nos pontos
    for i in range(df_tradeoff.shape[0]):
        plt.text(df_tradeoff.Tempo_Execucao_ms[i], df_tradeoff.Score[i] + 0.005, df_tradeoff.Cenario[i], 
                 horizontalalignment='center', size='medium', weight='semibold')

    plt.title("Matriz de Decisão Geral: Tempo de Execução vs Score", fontsize=14, weight='bold')
    plt.xlabel("Tempo Médio de Processamento (ms)")
    plt.ylabel("Qualidade Geral (Score Médio)")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(pasta_saida / "3_Matriz_Decisao_Tradeoff.png")
    plt.close()

    # 4. VALIDAÇÃO DOS PESOS (Comprova se o algoritmo obedeceu aos objetivos)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    sns.barplot(data=df, x="Variacao_TP", y="Disponibilidade", ax=axes[0], hue="Variacao_TP", palette="Blues", legend=False)
    axes[0].set_title("Disponibilidade\n(O TPa deveria ser o maior aqui)", weight='bold')

    sns.barplot(data=df, x="Variacao_TP", y="Custo", ax=axes[1], hue="Variacao_TP", palette="Reds", legend=False)
    axes[1].set_title("Custo\n(O TPc deveria ser o menor aqui)", weight='bold')

    sns.barplot(data=df, x="Variacao_TP", y="Tempo_Resposta", ax=axes[2], hue="Variacao_TP", palette="Greens", legend=False)
    axes[2].set_title("Tempo de Resposta\n(O TPr deveria ser o menor aqui)", weight='bold')

    plt.tight_layout()
    plt.savefig(pasta_saida / "4_Validacao_Metricas_Pesos.png")
    plt.close()
    
    print("🚀 Todos os gráficos foram criados na pasta 'Resultados_Graficos_TP'!")

if __name__ == '__main__':
    gerar_graficos_analise()