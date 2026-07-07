#!/usr/bin/env python3
"""Análise de variância sintática para o pipeline texto-br.

Lê texto (markdown ou puro) no stdin e devolve JSON no stdout com métricas
de ritmo sintático e um relatório de diagnóstico em pt-BR. A métrica segue
a definição operacional da seção 6 de humanizacao-algoritmos.md:
burstiness = sigma(L) / mu(L), onde L são os comprimentos (palavras) das
sentenças. Intervir se < 0.5; alvo >= 0.7; faixa humana 0.6-1.2.

Apenas stdlib: este script mede e diagnostica; quem reescreve é o modelo.
"""

import json
import math
import re
import statistics
import sys

from texto_util import (
    contar_palavras,
    dividir_paragrafos,
    dividir_sentencas,
    excerto,
    limpar_markdown,
)

CONECTIVOS_INICIAIS = [
    "além disso", "no entanto", "por outro lado", "adicionalmente",
    "portanto", "contudo", "entretanto", "dessa forma", "desse modo",
    "por fim", "em suma", "em conclusão", "assim sendo", "ou seja",
    "nesse sentido", "vale ressaltar", "é importante",
]

# Aberturas que sinalizam ordem não-canônica (subordinada anteposta, gerúndio
# ou adjunto fronteado), em vez do padrão sujeito-verbo-objeto direto.
SUBORDINADORES_INICIAIS = [
    "quando", "se ", "embora", "enquanto", "caso", "apesar de", "mesmo que",
    "ainda que", "antes de", "depois de", "já que", "por mais que",
    "assim que", "sempre que", "desde que", "até que", "sem que", "para que",
    "mesmo sem", "mesmo com", "na falta de", "no dia em que",
]

# Palavras funcionais cuja repetição em início de sentença é natural em pt-BR
# (artigos, preposições, pronomes átonos de abertura): não contam como
# "início repetido".
INICIOS_NEUTROS = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "e", "em", "no", "na", "nos", "nas", "de", "do", "da",
    "mas", "que", "se", "por", "com", "para", "é",
}

# Falsos gerúndios frequentes: palavras terminadas em "ndo" que não são
# gerúndio quando abrem sentença.
FALSOS_GERUNDIOS = {"mundo", "segundo", "quando", "lindo", "fundo", "bando"}



def primeiro_termo(sentenca):
    m = re.match(r"^[\"'«(]*([\wÀ-ÿ]+)", sentenca)
    return m.group(1).lower() if m else ""



