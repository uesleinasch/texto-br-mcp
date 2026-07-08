#!/usr/bin/env python3
"""Score de humanidade unificado para o pipeline texto-br.

Lê JSON no stdin: {"texto": rascunho, "secao10": seção 10 das references}.
Compõe os dois analisadores (variância sintática + perturbação lexical) em
17 sinais 0-1 (`sinais()`), dos quais um modelo de regressão logística
calibrado (Etapa 4, calibrar.py --fit-logistico sobre references/Corpus,
k=9 λ=1.0, AUC LOO-CV 0.902) usa 9 para estimar P(texto ser humano).
score = P(humano) x 100. O modelo (MODELO) e o alvo (ALVO) são congelados
no runtime — sem fitting, sem I/O de corpus em tempo de execução; ver
modelo-calibrado.json para a proveniência dos valores.

PESOS_MANUAIS é a referência histórica pré-calibração (pesos escolhidos a
olho, Etapa 0) — usada como prior fixo e determinístico da calibração e como
baseline do teste de separação (test_separacao.py), não como pesos de
runtime.
"""

import json
import math
import os
import sys

import lexico
import metricas
import variancia
from texto_util import clamp, limpar_markdown, listar_palavras

# Referência humana congelada (gerada por referencia_prep.py a partir do lado
# humano do corpus; versionada). Carga única na importação — artefato fixo do
# runtime, não I/O de corpus.
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "referencia_humana.json"), encoding="utf-8") as _f:
    REFERENCIA = json.load(_f)

# Pesos manuais originais (pré-Etapa-3), escolhidos a olho. Referência
# histórica e baseline do teste de separação (test_separacao.py) — prior
# fixo e determinístico usado por calibrar.py, reproduzível do repo
# independente de qualquer recalibração posterior. Não mexer. Soma 100.
PESOS_MANUAIS = {
    "burstiness": 25.0,
    "sem_sequencias_uniformes": 5.0,
    "sem_inicios_repetidos": 5.0,
    "ordem_nao_canonica": 5.0,
    "sem_pivots": 25.0,
    "diversidade_lexical": 10.0,
    "sem_trigramas_repetidos": 5.0,
    "paragrafos_variados": 8.0,
    "sentenca_de_impacto": 6.0,
    "sem_corrente_de_conectivos": 6.0,
}

# Modelo logístico calibrado na Etapa 4 (calibrar.py --fit-logistico sobre
# references/Corpus; ver modelo-calibrado.json — os valores aqui são cópia
# congelada byte-a-byte). score = P(humano) x 100. ALVO = p75 das
# probabilidades humanas x 100 (política p75_humano, decisão de produto).
#
# Nota sobre o coeficiente negativo de razao_compressao (-0.369619): é
# correção de colinearidade dentro do modelo de 9 coeficientes — só é válido
# lido em conjunto com os outros 8; isoladamente, valor bruto MENOR de
# razao_compressao indica humano (ver NORMALIZACAO_NOVOS abaixo), então não
# leia o sinal do coeficiente como a direção do sinal.
MODELO = {
    "chaves": [
        "burstiness_gb",
        "burstiness",
        "zipf",
        "sentenca_de_impacto",
        "razao_compressao",
        "burrows_delta",
        "yule_k",
        "cross_entropy_trigramas",
        "sem_pivots",
    ],
    "coeficientes": {
        "burstiness_gb": 0.603605,
        "burstiness": 0.289515,
        "zipf": 0.638093,
        "sentenca_de_impacto": 0.834445,
        "razao_compressao": -0.369619,
        "burrows_delta": 0.729567,
        "yule_k": 0.51813,
        "cross_entropy_trigramas": 1.257221,
        "sem_pivots": 1.338965,
    },
    "intercepto": 0.019577,
    "medias": {
        "burstiness_gb": 0.544985,
        "burstiness": 0.601766,
        "zipf": 0.430624,
        "sentenca_de_impacto": 0.678571,
        "razao_compressao": 0.497146,
        "burrows_delta": 0.606136,
        "yule_k": 0.647133,
        "cross_entropy_trigramas": 0.515391,
        "sem_pivots": 0.267857,
    },
    "desvios": {
        "burstiness_gb": 0.309631,
        "burstiness": 0.17922,
        "zipf": 0.285577,
        "sentenca_de_impacto": 0.467025,
        "razao_compressao": 0.294521,
        "burrows_delta": 0.310421,
        "yule_k": 0.274024,
        "cross_entropy_trigramas": 0.272366,
        "sem_pivots": 0.343359,
    },
}

