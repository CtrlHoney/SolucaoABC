#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask
import time
import json
import itertools
import random
import os

app = Flask(__name__)

# ========================================================================
# CONFIGURAÇÕES DE DIRETÓRIOS E ESTEIRA DE TESTES
# ========================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(BASE_DIR, 'JSON-ApproachACOKP-2GG')
PASTA_SAIDA = os.path.join(BASE_DIR, "Testes_Estresse_Escalonado")

if not os.path.exists(PASTA_SAIDA):
    os.makedirs(PASTA_SAIDA)

# Aplicações a serem testadas (1 a 5, usando 'ability' como padrão de complexidade)
apps_range = range(1, 6)
variacao = "ability"

# Níveis de Estresse (Do menor arquivo até o 100-10)
niveis_estresse = [
    {"id": "01_Prov05", "prov": "ProvidersACOKP5-5.json", "links": "linksProviders5.json"},
    {"id": "02_Prov10", "prov": "ProvidersACOKP10-10.json", "links": "linksProviders10.json"},
    {"id": "03_Prov15", "prov": "ProvidersACOKP15-10.json", "links": "linksProviders15.json"},
    {"id": "04_Prov20", "prov": "ProvidersACOKP20-20.json", "links": "linksProviders20.json"},
    {"id": "05_Prov25", "prov": "ProvidersACOKP25-10.json", "links": "linksProviders25.json"},
    {"id": "06_Prov30", "prov": "ProvidersACOKP30-10.json", "links": "linksProviders30.json"},
    {"id": "07_Prov100", "prov": "ProvidersACOKP100-10.json", "links": "linksProviders100.json"}
]

# Parâmetros Padrão do ABC
ITE_MAX = 50
N_BEES = 20
LIMIT = 20

# Globais nativas
listaCandGeral = []
listaCandEsp = []
qtdALlSerPrvd = []
qtdAllCombPrvd = []

# ========================================================================
# MÉTODOS DO ALGORITMO
# ========================================================================
def calcNumofMS(nameMS):
    numofMS = ""
    for i in range(len(nameMS)-1):
        if (nameMS[i] in ["0","1","2","3","4","5","6","7","8","9"]):
            numofMS += nameMS[i]
    return int(numofMS)

def calcProfit(terms,MatLinks,priorities,totalCost,appAva,appRT):
    profit = 0.0
    avaTerms = 1
    rtTerms = 0
    costTerms = 0
    for term in terms:
        avaFlows = 0
        rtFlows = 0
        costFlows = 0
        for (eachFlow,links,prob) in term:
            ava = 1
            rt = 0
            cost = 0
            msAnalyzed = []
            for eachComb in eachFlow:
                if (not eachComb[2] in msAnalyzed):
                    ava *= (eachComb[0][0][1])/100 
                    rt += eachComb[0][0][2]
                    cost += eachComb[0][1]
                    msAnalyzed.append(eachComb[2])
              
            for i in range(len(links)-1):
              for link_item in MatLinks:
                 if not link_item: continue # CORREÇÃO DE LISTA VAZIA
                 link = link_item[0] if isinstance(link_item, list) else link_item
                 if(link['out'] == links[i] and link['in'] == links[i+1]): 
                   ava *= link['availability']/100
                   rt += link['delay']
                   cost += link['cost']
           
            avaFlows += (ava * prob)   
            rtFlows += (rt * prob)
            costFlows += (cost * prob)
        avaTerms *= round(avaFlows,2)
        rtTerms += rtFlows
        costTerms += costFlows 
    avaTerms = round(avaTerms*100,2)   
   
    if(avaTerms >= appAva and rtTerms <= appRT and costTerms <= totalCost):
        profit = round(( ((totalCost - costTerms)/totalCost) * priorities[1] + ((avaTerms - appAva)/appAva) * priorities[2] + ((appRT - rtTerms)/appRT) * priorities[0]),4)

    return (profit,avaTerms,rtTerms,costTerms)

def decode_solution(indices, seqFlowsMS, MatIn):
    sAnt = []
    for eachTerm in seqFlowsMS:
        sTerm = []
        for eachFlow in eachTerm[1]:
            sFlow = []
            links = []
            for i,eachMS in enumerate(eachFlow[2]):
                j = calcNumofMS(eachMS[0]) - 1
                posComb = indices[j]
                comb = MatIn[j][posComb]
                links.append(comb[2])
                sFlow.append((comb,posComb,j))
            sTerm.append((sFlow,links,eachFlow[1]))
        sAnt.append(sTerm)
    return sAnt