def analisar(texto):
    prosa, linhas_excluidas = limpar_markdown(texto)
    paragrafos = dividir_paragrafos(prosa)

    sentencas = []
    sentencas_por_paragrafo = []
    for p in paragrafos:
        ss = dividir_sentencas(p)
        sentencas_por_paragrafo.append(ss)
        sentencas.extend(ss)

    comprimentos = [contar_palavras(s) for s in sentencas]
    diagnostico = []

    if len(sentencas) < 3:
        return {
            "erro": (
                "Texto com menos de 3 sentenças de prosa analisáveis; "
                "variância sintática não se aplica."
            ),
            "inaplicavel": True,
        }

    media = statistics.mean(comprimentos)
    desvio = statistics.pstdev(comprimentos)
    burstiness = desvio / media if media > 0 else 0.0

    # Candidatas a quebra/fusão: sentenças no entorno da média (mu +- 30%)
    candidatas = [
        {"indice": i + 1, "palavras": c, "trecho": excerto(sentencas[i])}
        for i, c in enumerate(comprimentos)
        if media * 0.7 <= c <= media * 1.3
    ]

    # Sequências uniformes: 3+ sentenças consecutivas de comprimento similar
    # E médias/longas (média da corrida >= 8 palavras). Sequências de
    # sentenças curtas de impacto são ritmo humano, não uniformidade.
    sequencias = []
    inicio = 0
    for i in range(1, len(comprimentos) + 1):
        fim_de_corrida = i == len(comprimentos) or abs(
            comprimentos[i] - comprimentos[i - 1]
        ) > max(2, comprimentos[i - 1] * 0.2)
        if fim_de_corrida:
            corrida = comprimentos[inicio:i]
            if len(corrida) >= 3 and statistics.mean(corrida) >= 8:
                sequencias.append(
                    {"sentencas": f"{inicio + 1}-{i}", "comprimentos": corrida}
                )
            inicio = i

    # Inícios repetidos: proporcional ao tamanho do texto e ignorando
    # palavras funcionais (3 sentenças abrindo com "o" é normal em pt-BR).
    contagem_inicios = {}
    for s in sentencas:
        termo = primeiro_termo(s)
        if termo and termo not in INICIOS_NEUTROS:
            contagem_inicios[termo] = contagem_inicios.get(termo, 0) + 1
    limite_inicios = max(3, math.ceil(len(sentencas) * 0.15))
    inicios_repetidos = {
        t: n for t, n in contagem_inicios.items() if n >= limite_inicios
    }

    # Tipos de sentença (pela pontuação final) e fragmentos prováveis
    tipos = {"declarativa": 0, "interrogativa": 0, "exclamativa": 0}
    for s in sentencas:
        if s.endswith("?"):
            tipos["interrogativa"] += 1
        elif s.endswith("!"):
            tipos["exclamativa"] += 1
        else:
            tipos["declarativa"] += 1
    muito_curtas = sum(1 for c in comprimentos if c <= 4)
    muito_longas = sum(1 for c in comprimentos if c >= 30)

    # Ordem não-canônica: subordinada anteposta ou gerúndio inicial
    def nao_canonica(s):
        inicio = s.lower().lstrip("\"'«“( ")
        for sub in SUBORDINADORES_INICIAIS:
            if re.match(re.escape(sub.strip()) + r"\b", inicio):
                return True
        primeira = re.match(r"^([\wÀ-ÿ]+)", inicio)
        return bool(
            primeira
            and primeira.group(1).endswith("ndo")
            and primeira.group(1) not in FALSOS_GERUNDIOS
        )

    nao_canonicas = sum(1 for s in sentencas if nao_canonica(s))

    # Parágrafos: uniformidade e conectivos iniciais
    palavras_paragrafo = [sum(contar_palavras(s) for s in ss) for ss in sentencas_por_paragrafo]
    paragrafos_uniformes = False
    if len(palavras_paragrafo) >= 4:
        mp = statistics.mean(palavras_paragrafo)
        cv = statistics.pstdev(palavras_paragrafo) / mp if mp else 0
        paragrafos_uniformes = cv < 0.25

    conectivos_consecutivos = 0
    corrida = 0
    for p in paragrafos:
        inicio_p = p.lower().lstrip("\"'«( ")
        if any(inicio_p.startswith(c) for c in CONECTIVOS_INICIAIS):
            corrida += 1
            conectivos_consecutivos = max(conectivos_consecutivos, corrida)
        else:
            corrida = 0

    # Diagnóstico
    if burstiness < 0.5:
        diagnostico.append(
            f"INTERVIR: burstiness {burstiness:.2f} < 0.5. Quebre candidatas em "
            "sentenças muito curtas (1-5 palavras) e funda outras com vizinhas "
            "(30+ palavras) para aumentar o desvio sem mexer muito na média."
        )
    elif burstiness < 0.7:
        diagnostico.append(
            f"ABAIXO DO ALVO: burstiness {burstiness:.2f} (alvo >= 0.7). "
            "Acentue contrastes: mais sentenças muito curtas e muito longas."
        )
    else:
        diagnostico.append(f"OK: burstiness {burstiness:.2f} dentro do alvo (>= 0.7).")

    for seq in sequencias:
        diagnostico.append(
            f"Sequência uniforme nas sentenças {seq['sentencas']} "
            f"(comprimentos {seq['comprimentos']}): quebre ou funda ao menos uma."
        )
    for termo, n in inicios_repetidos.items():
        diagnostico.append(
            f"{n} sentenças começam com \"{termo}\": varie as aberturas."
        )
    if muito_curtas == 0:
        diagnostico.append(
            "Nenhuma sentença muito curta (<= 4 palavras): crie 1-2 de impacto."
        )
    if muito_longas == 0 and media < 22:
        diagnostico.append(
            "Nenhuma sentença longa (>= 30 palavras): funda vizinhas em ao menos uma."
        )
    if tipos["interrogativa"] == 0 and len(sentencas) >= 10:
        diagnostico.append(
            "Nenhuma interrogativa: considere 1 pergunta retórica, se o tipo permitir."
        )
    if nao_canonicas == 0 and len(sentencas) >= 8:
        diagnostico.append(
            "Nenhuma sentença com ordem não-canônica: insira 1-2 subordinadas "
            "antepostas (\"Quando X, Y\"), intercaladas (\"O projeto, embora "
            "atrasado, saiu\") ou gerúndio inicial."
        )
    if paragrafos_uniformes:
        diagnostico.append(
            "Parágrafos com tamanho uniforme: misture um parágrafo de uma linha "
            "com outros mais longos."
        )
    if conectivos_consecutivos >= 3:
        diagnostico.append(
            "3+ parágrafos consecutivos abrem com conectivo lógico: remova ao "
            "menos um e deixe a justaposição falar."
        )

    atingiu_alvo = burstiness >= 0.7 and not sequencias and not inicios_repetidos

    return {
        "metricas": {
            "sentencas": len(sentencas),
            "palavras": sum(comprimentos),
            "paragrafos": len(paragrafos),
            "comprimentos": comprimentos,
            "media": round(media, 2),
            "desvio": round(desvio, 2),
            "burstiness": round(burstiness, 3),
            "alvo": {"intervir_abaixo_de": 0.5, "minimo": 0.7, "faixa_humana": "0.6-1.2"},
            "tipos_de_sentenca": tipos,
            "muito_curtas": muito_curtas,
            "muito_longas": muito_longas,
            "nao_canonicas": nao_canonicas,
            "paragrafos_uniformes": paragrafos_uniformes,
            "conectivos_consecutivos": conectivos_consecutivos,
            "linhas_nao_prosa_excluidas": linhas_excluidas,
        },
        "candidatas_quebra_fusao": candidatas[:12],
        "sequencias_uniformes": sequencias,
        "inicios_repetidos": inicios_repetidos,
        "atingiu_alvo": atingiu_alvo,
        "diagnostico": diagnostico,
    }


