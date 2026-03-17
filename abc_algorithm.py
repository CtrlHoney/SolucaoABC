import json
import random
import numpy as np

class ABCCloudSelection:
    def __init__(self, candidates_per_ms, constraints, weights, n_bees=30, max_iter=100, limit=20):
        """
        :param candidates_per_ms: Lista de listas de objetos de serviço (do seu JSON)
        :param constraints: {'cost': max_cost, 'availability': min_ava, 'rt': max_rt}
        :param weights: [w_rt, w_cost, w_ava] - Pesos para o Score
        """
        self.candidates = candidates_per_ms
        self.num_ms = len(candidates_per_ms)
        self.constraints = constraints
        self.weights = weights
        self.n_fontes = n_bees // 2
        self.max_iter = max_iter
        self.limit = limit
        
        self.fontes = []
        self.fitness = []
        self.falhas = [0] * self.n_fontes
        
        self.best_sol = None
        self.best_fit = -1

    def calculate_metrics(self, solution):
        """Calcula os valores reais baseados nos userRequirements do gerador"""
        t_cost = 0
        t_rt = 0
        t_ava = 1.0
        t_score = 0

        for ms_idx, s_idx in enumerate(solution):
            servico = self.candidates[ms_idx][s_idx]
            req = servico["userRequirements"][0]
            
            t_cost += req["cost"]
            t_rt += (req["executionTime"] + req["delay"])
            t_ava *= (req["availability"] / 100.0)
            
            # Cálculo de Score simples 
            # RT e Cost (menor é melhor)
            t_score += (100 / (req["cost"] + 1)) * self.weights[1] + \
                       (req["availability"]) * self.weights[2]

        t_ava_percent = t_ava * 100
        
        # Validação de Restrições (Penalty)
        if (t_cost > self.constraints['cost'] or 
            t_ava_percent < self.constraints['availability'] or 
            t_rt > self.constraints['rt']):
            return 0
        
        return round(t_score, 4)

    def generate_neighbor(self, solution):
        new_sol = list(solution)
        ms_idx = random.randint(0, self.num_ms - 1)
        # Escolhe um novo serviço dentro do mesmo grupo de candidatos
        new_sol[ms_idx] = random.randint(0, len(self.candidates[ms_idx]) - 1)
        return new_sol

    def solve(self):
        # Inicialização
        for _ in range(self.n_fontes):
            sol = [random.randint(0, len(self.candidates[i]) - 1) for i in range(self.num_ms)]
            self.fontes.append(sol)
            self.fitness.append(self.calculate_metrics(sol))

        for _ in range(self.max_iter):
            # Fase Abelhas Empregadas
            for i in range(self.n_fontes):
                v = self.generate_neighbor(self.fontes[i])
                fit_v = self.calculate_metrics(v)
                if fit_v > self.fitness[i]:
                    self.fontes[i], self.fitness[i], self.falhas[i] = v, fit_v, 0
                else:
                    self.falhas[i] += 1

            # Fase Abelhas Observadoras
            total_fit = sum(self.fitness)
            probs = [f/total_fit if total_fit > 0 else 1/self.n_fontes for f in self.fitness]
            for _ in range(self.n_fontes):
                i = np.random.choice(range(self.n_fontes), p=probs)
                v = self.generate_neighbor(self.fontes[i])
                fit_v = self.calculate_metrics(v)
                if fit_v > self.fitness[i]:
                    self.fontes[i], self.fitness[i], self.falhas[i] = v, fit_v, 0
                else:
                    self.falhas[i] += 1

            # Fase Abelhas Escoteiras
            for i in range(self.n_fontes):
                if self.falhas[i] > self.limit:
                    self.fontes[i] = [random.randint(0, len(self.candidates[j]) - 1) for j in range(self.num_ms)]
                    self.fitness[i] = self.calculate_metrics(self.fontes[i])
                    self.falhas[i] = 0

            # Update Global Best
            best_idx = np.argmax(self.fitness)
            if self.fitness[best_idx] > self.best_fit:
                self.best_fit = self.fitness[best_idx]
                self.best_sol = list(self.fontes[best_idx])

        return self.best_sol, self.best_fit

# --- Exemplo de carregamento dos dados do seu gerador ---

def main():
    # Supondo que você gerou o arquivo 'ProvidersACOKP100-10.json'
    try:
        with open('ProvidersACOKP100-10.json', 'r') as f:
            providers = json.load(f)
    except FileNotFoundError:
        print("Gere o arquivo JSON primeiro!")
        return

    # Mapeando candidatos para uma App de 3 Microserviços (Compute, Storage, Database)
    # Filtrando os serviços que existem em todos os provedores
    ms_groups = [[], [], []]
    for p in providers:
        ms_groups[0].extend(p["servicesClass"][0]["services"]) # Compute
        ms_groups[1].extend(p["servicesClass"][1]["services"]) # Storage
        ms_groups[2].extend(p["servicesClass"][2]["services"]) # Database

    constraints = {'cost': 60, 'availability': 95.0, 'rt': 15} 
    weights = [0.3, 0.3, 0.4] # RT, Cost, Availability 

    abc = ABCCloudSelection(ms_groups, constraints, weights)
    best_sol, score = abc.solve()

    if score > 0:
        print("--- Melhor Solução Encontrada ---")
        for i, s_idx in enumerate(best_sol):
            servico = ms_groups[i][s_idx]
            print(f"MS {i+1}: {servico['nameSer']} | Custo: {servico['userRequirements'][0]['cost']}")
        print(f"Score Final: {score}")
    else:
        print("Nenhuma solução atendeu às restrições.")

if __name__ == "__main__":
    main()