def abcKnapSack(MatIn, totalCost, appAva, appRT, iteMax, nBees, limit, seqFlowsMS, MatLinks, priorities):
    num_ms = len(MatIn)
    n_fontes = nBees // 2
    fontes = []
    fitness = []
    falhas = [0] * n_fontes
    melhor_sAPP = [([], 0.0)]
    
    for i in range(n_fontes):
        sol = [random.randint(0, len(MatIn[j])-1) for j in range(num_ms)]
        sAnt = decode_solution(sol, seqFlowsMS, MatIn)
        prof, ava, rt, cost = calcProfit(sAnt, MatLinks, priorities, totalCost, appAva, appRT)
        fontes.append(sol)
        fitness.append(prof)
        if prof > 0.0:
            if melhor_sAPP == [([], 0.0)] or prof > melhor_sAPP[0][1]:
                melhor_sAPP = [(sAnt, prof, ava, rt, cost)]

    for ite in range(iteMax):
        for i in range(n_fontes):
            nova_sol = list(fontes[i])
            ms_idx = random.randint(0, num_ms - 1)
            nova_sol[ms_idx] = random.randint(0, len(MatIn[ms_idx]) - 1)
            sAnt = decode_solution(nova_sol, seqFlowsMS, MatIn)
            prof, ava, rt, cost = calcProfit(sAnt, MatLinks, priorities, totalCost, appAva, appRT)
            if prof > fitness[i]:
                fontes[i] = nova_sol
                fitness[i] = prof
                falhas[i] = 0
                if prof > 0.0 and (melhor_sAPP == [([], 0.0)] or prof > melhor_sAPP[0][1]):
                    melhor_sAPP = [(sAnt, prof, ava, rt, cost)]
            else: falhas[i] += 1
                
        total_fit = sum(fitness)
        probs = [1.0 / n_fontes] * n_fontes if total_fit == 0 else [f / total_fit for f in fitness]
            
        for _ in range(n_fontes):
            r = random.random()
            acum = 0.0
            idx_escolhido = n_fontes - 1
            for idx, p in enumerate(probs):
                acum += p
                if r <= acum:
                    idx_escolhido = idx
                    break
            nova_sol = list(fontes[idx_escolhido])
            ms_idx = random.randint(0, num_ms - 1)
            nova_sol[ms_idx] = random.randint(0, len(MatIn[ms_idx]) - 1)
            sAnt = decode_solution(nova_sol, seqFlowsMS, MatIn)
            prof, ava, rt, cost = calcProfit(sAnt, MatLinks, priorities, totalCost, appAva, appRT)
            if prof > fitness[idx_escolhido]:
                fontes[idx_escolhido] = nova_sol
                fitness[idx_escolhido] = prof
                falhas[idx_escolhido] = 0
                if prof > 0.0 and (melhor_sAPP == [([], 0.0)] or prof > melhor_sAPP[0][1]):
                    melhor_sAPP = [(sAnt, prof, ava, rt, cost)]
            else: falhas[idx_escolhido] += 1
                
        for i in range(n_fontes):
            if falhas[i] > limit:
                fontes[i] = [random.randint(0, len(MatIn[j])-1) for j in range(num_ms)]
                sAnt = decode_solution(fontes[i], seqFlowsMS, MatIn)
                prof, ava, rt, cost = calcProfit(sAnt, MatLinks, priorities, totalCost, appAva, appRT)
                fitness[i] = prof
                falhas[i] = 0
                if prof > 0.0 and (melhor_sAPP == [([], 0.0)] or prof > melhor_sAPP[0][1]):
                    melhor_sAPP = [(sAnt, prof, ava, rt, cost)]

    return melhor_sAPP

def minCapabilities(capabilitiesSr,capabilitiesPr):
    if (not capabilitiesPr and not capabilitiesSr): return True
    if (capabilitiesPr[0]['CPU'] >= capabilitiesSr[0]['CPU'] and capabilitiesPr[0]['Core'] >= capabilitiesSr[0]['Core'] and capabilitiesPr[0]['RAM'] >= capabilitiesSr[0]['RAM'] and capabilitiesPr[0]['HD'] >= capabilitiesSr[0]['HD']): return True
    return False

def discovery(service,provider):
    lista = []
    for pr in provider['servicesClass']:
       if (service['nameCl'] == pr['nameCl']):
           for srPr in pr['services']:
               if (service['functionality'] == srPr['functionality']):
                   if (minCapabilities(service['capabilities'], srPr['capabilities'])):
                           lista.append(srPr)
    return lista