def formatar_relatorio(resultado):
    if "erro" in resultado:
        return resultado["erro"]
    m = resultado["metricas"]
    linhas = [
        "## Análise de variância sintática",
        "",
        f"Sentenças: {m['sentencas']} | Palavras: {m['palavras']} | "
        f"Parágrafos: {m['paragrafos']}",
        f"Comprimento médio: {m['media']} palavras | Desvio: {m['desvio']}",
        f"**Burstiness (sigma/mu): {m['burstiness']}** | alvo >= 0.7 | "
        f"faixa humana 0.6-1.2",
        f"Comprimentos por sentença: {m['comprimentos']}",
        f"Tipos: {m['tipos_de_sentenca']['declarativa']} declarativas, "
        f"{m['tipos_de_sentenca']['interrogativa']} interrogativas, "
        f"{m['tipos_de_sentenca']['exclamativa']} exclamativas | "
        f"muito curtas (<=4): {m['muito_curtas']} | muito longas (>=30): {m['muito_longas']} | "
        f"ordem não-canônica: {m['nao_canonicas']}",
        "",
        "### Diagnóstico",
        "",
    ]
    linhas += [f"- {d}" for d in resultado["diagnostico"]]
    if not resultado["atingiu_alvo"] and resultado["candidatas_quebra_fusao"]:
        linhas += [
            "",
            "### Candidatas a quebra/fusão (no entorno da média)",
            "",
        ]
        linhas += [
            f"- Sentença {c['indice']} ({c['palavras']} palavras): \"{c['trecho']}\""
            for c in resultado["candidatas_quebra_fusao"]
        ]
        linhas += [
            "",
            "Padrões de ritmo úteis: revelação [longa][curta-impacto]; "
            "cascata [curta][média][longa]; eco [curta][longa][curta][longa][curta]; "
            "declaração + qualificação [muito curta][longa].",
        ]
    veredicto = "ALVO ATINGIDO" if resultado["atingiu_alvo"] else "REESCREVER E MEDIR DE NOVO"
    linhas += ["", f"**Veredicto: {veredicto}**"]
    return "\n".join(linhas)


def main():
    texto = sys.stdin.read()
    resultado = analisar(texto)
    resultado["relatorio"] = formatar_relatorio(resultado)
    json.dump(resultado, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
