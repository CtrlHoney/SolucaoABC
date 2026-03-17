# Otimização de Seleção de Serviços em Nuvem para Microserviços via ABC

Este repositório contém o código-fonte desenvolvido para o TCC focado na "Seleção Otimizada de Serviços em Nuvem para Compor Microserviços Fazendo Uso de Algoritmos de Inteligência Coletiva".

A solução converte o desafio num problema MCKP (*Multi-Choice Knapsack Problem*) e resolve-o utilizando o algoritmo **Artificial Bee Colony (ABC)** (Colónia de Abelhas).

## 🗂️ Estrutura de Ficheiros

1. **`provedoresGerador.py`**: Script que gera aleatoriamente ficheiros JSON contendo a simulação de Provedores em Nuvem (como AWS, Azure, GCP). Define instâncias de computação, armazenamento e bases de dados com características técnicas.
2. **`linkGerador.py`**: Gera ficheiros JSON mapeando o custo de comunicação, atraso (delay) e disponibilidade de rede entre diferentes provedores.
3. **`cloudSelection-approach4-8.py`**: O motor principal. Analisa os requisitos da aplicação, filtra candidatos adequados, usa o método multicritério **SAW** (Simple Additive Weighting) para avaliar a qualidade e lança o algoritmo **ABC** para selecionar o melhor serviço para cada microserviço.

## 🛠️ Como Executar o Projeto

**Pré-requisitos:** Python 3 instalado e o pacote `Flask` (pode ser instalado via terminal usando `pip install flask`).

1. Execute `python provedoresGerador.py` para gerar o ficheiro `ProvidersACOKP10-10.json`.
2. Execute `python linkGerador.py` para gerar o ficheiro `linksProviders10.json`.
3. Certifique-se que existe a pasta `./JSON-ApproachACOKP-2GG/` e mova os JSONs gerados para lá, juntamente com os JSONs da aplicação (ex: `Application1-ability.json`).
4. Inicie a otimização executando `python cloudSelection-approach4-8.py`.
5. O terminal exibirá o processo de forrageamento das abelhas e, no fim, serão gerados dois ficheiros na pasta raiz: `resultData...txt` (a configuração final) e `executionTime...txt` (tempo de computação).

## 🧪 Guia de Testes para o TCC (Alteração de Parâmetros)

Para a sua monografia, pode avaliar o comportamento do algoritmo sob diferentes condições. Todas as alterações são feitas dentro do ficheiro `cloudSelection-approach4-8.py`:

### Teste 1: Aumentar as Repetições Estatísticas
Para provar a eficiência e estabilidade do algoritmo num artigo científico, nunca testamos apenas uma vez.
* **Onde alterar:** Procure a variável `repeticoes_experimento = 1` (na linha 281).
* **O que alterar:** Mude para `30` ou `50`. O algoritmo correrá várias vezes para o mesmo cenário e gravará 30 resultados diferentes nos `.txt`, permitindo-lhe calcular médias e desvios padrão do Score e do Tempo de Execução.

### Teste 2: Calibragem do Algoritmo ABC (Tuning)
As capacidades das abelhas são governadas por três parâmetros (linhas 315-317):
* **`iteMax = 50`** (Número de Gerações): Determina quantas vezes a colmeia vai procurar soluções. Aumentar para `100` ou `200` pode encontrar soluções melhores, mas demorará mais tempo.
* **`nBees = 20`** (Tamanho da População): Número total de abelhas. Metade atua como empregadas e metade como observadoras. Se o espaço de busca for muito vasto, aumentar para `50` melhora a exploração em paralelo.
* **`limit = 20`** (Limite de abandono de fonte): O número máximo de tentativas falhadas antes de uma abelha se tornar Escoteira (Scout) e saltar para uma solução aleatória completamente nova. Um limit baixo favorece exploração global (não fica preso em mínimos locais); um limit alto favorece exploração local. Experimente alterar para `10` ou `30`.

### Teste 3: Volume de Provedores na Nuvem (Escalabilidade)
Para avaliar como o tempo de execução aumenta se existirem mais fornecedores no mercado.
1. No ficheiro `provedoresGerador.py`, altere `range(10, 11, 1)` para `range(30, 31, 1)`.
2. No ficheiro `linkGerador.py`, altere `numberOfProviders = 10` para `30`.
3. Gere os novos ficheiros e adicione o caminho `'./JSON-.../ProvidersACOKP30-10.json'` nas listas iniciais `prvd` e `linksPrvd` no início do ficheiro principal.

---
**Nota para a Defesa de Tese:** Ao apresentar o algoritmo ABC, reforce que este tem uma vantagem inerente sobre o antigo ACO (Ant Colony) porque a fase de **Abelhas Escoteiras (Scouts)** evita automaticamente que a solução convirja precocemente para configurações de má qualidade, sem necessidade de calcular complexas taxas de evaporação de feromona.