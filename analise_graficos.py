import os
import re
import matplotlib.pyplot as plt
import pandas as pd

def analisar_resultados():
    pastas = [p for p in os.listdir('.') if os.path.isdir(p) and p.startswith('Resultados_parametros')]
    
    if not pastas:
        print("Nenhuma pasta de resultados encontrada!")
        return

    dados_consolidados = []

    for pasta in pastas:
        # Extrair dados do nome da pasta (Ex: Resultados_parametrosApa1-3)
        match = re.search(r'Ap([a-zA-Z]+)(\d+)-(\d+)', pasta)
        if not match: continue
        
        variante, num_app, test_id = match.groups()
        
        # Ler Tempos de Execucao
        tempos = []
        for ficheiro in os.listdir(pasta):
            if ficheiro.startswith('executionTime'):
                with open(os.path.join(pasta, ficheiro), 'r') as f:
                    linhas = f.readlines()
                    for linha in linhas:
                        if linha.strip().isdigit():
                            tempos.append(int(linha.strip()))
        
        # Ler Scores
        scores = []
        for ficheiro in os.listdir(pasta):
            if ficheiro.startswith('resultData'):
                with open(os.path.join(pasta, ficheiro), 'r') as f:
                    conteudo = f.read()
                    # A regex captura o valor após "Socre = "
                    matches_score = re.findall(r'Socre\s*=\s*([\d\.]+)', conteudo)
                    scores.extend([float(s) for s in matches_score])

        if tempos and scores:
            media_tempo = sum(tempos) / len(tempos)
            media_score = sum(scores) / len(scores)
            
            dados_consolidados.append({
                'App': f"App{num_app}-{variante}",
                'Teste': f"Param {test_id}",
                'Score': media_score,
                'Tempo (ms)': media_tempo
            })

    if not dados_consolidados:
        print("Nenhum dado legível nos .txt!")
        return

    df = pd.DataFrame(dados_consolidados)
    apps_unicas = df['App'].unique()

    # Gerar Gráficos para cada Aplicação
    for app in apps_unicas:
        df_app = df[df['App'] == app].sort_values(by='Teste')
        
        fig, ax1 = plt.subplots(figsize=(10, 6))

        # Eixo do Score
        color = 'tab:blue'
        ax1.set_xlabel('Cenário de Parâmetros', fontweight='bold')
        ax1.set_ylabel('Score (Maior = Melhor)', color=color, fontweight='bold')
        barras = ax1.bar(df_app['Teste'], df_app['Score'], color=color, alpha=0.7, label='Score Médio')
        ax1.tick_params(axis='y', labelcolor=color)

        # Eixo do Tempo (Eixo Y Secundário)
        ax2 = ax1.twinx()  
        color = 'tab:red'
        ax2.set_ylabel('Tempo Execução (ms) (Menor = Melhor)', color=color, fontweight='bold')
        linha = ax2.plot(df_app['Teste'], df_app['Tempo (ms)'], color=color, marker='o', linewidth=3, label='Tempo Médio (ms)')
        ax2.tick_params(axis='y', labelcolor=color)

        plt.title(f'Comparação de Parâmetros ABC - {app}', fontsize=14)
        fig.tight_layout()
        
        nome_grafico = f"Grafico_{app}.png"
        plt.savefig(nome_grafico)
        print(f"Gráfico gerado com sucesso: {nome_grafico}")

if __name__ == "__main__":
    analisar_resultados()