def servicosCandidatosMS(microservice,dataPrvd):
   candidatesPrSr = []
   listaTeste = []
   global qtdALlSerPrvd
   for pr in dataPrvd:
       candidateSr = []
       for sr in microservice['services']: 
           discovList = discovery(sr,pr)
           if (discovList != [{}] and discovList != []): candidateSr.append((sr['nameSr'],discovList))
           else: 
               candidateSr.clear()
               break
         
       if (candidateSr != []):
           total = 0
           qtdALlSerPrvd.append((pr['provider'],microservice['nameMS'], len(candidateSr)))
           for listaSr in candidateSr: total += len(listaSr)
           listaTeste.append((pr['provider'], total))
           candidatesPrSr.append((pr['provider'],microservice['nameMS'],candidateSr))     
   return (candidatesPrSr,listaTeste)

def maximum(srL,req): return max([sr['userRequirements'][0][req] for sr in srL] + [0])
def minimum(srL,req): return min([sr['userRequirements'][0][req] for sr in srL] + [100000])
def maximumRespTime(srL,req1,req2): return max([sr['userRequirements'][0][req1] + sr['userRequirements'][0][req2] for sr in srL] + [0])
def minimumRespTime(srL,req1,req2): return min([sr['userRequirements'][0][req1] + sr['userRequirements'][0][req2] for sr in srL] + [10000])

def saw1(adqSrlist):
    vAllSr = []
    for srL in adqSrlist:
        aRqMax = maximum(srL[1],'availability')
        aRqMin = minimum(srL[1],'availability')
        rtRqMax = maximumRespTime(srL[1],'executionTime','delay')
        rtRqMin = minimumRespTime(srL[1],'executionTime','delay')
        cRqMax = maximum(srL[1],'cost')
        cRqMin = minimum(srL[1],'cost')
        vSr = []
        for sr in srL[1]:
            aSr = 1.0 if aRqMax == aRqMin else round((sr['userRequirements'][0]['availability'] - aRqMin) / (aRqMax - aRqMin),3)
            rtSr = 1.0 if rtRqMax == rtRqMin else round((rtRqMax - (sr['userRequirements'][0]['executionTime'] + sr['userRequirements'][0]['delay'])) / (rtRqMax - rtRqMin),3)
            cSr = 1.0 if cRqMax == cRqMin else round((sr['userRequirements'][0]['cost'] - cRqMin) / (cRqMax - cRqMin),3)
            vSr.append((aSr,rtSr,cSr))
        vAllSr.append(vSr)
    return vAllSr

def saw2(adqSrlist, vReq, weights):
    scoreAllList = []
    for candReq,candSr in zip(vReq, adqSrlist):
        scoreSrList = []
        for srReq,Sr in zip(candReq,candSr[1]):
            score = sum(round((srReq[i] * weights[i]),3) for i in range(len(srReq)))
            scoreSrList.append((Sr,score))    
        scoreAllList.append(scoreSrList) 
    return scoreAllList    

def avbComb(flow,prob):
    av = 1
    for serv in flow: av *= (serv[0][0]['userRequirements'][0]['availability']/100)
    av *= prob * (serv[1][0]['ava']/100)
    return round((av*100),2)

def rtComb(flow,prob):
    rt = sum(serv[0][0]['userRequirements'][0]['executionTime'] + serv[0][0]['userRequirements'][0]['delay'] for serv in flow)
    return (rt * prob) + flow[-1][1][0]['delay']

def costComb(flow,prob):
    cost = sum(serv[0][0]['userRequirements'][0]['cost'] for serv in flow)
    return (cost * prob) + flow[-1][1][0]['cost']

def calcScore(flow,probability): return sum(eachMS[0][1] for eachMS in flow) * probability

def calcNumServ(nameServ): return int("".join(c for c in nameServ if c.isdigit()))

