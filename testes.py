#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 11:23:13 2018
Adaptado para ABC (Artificial Bee Colony) - Automação de Cenários e Aplicações
"""

from flask import Flask
import time
import json
import itertools
import random

app = Flask(__name__)

import os

# 1. Descobre a pasta exata onde este arquivo Python está salvo (ex: a pasta HoneyABC)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Constrói o caminho completo até a pasta dos arquivos JSON
JSON_DIR = os.path.join(BASE_DIR, 'JSON-ApproachACOKP-2GG')

# 3. Atualiza os caminhos iniciais usando a nova variável JSON_DIR
prvd = [os.path.join(JSON_DIR, 'ProvidersACOKP10-10.json')]
linksPrvd = [os.path.join(JSON_DIR, 'linksProviders10.json')]

# ========================================================================
# CONFIGURAÇÃO DOS CENÁRIOS E APLICAÇÕES
# ========================================================================

cenarios = [
    {"id": 1, "nome": "Padrao", "iteMax": 50, "nBees": 20, "limit": 20},
    {"id": 2, "nome": "Exploracao_Agressiva", "iteMax": 50, "nBees": 40, "limit": 10},
    {"id": 3, "nome": "Explotacao_Profunda", "iteMax": 100, "nBees": 20, "limit": 40},
    {"id": 4, "nome": "Baixo_Custo", "iteMax": 25, "nBees": 10, "limit": 15},
    {"id": 5, "nome": "Enxame_Massivo", "iteMax": 150, "nBees": 50, "limit": 30}
]

apps_range = range(1, 6) # Aplicações de 1 a 5
variacoes = {
    'ability': 'a',
    'cost': 'c',
    'rt': 'r',
    'acr': 'acr'
}

##################################### METODOS JSON PARA PROVIDERS e APPLICATIONS ##################################################

count = 0
listaTeste = []
listaCandGeral = []
listaCandEsp = []

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
                 
                 # 1. Ignora posições vazias (As listas vazias geradas na inicialização)
                 if not link_item: 
                     continue
                 
                 # 2. Desencapsula caso o JSON traga a propriedade dentro de uma lista
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

#################### ALGORITMO ABC ####################
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
    
    # Inicialização
    for i in range(n_fontes):
        sol = [random.randint(0, len(MatIn[j])-1) for j in range(num_ms)]
        sAnt = decode_solution(sol, seqFlowsMS, MatIn)
        prof, ava, rt, cost = calcProfit(sAnt, MatLinks, priorities, totalCost, appAva, appRT)
        fontes.append(sol)
        fitness.append(prof)
        
        if prof > 0.0:
            if melhor_sAPP == [([], 0.0)] or prof > melhor_sAPP[0][1]:
                melhor_sAPP = [(sAnt, prof, ava, rt, cost)]

    # Loop Principal
    for ite in range(iteMax):
        # Fase Empregadas
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
            else:
                falhas[i] += 1
                
        # Fase Observadoras
        total_fit = sum(fitness)
        if total_fit == 0:
            probs = [1.0 / n_fontes] * n_fontes
        else:
            probs = [f / total_fit for f in fitness]
            
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
            else:
                falhas[idx_escolhido] += 1
                
        # Fase Escoteiras
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

#################### MÉTODOS DE DESCOBERTA E SAW ####################
    
def minCapabilities(capabilitiesSr,capabilitiesPr):
    if (not capabilitiesPr and not capabilitiesSr):
        adequate = True
    else:
        if (capabilitiesPr[0]['CPU'] >= capabilitiesSr[0]['CPU'] and capabilitiesPr[0]['Core'] >= capabilitiesSr[0]['Core'] and capabilitiesPr[0]['RAM'] >= capabilitiesSr[0]['RAM'] and capabilitiesPr[0]['HD'] >= capabilitiesSr[0]['HD']):
            adequate = True
        else: adequate = False
    return adequate

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
   for pr in dataPrvd:
       candidateSr = []
       for sr in microservice['services']: 
           discovList = discovery(sr,pr)
           if (discovList != [{}] and discovList != []):
               candidateSr.append((sr['nameSr'],discovList))
           else: 
               candidateSr.clear()
               break
         
       if (candidateSr != []):
           total = 0
           global qtdALlSerPrvd # Declarando para atualizar corretamente no novo escopo aninhado
           qtdALlSerPrvd.append((pr['provider'],microservice['nameMS'], len(candidateSr)))
           for listaSr in candidateSr:
               total += len(listaSr)
           listaTeste.append((pr['provider'], total))
           candidatesPrSr.append((pr['provider'],microservice['nameMS'],candidateSr))     
     
   return (candidatesPrSr,listaTeste)

def maximum(srL,req):
    reqMax = 0
    for sr in srL:
        if (sr['userRequirements'][0][req] > reqMax):
            reqMax = sr['userRequirements'][0][req]
    return reqMax        
    
def minimum(srL,req):
    reqMin = 100000
    for sr in srL:
        if (sr['userRequirements'][0][req] < reqMin):
            reqMin = sr['userRequirements'][0][req]
    return reqMin        

def maximumRespTime(srL,req1,req2):
    reqMax = 0
    for sr in srL:
        responseTime = sr['userRequirements'][0][req1] + sr['userRequirements'][0][req2]
        if (responseTime > reqMax):
            reqMax = responseTime
    return reqMax        

def minimumRespTime(srL,req1,req2):
    reqMin = 10000
    for sr in srL:
        responseTime = sr['userRequirements'][0][req1] + sr['userRequirements'][0][req2]
        if ( responseTime < reqMin):
            reqMin =  responseTime
    return reqMin

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
            if (aRqMax == aRqMin):
                aSr = 1.0
            else: aSr = round((sr['userRequirements'][0]['availability'] - aRqMin) / (aRqMax - aRqMin),3)
            
            if (rtRqMax == rtRqMin):
                rtSr = 1.0
            else: rtSr = round((rtRqMax - (sr['userRequirements'][0]['executionTime'] + sr['userRequirements'][0]['delay'])) / (rtRqMax - rtRqMin),3)
            
            if (cRqMax == cRqMin):
                cSr = 1.0
            else: cSr = round((sr['userRequirements'][0]['cost'] - cRqMin) / (cRqMax - cRqMin),3)
            vSr.append((aSr,rtSr,cSr))
        vAllSr.append(vSr)
    return vAllSr

def saw2(adqSrlist, vReq, weights):
    scoreAllList = []
    for candReq,candSr in zip(vReq, adqSrlist):
        scoreSrList = []
        for srReq,Sr in zip(candReq,candSr[1]):
            score = 0
            for i in range(len(srReq)):
                score += round((srReq[i] * weights[i]),3)
            scoreSrList.append((Sr,score))    
        scoreAllList.append(scoreSrList) 
    return scoreAllList    

def avbComb(flow,prob):
    av = 1
    for serv in flow:
        sr = serv[0][0]
        av *= (sr['userRequirements'][0]['availability']/100)
    av *= prob
    av *= serv[1][0]['ava']/100
    av = round((av*100),2)
    return av

def rtComb(flow,prob):
    rt = 0
    for serv in flow:
        sr = serv[0][0]
        rt += sr['userRequirements'][0]['executionTime'] + sr['userRequirements'][0]['delay']
    rt *= prob  
    rt += serv[1][0]['delay']
    return rt  

def costComb(flow,prob):
    cost = 0
    for serv in flow:
        sr = serv[0][0]
        cost += sr['userRequirements'][0]['cost']
    cost *= prob
    cost += serv[1][0]['cost']    
    return cost    

def calcScore(flow,probability):
    score = 0
    for eachMS in flow:
       score += eachMS[0][1]
    score *= probability
    return score

def calcNumServ(nameServ):
   numofSr = ""
   for i in range(len(nameServ)):
       if (nameServ[i] in ["0","1","2","3","4","5","6","7","8","9"]):
           numofSr += nameServ[i] 
   return int(numofSr)

def combinationsSr(serCadPrv,nameMS,namePr,costAPP,avbtyAPP,rspTmAPP,seqFlow):
    combList = []
    combs = list(itertools.product(*serCadPrv))
    for comb in combs:
        costMS = 0
        avlbtyMS = 1
        respTmMS  = 0
        scoreMS = 0
        for eachTerm in seqFlow:
          avlbty = 0
          cost = 0
          respTm = 0
          score = 0
        
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

    return (combList)     

def calcNumofPrvds(nameLinks):
   numofPrvd = ""
   for i in range(1,len(nameLinks)):
       if (nameLinks[i] in ["0","1","2","3","4","5","6","7","8","9"] and nameLinks[i-1] != "-"):
           numofPrvd += nameLinks[i]
   return int(numofPrvd) 

def cloudsSelection(nameApp,dataAMS,dataPrvd):
   app = [ app for app in dataAMS if (app['app'] == nameApp['app']) ]
   combMSPr = []
   global qtdAllCombPrvd

   for ms in app[0]['microservices']:
       combListSr = []
       combAvgList = []
       combPr = []
       listaTesteEsp = []
  
       srCandMS = servicosCandidatosMS(ms,dataPrvd)
       listaCandGeral.append((ms['nameMS'],srCandMS[1]))
 
       iteMS =  [item['terms'] for item in iteApp[0]['iterationsMS']  if (item['microservice'] == ms['nameMS'])]    
       termsApp = [(term['nameTerm'],[term['sequences']]) for term in iteMS[0]]   
       seqFlow = [(term[0],[(flow['nameseq'],flow['probability'],[(seq['service'],seq['linksInput']) for seq in flow['dataSeq']])  for flow in term[1][0]]) for term in termsApp ]

       for srCad in srCandMS[0]:
           combListSr = []
           if (srCad[2]):
              vReq = saw1(srCad[2])
              scAllList = saw2(srCad[2], vReq,app[0]['weights'])
              combListSr = combinationsSr(scAllList,srCad[1],srCad[0],app[0]['cost'],app[0]['availability'],app[0]['responseTime'],seqFlow)
              
              if(len(combListSr)>0):
                   qtdAllCombPrvd.append((srCad[0],ms['nameMS'],len(combListSr)))
                   combAvgList = list(combListSr)
         
           if (combAvgList):
             combPr.append(combAvgList)       
       listaCandEsp.append((ms['nameMS'],listaTesteEsp))
      
       if (combPr):
         combMSPr.append(combPr)
  
   return (combMSPr, app[0]['cost'],app[0]['availability'],app[0]['responseTime'],app[0]['weights'])

def removeMS(flow,msData):
    j = 0
    while(j <len(flow[0])):
      nameMs = "MS" + str(flow[0][j][2]+1)
      achou = 0
      for msdata in msData:
        if (nameMs == msdata[0]):
            flow[0].pop(j)
            achou = 1
      if(not achou):
          j += 1


######### LOOP PRINCIPAL DE TESTES ORQUESTRADOS #########

for app_num in apps_range:
    for var_full, var_short in variacoes.items():
        
        # Constrói o path dos arquivos dinamicamente baseado na localização real
        nameApp = os.path.join(JSON_DIR, f'Application{app_num}-{var_full}.json')
        nameInte = os.path.join(JSON_DIR, f'APP{app_num}-iterations-1.json')
        
        # Segurança contra arquivos não existentes no sistema
        if not os.path.exists(nameApp) or not os.path.exists(nameInte):
            print(f"[AVISO] Arquivos não encontrados para APP{app_num} ({var_full}). Pulando...")
            # print(f"Caminho tentado: {nameApp}") # Descomente esta linha se quiser ver o caminho que ele tentou buscar
            continue
            
        with open(nameApp) as json_data_file:
            dataAMS = json.load(json_data_file)
        
        with open(nameInte) as json_data_file:
            iteApp = json.load(json_data_file)
            
        for app in dataAMS:
            for namePrvd, nameLinks in zip(prvd, linksPrvd):
                
                with open(namePrvd) as json_data_file:
                    dataPrvd = json.load(json_data_file)
                with open(nameLinks) as json_data_file:
                    dataLinks = json.load(json_data_file)    
                
                # Executa os testes iterando pelos 5 cenários calibrados
                for cenario in cenarios:
                    print(f"\n========================================================")
                    print(f" Iniciando testes: APP {app_num} | Var: {var_full} | Cenário: {cenario['nome']}")
                    print(f"========================================================")
                    
                    # Cria a estrutura de pastas: TPAppX / TPy / CenarioZ
                    pasta_app = f"TPApp{app_num}"
                    pasta_var = os.path.join(pasta_app, f"TP{var_short}")
                    PASTA_RESULTADOS = os.path.join(pasta_var, f"Cenario{cenario['id']}_{cenario['nome']}")
                    
                    if not os.path.exists(PASTA_RESULTADOS):
                        os.makedirs(PASTA_RESULTADOS)
                        
                    timeList = []
                    listsAPP = []
                    
                    global qtdALlSerPrvd, qtdAllCombPrvd
                    qtdALlSerPrvd = []
                    qtdAllCombPrvd = []
                    
                    # Altere para range(30) ou o número desejado de execuções independentes
                    for execucao in range(1): 
                        totalComb = []
                        inicio = time.time() 
                        totalComb = cloudsSelection(app, dataAMS, dataPrvd)
                  
                        posMS = []
                        for comb in totalComb[0]:
                            total = 0
                            for eachComb in comb:
                                total += len(eachComb)
                            if totalComb[0].index(comb) == 0:
                                posMS.append(total)
                            else: 
                                posMS.append(posMS[-1] + total)
                      
                        MS = [totalComb[0].index(comb) for comb in totalComb[0]  for eachComb in comb for idx in range(len(eachComb))]
                        PR = [eachComb[0][0][1] for comb in totalComb[0] for eachComb in comb for idx in range(len(eachComb))]
                        Score = [(eachComb[0][1],eachComb[0][0][4],eachComb[0][0][5]) for comb in totalComb[0] for eachComb in comb for idx in range(len(eachComb))]
                        Cost = [eachComb[0][0][3] for comb in totalComb[0] for eachComb in comb for idx in range(len(eachComb))]
                        
                        totalCost = totalComb[1]
                        numofPrvds = calcNumofPrvds(nameLinks)
                
                        MatLinks = [[] for x in range(numofPrvds*(numofPrvds-1))]
                        for j,link in enumerate(dataLinks):
                            MatLinks[j] = link
                                    
                        MatIn = [[] for x in range(len(posMS))]
                    
                        for j, item in enumerate(MS):
                            MatIn[item].append((Score[j],Cost[j],PR[j]))
                    
                        for k in range(len(MatIn)):    
                            MatIn[k].sort(key=lambda x: x[1])
                      
                        priorities = totalComb[4]
        
                        termsApp1 = iteApp[0]['iterationsAPP']
                        seqFlowsMS = [(term['nameTerm'],[(flow['nameseq'],flow['probability'],[(seq['microservice'],seq['linksInput']) for seq in flow['dataSeq']])  for flow in term['sequences']]) for term in termsApp1 ] 
                
                        # Aplica Parâmetros Dinâmicos do ABC a partir do Dicionário
                        iteMax = cenario['iteMax']
                        nBees = cenario['nBees']
                        limit = cenario['limit']
                        
                        appAva = totalComb[2]
                        appRT = totalComb[3]
                        
                        # Chamada do ABC
                        sAPP = abcKnapSack(MatIn, totalCost, appAva, appRT, iteMax, nBees, limit, seqFlowsMS, MatLinks, priorities)
                
                        fim = time.time()
                        FinalTime = int(round(fim - inicio,3)*1000)
                        timeList.append(FinalTime)
                        
                        print(f"Execucao: {execucao+1} | Tempo: {FinalTime}ms")
                        
                        if(sAPP != [([], 0.0)]):
                            msData = []
                            for term in sAPP[0][0]:
                                    for flow in term:
                                        if (msData != []):
                                            removeMS(flow,msData)
                                            
                                        for ms in flow[0]:
                                            nameMs = "MS" + str(ms[2]+1)
                                            avaMs = ms[0][0][1]
                                            rtMs = ms[0][0][2]
                                            costMs = ms[0][1]
                                            scoreMs = ms[0][0][0]
                                            prMs = ms[0][2]
                                            msData.append((nameMs,avaMs,rtMs,costMs,scoreMs,prMs))
                            msData.sort(key=lambda a: a[0])            
                            appData = [msData,sAPP[0][1],sAPP[0][2],sAPP[0][3],sAPP[0][4],priorities]           
                              
                            listsAPP.append(appData)
                        else: print('Resultado não encontrado para essa execução.')    
                              
                    
                    # =================================================================
                    # GRAVAÇÃO DOS DADOS NO ARQUIVO ESPECÍFICO DO CENÁRIO
                    # =================================================================
                    nomeArq = os.path.join(PASTA_RESULTADOS, f"resultData_{app['app']}.txt")
                    with open(nomeArq, 'a') as arq2:
                        arq2.write(f'Cenario Parametros ABC: {cenario["nome"]} (iteMax={iteMax}, nBees={nBees}, limit={limit})\n')
                        arq2.write(f'Set of Provider: {namePrvd}\n\n')
                        for appData in listsAPP:
                            for ms in appData[0]:
                              arq2.writelines(ms[0])
                              arq2.writelines(': ')
                              arq2.writelines('Availability = ')
                              arq2.writelines(str(ms[1]))
                              arq2.writelines(' Response Time = ')
                              arq2.writelines(str(ms[2]))
                              arq2.writelines(' Cost = ')
                              arq2.writelines(str(ms[3]))
                              arq2.writelines(' score = ')
                              arq2.writelines(str(ms[4]))
                              arq2.writelines(' Provider = ')
                              arq2.writelines(str(ms[5]))
                              arq2.write('\n')
                            arq2.writelines('APP Data: ')
                            arq2.writelines('Availability = ')
                            arq2.writelines(str(appData[2]))
                            arq2.writelines(' Response Time = ')
                            arq2.writelines(str(appData[3]))
                            arq2.writelines(' Cost = ')
                            arq2.writelines(str(appData[4]))
                            arq2.writelines(' Socre = ')
                            arq2.writelines(str(appData[1]))
                            arq2.write('\n')
                            arq2.writelines('Priorities: ')
                            arq2.writelines('Availability = ')
                            arq2.writelines(str(priorities[2]))
                            arq2.writelines(' response Time = ')
                            arq2.writelines(str(priorities[0]))
                            arq2.writelines(' Cost = ')
                            arq2.writelines(str(priorities[1]))  
                            arq2.write('\n')
                            arq2.writelines(str(seqFlowsMS))
                            arq2.write('\n\n\n')
                    
                    nomeArqTime = os.path.join(PASTA_RESULTADOS, f"executionTime_{app['app']}.txt")
                    with open(nomeArqTime, 'a') as arq3:
                        arq3.write(f'Cenario Parametros ABC: {cenario["nome"]}\n')
                        arq3.write(f'Set of Provider: {namePrvd}\n\n')
                        for tm in timeList:
                            arq3.writelines(str(tm))
                            arq3.write('\n')
                     
                    print(f"-> Dados salvos com sucesso em: {PASTA_RESULTADOS}")