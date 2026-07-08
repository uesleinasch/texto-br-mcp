#!/usr/bin/env python3
"""Score de humanidade unificado para o pipeline texto-br.

Lê JSON no stdin: {"texto": rascunho, "secao10": seção 10 das references}.
Compõe os dois analisadores (variância sintática + perturbação lexical) numa
função objetivo 0-100, usada como critério único do loop de otimização da
Fase 2.

Pesos e ALVO calibrados empiricamente na Etapa 3 sobre o corpus rotulado
(calibrar.py --fit; ver PESOS/ALVO abaixo e pesos-calibrados.json). Os 10
sinais que compõem o score estão definidos em `sinais()`. PESOS_MANUAIS é a
referência histórica pré-calibração (pesos escolhidos a olho) — usada como
prior fixo e determinístico da calibração, não como pesos de runtime.
"""

import json
import sys

import lexico
import metricas
import variancia
from texto_util import clamp, limpar_markdown, listar_palavras

# Pesos manuais originais (pré-Etapa-3), escolhidos a olho. Referência FIXA
# usada como prior/baseline da calibração em calibrar.py — não mexer, mesmo
# quando PESOS (abaixo) for recalibrado. Soma 100.
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

# Pesos e ALVO calibrados na Etapa 3 (calibrar.py --fit sobre references/Corpus).
# ALVO = p75 dos scores humanos (política p75_humano; decisão de produto sobre
# o ponto de Youden). Ver pesos-calibrados.json.
ALVO = 74.4

PESOS = {
    "burstiness": 21.3,
    "sem_sequencias_uniformes": 2.0,
    "sem_inicios_repetidos": 10.2,
    "ordem_nao_canonica": 6.4,
    "sem_pivots": 23.0,
    "diversidade_lexical": 2.5,
    "sem_trigramas_repetidos": 2.0,
    "paragrafos_variados": 10.6,
    "sentenca_de_impacto": 13.7,
    "sem_corrente_de_conectivos": 8.3,
}


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


def sinais(ritmo, lex, texto):
    """Os sinais normalizados 0-1 (1 = mais humano) que compõem o score.
    Costura única entre o runtime e a calibração (calibrar.py)."""
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
    componentes = {k: round(s[k] * PESOS[k], 1) for k in PESOS}
    total = round(sum(componentes.values()), 1)
    atingiu = total >= ALVO
    maximos = dict(PESOS)

    return {
        "score": {
            "total": total,
            "alvo": ALVO,
            "componentes": componentes,
            "maximos": maximos,
        },
        "atingiu_alvo": atingiu,
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
        f"**Total: {s['total']} / 100** | alvo >= {s['alvo']} | "
        f"veredicto: {'ALVO ATINGIDO' if resultado['atingiu_alvo'] else 'REESCREVER E MEDIR DE NOVO'}",
        "",
        "| Componente | Pontos |",
        "| --- | --- |",
    ]
    linhas += [f"| {nome} | {pontos} |" for nome, pontos in s["componentes"].items()]
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