# round(alvo_p75_humano_prob_precisa * 100, 1) de modelo-calibrado.json —
# o campo preciso (4 casas), não o grosseiro alvo_p75_humano_prob (1 casa,
# arredondado na escala 0-100 da antiga rota aditiva).
ALVO = 93.6


def probabilidade(s):
    """P(humano) do modelo logístico congelado sobre o dict de sinais."""
    z = MODELO["intercepto"]
    for k in MODELO["chaves"]:
        z += (MODELO["coeficientes"][k]
              * (s[k] - MODELO["medias"][k]) / MODELO["desvios"][k])
    return 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z))))


# Normalização dos sinais novos (Etapa 4): (lo, hi, invertido).
# lo/hi = percentis 5/95 da métrica no corpus (classes agrupadas),
# arredondados e congelados — ver Step 5 desta task no plano da Etapa 4.
# invertido=True quando valor MENOR indica humano. AUC é invariante a
# transformação monótona: a escolha de lo/hi não vaza informação de rótulo.
NORMALIZACAO_NOVOS = {
    "razao_compressao": (0.36, 0.52, True),
    "yule_k": (74.01, 143.25, True),
    "burstiness_gb": (-0.53, -0.12, False),
    "autocorrelacao_lag1": (-0.40, 0.30, False),
    # zipf usa a INCLINAÇÃO (não o r2): no corpus, |AUC-0.5| da inclinação
    # (0.265) supera o do r2 (0.246) — humano tem inclinação mais negativa
    # (mais aderente à lei de Zipf) que IA; invertido=True porque o AUC bruto
    # da inclinação é 0.235 (< 0.5, sinal cru favorece IA sem inversão).
    "zipf": (-0.82, -0.51, True),
    # Bloco B (Task 9/10): burrows_delta e cross_entropy_trigramas contra a
    # referência humana (score.REFERENCIA, os 29 humanos elegíveis). Menor
    # valor bruto = mais próximo/previsível pelo perfil humano de referência
    # -> invertido=True (AUC bruto 0.347/0.381, < 0.5 sem inversão, confirma
    # a direção: humano tem valor bruto menor que IA nos dois sinais).
    "burrows_delta": (0.58, 1.17, True),
    "cross_entropy_trigramas": (7.05, 7.69, True),
}

# Ordem congelada dos sinais — costura única entre runtime e calibração.
CHAVES_SINAIS = list(PESOS_MANUAIS.keys()) + list(NORMALIZACAO_NOVOS.keys())


def _norm(nome, valor):
    """Mapeia a métrica bruta para [0,1] com 1 = mais humano; None (métrica
    inaplicável em texto curto) vira 0.5, neutro."""
    if valor is None:
        return 0.5
    lo, hi, invertido = NORMALIZACAO_NOVOS[nome]
    v = clamp((valor - lo) / (hi - lo))
    return 1.0 - v if invertido else v


def sinais(ritmo, lex, texto, referencia=None):
    """Os sinais normalizados 0-1 (1 = mais humano) que compõem o score.
    Costura única entre o runtime e a calibração (calibrar.py).

    `referencia`: estatísticas de referência humana (burrows_delta,
    cross_entropy_trigramas). None -> REFERENCIA congelada (runtime); a
    calibração passa a referência do fold (sem vazamento no LOO-CV)."""
    ref = referencia if referencia is not None else REFERENCIA
    mr, ml = ritmo["metricas"], lex["metricas"]
    texto_limpo, _ = limpar_markdown(texto)
    palavras = listar_palavras(texto_limpo)
    comprimentos = mr["comprimentos"]
    s = {
        "burstiness": clamp(mr["burstiness"] / 0.9),
        "sem_sequencias_uniformes": 0.0 if ritmo["sequencias_uniformes"] else 1.0,
        "sem_inicios_repetidos": 0.0 if ritmo["inicios_repetidos"] else 1.0,
        "ordem_nao_canonica": 1.0 if (mr["nao_canonicas"] >= 1 or mr["sentencas"] < 8) else 0.0,
        "sem_pivots": clamp(1 - ml["ocorrencias_pivot"] / 10),
        "diversidade_lexical": clamp((ml["diversidade_lexical"] - 0.4) / 0.3),
        "sem_trigramas_repetidos": 0.0 if lex["trigramas_repetidos"] else 1.0,
        "paragrafos_variados": 0.0 if mr["paragrafos_uniformes"] else 1.0,
        "sentenca_de_impacto": 1.0 if mr["muito_curtas"] >= 1 else 0.0,
        "sem_corrente_de_conectivos": 1.0 if mr["conectivos_consecutivos"] < 3 else 0.0,
    }
    s["razao_compressao"] = _norm("razao_compressao", metricas.razao_compressao(texto_limpo))
    s["yule_k"] = _norm("yule_k", metricas.yule_k(palavras))
    s["burstiness_gb"] = _norm("burstiness_gb", metricas.burstiness_goh_barabasi(comprimentos))
    s["autocorrelacao_lag1"] = _norm("autocorrelacao_lag1", metricas.autocorrelacao_lag1(comprimentos))
    ajuste = metricas.zipf_ajuste(palavras)
    s["zipf"] = _norm("zipf", None if ajuste is None else ajuste[0])
    s["burrows_delta"] = _norm("burrows_delta", metricas.burrows_delta(palavras, ref))
    s["cross_entropy_trigramas"] = _norm(
        "cross_entropy_trigramas", metricas.cross_entropy_trigramas(texto_limpo, ref))
    return s