def combinationsSr(serCadPrv,nameMS,namePr,costAPP,avbtyAPP,rspTmAPP,seqFlow):
    combList = []
    combs = list(itertools.product(*serCadPrv))
    for comb in combs:
        costMS, avlbtyMS, respTmMS, scoreMS = 0, 1, 0, 0
        for eachTerm in seqFlow:
          avlbty, cost, respTm, score = 0, 0, 0, 0
          for eachFlow in eachTerm[1]:
            flow = []
            probability = eachFlow[1]
            for eachServ in eachFlow[2]:
                numofMS = calcNumServ(eachServ[0][-1]) - 1
                flow.append((comb[numofMS],eachServ[1])) 
            cost += costComb(flow,probability)
            avlbty += avbComb(flow,probability)
            respTm += rtComb(flow,probability)
            score += calcScore(flow,probability)
          costMS += cost
          avlbtyMS *= (avlbty/100)
          respTmMS += respTm
          scoreMS += score
        avlbtyMS = round((avlbtyMS*100),2)    
        if (costMS <= costAPP and avlbtyMS >= avbtyAPP and respTmMS <= rspTmAPP):
            combList.append(((nameMS,namePr,comb,costMS,avlbtyMS,respTmMS),round(scoreMS,2)))
    return combList     

def calcNumofPrvds(nameLinks):
   numofPrvd = ""
   for i in range(1,len(nameLinks)):
       if (nameLinks[i].isdigit() and nameLinks[i-1] != "-"): numofPrvd += nameLinks[i]
   return int(numofPrvd) if numofPrvd else 1

def cloudsSelection(app, dataAMS, dataPrvd, iteApp):
   combMSPr = []
   global qtdAllCombPrvd
   for ms in app['microservices']:
       combListSr = []
       combPr = []
       srCandMS = servicosCandidatosMS(ms,dataPrvd)
       iteMS =  [item['terms'] for item in iteApp[0]['iterationsMS']  if (item['microservice'] == ms['nameMS'])]    
       termsApp = [(term['nameTerm'],[term['sequences']]) for term in iteMS[0]]   
       seqFlow = [(term[0],[(flow['nameseq'],flow['probability'],[(seq['service'],seq['linksInput']) for seq in flow['dataSeq']])  for flow in term[1][0]]) for term in termsApp ]

       for srCad in srCandMS[0]:
           if (srCad[2]):
              vReq = saw1(srCad[2])
              scAllList = saw2(srCad[2], vReq,app['weights'])
              combListSr = combinationsSr(scAllList,srCad[1],srCad[0],app['cost'],app['availability'],app['responseTime'],seqFlow)
              if(len(combListSr)>0):
                   qtdAllCombPrvd.append((srCad[0],ms['nameMS'],len(combListSr)))
                   combPr.append(list(combListSr))
       if (combPr): combMSPr.append(combPr)
   return (combMSPr, app['cost'],app['availability'],app['responseTime'],app['weights'])

def removeMS(flow,msData):
    j = 0
    while(j <len(flow[0])):
      nameMs = "MS" + str(flow[0][j][2]+1)
      achou = 0
      for msdata in msData:
        if (nameMs == msdata[0]):
            flow[0].pop(j)
            achou = 1
      if(not achou): j += 1


# ========================================================================
# ORQUESTRAÇÃO DOS TESTES DE ESTRESSE
# ========================================================================

print("\n" + "="*60)
print("🚀 INICIANDO ESTEIRA DE TESTES DE ESTRESSE ESCALONADO")
print("="*60)

