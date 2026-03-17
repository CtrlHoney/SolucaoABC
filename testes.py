                # ========================================================================
                # CENÁRIOS DE TESTE DE PARÂMETROS DO ABC (CALIBRAÇÃO)
                # ========================================================================
                
                # --- CENÁRIO 1: O Padrão / Equilibrado ---
                # Por que usar: Oferece um meio-termo sólido entre tempo de resposta e qualidade da solução.
                # Geralmente é a linha de base para comparar com o ACO.
                # iteMax = 50
                # nBees = 20
                # limit = 20
                
                # --- CENÁRIO 2: Exploração Agressiva (Ambientes Complexos) ---
                # Por que usar: Ideal para quando você tem MUITOS provedores (ex: ProvidersACOKP100-10.json).
                # Como o limit é baixo (10), as abelhas escoteiras são ativadas rapidamente se a solução não melhorar,
                # forçando o algoritmo a saltar para áreas totalmente novas do espaço de busca.
                # iteMax = 50
                # nBees = 40
                # limit = 10
                
                # --- CENÁRIO 3: Explotação Profunda (Ajuste Fino) ---
                # Por que usar: Útil quando as restrições de Custo/Disponibilidade são muito apertadas.
                # Damos mais tempo (100 iterações) e um limit alto (40), permitindo que as abelhas
                # explorem exaustivamente os vizinhos das soluções que já são boas, refinando o Score ao máximo.
                # iteMax = 100
                # nBees = 20
                # limit = 40
                
                # --- CENÁRIO 4: Execução de Baixo Custo (Real-Time) ---
                # Por que usar: Se o objetivo do seu TCC for provar que a seleção pode ser feita "em tempo real"
                # (em poucos milissegundos) para microsserviços dinâmicos, este cenário brilha.
                # Ele sacrifica um pouco o Score perfeito em troca de extrema velocidade.
                # iteMax = 25 
                # nBees = 10
                # limit = 15

                # --- CENÁRIO 5: Enxame Massivo (Força Bruta Otimizada) ---
                # Por que usar: Para descobrir qual é o limite máximo de pontuação (Score) absoluto
                # que o algoritmo consegue atingir, não importando quanto tempo demore.
                # iteMax = 150
                # nBees = 50
                # limit = 30
                # ========================================================================