def calcular(texto, secao10):
    ritmo = variancia.analisar(texto)
    lex = lexico.analisar(texto, secao10)
    if "erro" in ritmo:
        resultado = {"erro": ritmo["erro"]}
        if ritmo.get("inaplicavel"):
            resultado["inaplicavel"] = True
        return resultado
    if "erro" in lex:
        resultado = {"erro": lex["erro"]}
        if lex.get("inaplicavel"):
            resultado["inaplicavel"] = True
        return resultado

    s = sinais(ritmo, lex, texto)
    p = probabilidade(s)
    total = round(p * 100, 1)
    contribuicoes = {
        k: round(MODELO["coeficientes"][k]
                 * (s[k] - MODELO["medias"][k]) / MODELO["desvios"][k], 2)
        for k in MODELO["chaves"]
    }

    return {
        "score": {
            "total": total,
            "alvo": ALVO,
            "componentes": contribuicoes,
            "sinais": {k: round(s[k], 2) for k in MODELO["chaves"]},
        },
        "atingiu_alvo": total >= ALVO,
        "ritmo": ritmo,
        "lexico": lex,
    }


def formatar_relatorio(resultado):
    if "erro" in resultado:
        return resultado["erro"]
    s = resultado["score"]
    linhas = [
        "## Score de humanidade",
        "",
        f"**Total: {s['total']} / 100** (probabilidade de texto humano) | alvo >= {s['alvo']} | "
        f"veredicto: {'ALVO ATINGIDO' if resultado['atingiu_alvo'] else 'REESCREVER E MEDIR DE NOVO'}",
        "",
        "| Sinal | Valor (0-1) | Contribuição |",
        "| --- | --- | --- |",
    ]
    linhas += [
        f"| {nome} | {s['sinais'][nome]} | {pontos:+} |"
        for nome, pontos in sorted(s["componentes"].items(), key=lambda kv: kv[1])
    ]
    linhas += ["", "Contribuição negativa puxa o texto para 'IA'; corrija esses sinais primeiro."]
    linhas += ["", "### Diagnóstico de ritmo", ""]
    linhas += [f"- {d}" for d in resultado["ritmo"]["diagnostico"]]
    if not resultado["ritmo"]["atingiu_alvo"] and resultado["ritmo"]["candidatas_quebra_fusao"]:
        linhas += [
            "",
            "Candidatas a quebra/fusão: "
            + "; ".join(
                f"S{c['indice']} ({c['palavras']}p) \"{c['trecho']}\""
                for c in resultado["ritmo"]["candidatas_quebra_fusao"][:8]
            ),
        ]
    linhas += ["", "### Diagnóstico lexical", ""]
    linhas += [f"- {d}" for d in resultado["lexico"]["diagnostico"]]
    if resultado["lexico"]["ocorrencias"]:
        linhas += [
            "",
            "Pivots a trocar: "
            + "; ".join(
                f"S{o['sentenca']} \"{o['encontrado']}\" → {o['alternativas']}"
                for o in resultado["lexico"]["ocorrencias"][:12]
            ),
        ]
    return "\n".join(linhas)


def main():
    entrada = json.load(sys.stdin)
    resultado = calcular(entrada["texto"], entrada.get("secao10", ""))
    resultado["relatorio"] = formatar_relatorio(resultado)
    json.dump(resultado, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