for app_id in apps_range:
    
    arq_app = f'Application{app_id}-{variacao}.json'
    arq_ite = f'APP{app_id}-iterations-1.json'
    
    caminho_app = os.path.join(JSON_DIR, arq_app)
    caminho_ite = os.path.join(JSON_DIR, arq_ite)
    
    if not os.path.exists(caminho_app) or not os.path.exists(caminho_ite):
        print(f"\n❌ [AVISO] Arquivos da Aplicação {app_id} não encontrados. Pulando.")
        continue

    print(f"\n========================================================")
    print(f" 📂 INICIANDO BATERIA PARA: APP {app_id} (Variação: {variacao})")
    print(f"========================================================")

    with open(caminho_app) as f: dataAMS = json.load(f)
    with open(caminho_ite) as f: iteApp = json.load(f)
    app_target = dataAMS[0] 

    pasta_app = os.path.join(PASTA_SAIDA, f"APP_{app_id}")

    for nivel in niveis_estresse:
        print(f"\n⏳ Escalonando para: {nivel['id']}...")
        
        pasta_nivel = os.path.join(pasta_app, nivel['id'])
        if not os.path.exists(pasta_nivel): os.makedirs(pasta_nivel)
            
        caminho_prov = os.path.join(JSON_DIR, nivel['prov'])
        caminho_links = os.path.join(JSON_DIR, nivel['links'])
        
        if not os.path.exists(caminho_prov):
            print(f"   [!] JSON {nivel['prov']} não encontrado.")
            continue

        with open(caminho_prov) as f: dataPrvd = json.load(f)
        with open(caminho_links) as f: dataLinks = json.load(f)    

        # Reseta controle interno para não misturar dados
        qtdALlSerPrvd = []
        qtdAllCombPrvd = []
        
        inicio = time.time()
        try:
            # ETAPA 1: Peneira SAW
            totalComb = cloudsSelection(app_target, dataAMS, dataPrvd, iteApp)
          
            if not totalComb[0]:
                fim = time.time()
                FinalTime = int(round(fim - inicio, 3) * 1000)
                print(f"   ⚠️ Corte SAW: Nenhuma combinacao inicial atendeu a SLA ({FinalTime}ms).")
                
                with open(os.path.join(pasta_nivel, "executionTime_Estresse.txt"), 'w') as f:
                    f.write(f"Tempo de execucao (ms):\n{FinalTime}\n")
                with open(os.path.join(pasta_nivel, "resultData_Estresse.txt"), 'w') as f:
                    f.write(f"ESTRESSE APP {app_id} - {nivel['id']}\nFalha SAW: Todas as opcoes foram filtradas.\n")
                continue

            posMS = []
            for comb in totalComb[0]:
                total = sum(len(eachComb) for eachComb in comb)
                if totalComb[0].index(comb) == 0: posMS.append(total)
                else: posMS.append(posMS[-1] + total)
          
            MS = [totalComb[0].index(comb) for comb in totalComb[0] for eachComb in comb for idx in range(len(eachComb))]
            PR = [eachComb[0][0][1] for comb in totalComb[0] for eachComb in comb for idx in range(len(eachComb))]
            Score = [(eachComb[0][1],eachComb[0][0][4],eachComb[0][0][5]) for comb in totalComb[0] for eachComb in comb for idx in range(len(eachComb))]
            Cost = [eachComb[0][0][3] for comb in totalComb[0] for eachComb in comb for idx in range(len(eachComb))]
            
            totalCost, appAva, appRT, priorities = totalComb[1], totalComb[2], totalComb[3], totalComb[4]
            numofPrvds = calcNumofPrvds(nivel['links'])

            MatLinks = [[] for x in range(numofPrvds*(numofPrvds-1))]
            for j,link in enumerate(dataLinks): MatLinks[j] = link
                        
            MatIn = [[] for x in range(len(posMS))]
            for j, item in enumerate(MS): MatIn[item].append((Score[j],Cost[j],PR[j]))
            for k in range(len(MatIn)): MatIn[k].sort(key=lambda x: x[1])

            seqFlowsMS = [(term['nameTerm'],[(flow['nameseq'],flow['probability'],[(seq['microservice'],seq['linksInput']) for seq in flow['dataSeq']]) for flow in term['sequences']]) for term in iteApp[0]['iterationsAPP'] ] 

            # ETAPA 2: Colônia de Abelhas
            sAPP = abcKnapSack(MatIn, totalCost, appAva, appRT, ITE_MAX, N_BEES, LIMIT, seqFlowsMS, MatLinks, priorities)

            fim = time.time()
            FinalTime = int(round(fim - inicio, 3) * 1000)
            
            arq_result = os.path.join(pasta_nivel, "resultData_Estresse.txt")
            arq_tempo = os.path.join(pasta_nivel, "executionTime_Estresse.txt")
            
            with open(arq_tempo, 'w') as f:
                f.write(f"Tempo de execucao (ms):\n{FinalTime}\n")
                
            if sAPP != [([], 0.0)]:
                print(f"   ✅ ABC SUCESSO! Tempo: {FinalTime}ms | Score Final: {sAPP[0][1]}")
                with open(arq_result, 'w') as f:
                    f.write(f"ESTRESSE APP {app_id} - {nivel['id']}\n")
                    f.write(f"APP Data: Availability = {sAPP[0][2]} Response Time = {sAPP[0][3]} Cost = {sAPP[0][4]} Score = {sAPP[0][1]}\n")
            else:
                print(f"   ⚠️ ABC FALHOU: Busca esgotada sem resultados uteis ({FinalTime}ms).")
                with open(arq_result, 'w') as f:
                    f.write(f"ESTRESSE APP {app_id} - {nivel['id']}\n")
                    f.write("Nenhuma rota que batesse as metas de SLA foi encontrada pelas abelhas.\n")

        except Exception as e:
            print(f"❌ [FALHA COMPUTACIONAL] Nível {nivel['id']} quebrou. Erro: {e}")

print("\n🎉 Testes Concluídos! Verifique a pasta 'Testes_Estresse_Escalonado'.")