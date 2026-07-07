#!/usr/bin/env python3
"""Score de humanidade unificado para o pipeline texto-br.

Lê JSON no stdin: {"texto": rascunho, "secao10": seção 10 das references}.
Compõe os dois analisadores (variância sintática + perturbação lexical) numa
função objetivo 0-100, usada como critério único do loop de otimização da
Fase 2. Componentes:

  Ritmo (40):     burstiness 25 | sem sequências uniformes 5 |
                  sem inícios repetidos 5 | ordem não-canônica presente 5
  Léxico (40):    ausência de pivots 25 | diversidade lexical 10 |
                  sem trigramas repetidos 5
  Estrutura (20): parágrafos não-uniformes 8 | sentença curta de impacto 6 |
                  sem corrente de conectivos 6

Alvo: score >= 80.
"""

import json
import sys

import lexico
import variancia
from texto_util import clamp

ALVO = 80


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

    mr, ml = ritmo["metricas"], lex["metricas"]

    componentes = {
        "burstiness": round(clamp(mr["burstiness"] / 0.9) * 25, 1),
        "sem_sequencias_uniformes": 5 if not ritmo["sequencias_uniformes"] else 0,
        "sem_inicios_repetidos": 5 if not ritmo["inicios_repetidos"] else 0,
        "ordem_nao_canonica": 5 if (mr["nao_canonicas"] >= 1 or mr["sentencas"] < 8) else 0,
        "sem_pivots": round(clamp(1 - ml["ocorrencias_pivot"] / 10) * 25, 1),
        "diversidade_lexical": round(clamp((ml["diversidade_lexical"] - 0.4) / 0.3) * 10, 1),
        "sem_trigramas_repetidos": 5 if not lex["trigramas_repetidos"] else 0,
        "paragrafos_variados": 8 if not mr["paragrafos_uniformes"] else 0,
        "sentenca_de_impacto": 6 if mr["muito_curtas"] >= 1 else 0,
        "sem_corrente_de_conectivos": 6 if mr["conectivos_consecutivos"] < 3 else 0,
    }
    total = round(sum(componentes.values()), 1)
    atingiu = total >= ALVO

    maximos = {
        "burstiness": 25,
        "sem_sequencias_uniformes": 5,
        "sem_inicios_repetidos": 5,
        "ordem_nao_canonica": 5,
        "sem_pivots": 25,
        "diversidade_lexical": 10,
        "sem_trigramas_repetidos": 5,
        "paragrafos_variados": 8,
        "sentenca_de_impacto": 6,
        "sem_corrente_de_conectivos": 6,
    }

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
