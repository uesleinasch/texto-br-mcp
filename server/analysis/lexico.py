#!/usr/bin/env python3
"""Perturbação lexical controlada (fase de medição) para o pipeline texto-br.

Lê JSON no stdin: {"texto": rascunho, "secao10": seção 10 de
humanizacao-algoritmos.md}. As tabelas pivot→alternativas da seção 10 são
parseadas em runtime (fonte única de verdade: editar o .md atualiza a análise).

Detecta vocabulário pivot de LLM, repetições lexicais e baixa diversidade,
devolvendo diagnóstico com alternativas. Este script mede; quem perturba o
léxico (reescreve) é o modelo, com critério de contexto.
"""

import json
import re
import sys
from collections import Counter

from texto_util import (
    STOPWORDS,
    dividir_paragrafos,
    dividir_sentencas,
    excerto,
    limpar_markdown,
    listar_palavras,
)

# Desinências verbais toleradas depois do radical de um verbo pivot (com
# fronteira final): alternância explícita em vez de sufixo genérico, para não
# casar derivados nominais como "abordagem" a partir do radical de "abordar".
SUFIXO_VERBAL = (
    r"(?:o|a|e|am|em|ou|eu|iu|ei|ia|iam|ava|avam|amos|emos|imos|"
    r"aram|eram|iram|"
    r"ará|arão|erá|erão|irá|irão|aria|ariam|eria|eriam|iria|iriam|"
    r"ando|endo|indo|ado|ada|ados|adas|ido|ida|idos|idas|ar|er|ir)\b"
)


def parsear_tabelas(secao10):
    """Extrai as tabelas pivot→alternativas das subseções 10.N."""
    categorias = {}
    categoria = None
    for linha in secao10.split("\n"):
        sub = re.match(r"^### 10\.\d+\s+(.+)$", linha)
        if sub:
            titulo = sub.group(1).lower()
            if "verbo" in titulo:
                categoria = "verbos"
            elif "adjetivo" in titulo:
                categoria = "adjetivos"
            elif "substantivo" in titulo:
                categoria = "substantivos"
            elif "conector" in titulo:
                categoria = "conectores"
            elif "abertura" in titulo:
                categoria = "aberturas"
            elif "fechamento" in titulo:
                categoria = "fechamentos"
            else:
                categoria = None
            continue
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$", linha)
        if not (m and categoria):
            continue
        evitar, trocar = m.group(1), m.group(2)
        if evitar.lower() in ("evitar", "") or set(evitar) <= {"-", " ", ":"}:
            continue  # cabeçalho ou separador da tabela
        # remove qualificadores e reticências: "fundamental (em excesso)", "Em um mundo onde..."
        termo = re.sub(r"\s*\([^)]*\)", "", evitar).strip().rstrip(".… ").lower()
        if termo:
            categorias.setdefault(categoria, []).append(
                {"termo": termo, "alternativas": trocar.strip()}
            )
    return categorias


def regex_para(termo, categoria):
    """Regex tolerante a flexão conforme a categoria do termo pivot."""
    palavras = termo.split()
    if categoria == "verbos":
        # radical do verbo (sem a terminação -ar/-er/-ir) + flexão
        primeira = palavras[0]
        raiz = re.sub(r"[aei]r$", "", primeira)
        partes = [re.escape(raiz) + SUFIXO_VERBAL] + [re.escape(p) for p in palavras[1:]]
        return re.compile(r"\b" + r"\s+".join(partes) + r"\b", re.IGNORECASE)
    if categoria in ("adjetivos", "substantivos"):
        if re.search(r"[oa]$", termo):
            base = re.escape(termo[:-1]) + r"[oa]s?"
        else:
            base = re.escape(termo) + r"s?"
        return re.compile(r"\b" + base + r"\b", re.IGNORECASE)
    # conectores, aberturas, fechamentos: frase com espaços flexíveis e
    # fronteira final, para não casar dentro de outra palavra (ex.: "além
    # disso" não pode casar o prefixo de "além dissonante").
    return re.compile(
        r"\b" + r"\s+".join(re.escape(p) for p in palavras) + r"\b", re.IGNORECASE
    )


def analisar(texto, secao10):
    prosa, _ = limpar_markdown(texto)
    paragrafos = dividir_paragrafos(prosa)
    sentencas = [s for p in paragrafos for s in dividir_sentencas(p)]
    palavras = listar_palavras(prosa)

    if len(palavras) < 30:
        return {
            "erro": "Texto com menos de 30 palavras de prosa; análise lexical não se aplica.",
            "inaplicavel": True,
        }

    categorias = parsear_tabelas(secao10)
    if not categorias:
        return {
            "erro": (
                "Tabelas de vocabulário pivot da seção 10 não carregadas; "
                "análise lexical não pode validar o alvo (verifique as references)."
            )
        }
    diagnostico = []

    # 1. Ocorrências de vocabulário pivot
    ocorrencias = []
    for categoria, entradas in categorias.items():
        for entrada in entradas:
            padrao = regex_para(entrada["termo"], categoria)
            for i, s in enumerate(sentencas):
                # aberturas só contam no início da sentença
                if categoria == "aberturas":
                    achou = padrao.match(s.lstrip("\"'«( "))
                else:
                    achou = padrao.search(s)
                if achou:
                    ocorrencias.append(
                        {
                            "categoria": categoria,
                            "pivot": entrada["termo"],
                            "encontrado": achou.group(0),
                            "sentenca": i + 1,
                            "trecho": excerto(s),
                            "alternativas": entrada["alternativas"],
                        }
                    )

    # 2. Repetições de palavras de conteúdo (avisos; repetição temática é legítima)
    conteudo = [p for p in palavras if len(p) >= 4 and p not in STOPWORDS]
    frequencias = Counter(conteudo)
    repetidas = [
        {"palavra": p, "vezes": n}
        for p, n in frequencias.most_common(8)
        if n >= 3
    ]

    proximas = []
    ultima_posicao = {}
    for pos, p in enumerate(conteudo):
        if p in ultima_posicao and pos - ultima_posicao[p] <= 20:
            proximas.append(p)
        ultima_posicao[p] = pos
    proximas = sorted(set(proximas))

    # 3. Diversidade lexical: MATTR (janela 100) em texto longo; TTR bruto abaixo.
    if len(palavras) >= 100:
        janelas = [
            len(set(palavras[i : i + 100])) / 100
            for i in range(0, len(palavras) - 99, 50)
        ]
        diversidade = round(sum(janelas) / len(janelas), 3)
        diversidade_regime = "MATTR-100"
    else:
        diversidade = round(len(set(palavras)) / len(palavras), 3)
        diversidade_regime = "TTR-bruto"

    # 4. Trigramas repetidos (estruturas de frase recicladas). Trigramas
    # compostos apenas de stopwords ("de que a") são ruído estatístico em
    # texto longo, não reciclagem de estrutura: não contam.
    def _so_stopwords(tri):
        return all(p in STOPWORDS for p in tri.split())

    trigramas = Counter(
        " ".join(palavras[i : i + 3]) for i in range(len(palavras) - 2)
    )
    trigramas_repetidos = [
        t for t, n in trigramas.items() if n >= 2 and not _so_stopwords(t)
    ]

    # Diagnóstico
    if ocorrencias:
        diagnostico.append(
            f"INTERVIR: {len(ocorrencias)} ocorrência(s) de vocabulário pivot de LLM. "
            "Troque cada uma pelas alternativas sugeridas (escolhendo a que cabe no contexto) "
            "ou corte a expressão."
        )
    else:
        diagnostico.append("OK: nenhuma ocorrência das listas de vocabulário pivot.")

    if diversidade < 0.5:
        diagnostico.append(
            f"Diversidade lexical baixa ({diversidade}): vocabulário repetitivo; "
            "varie as escolhas de palavras nas reescritas."
        )
    for r in repetidas:
        diagnostico.append(
            f"\"{r['palavra']}\" aparece {r['vezes']}x: se não for termo do tema, "
            "varie com sinônimos ou retomadas (\"isso\", \"esse processo\")."
        )
    if proximas:
        diagnostico.append(
            f"Repetições em proximidade (mesma palavra a <= 20 palavras de distância): "
            f"{', '.join(proximas[:8])}."
        )
    if trigramas_repetidos:
        diagnostico.append(
            f"Trigramas repetidos ({len(trigramas_repetidos)}): "
            f"{'; '.join(trigramas_repetidos[:5])}. Reformule uma das ocorrências."
        )

    atingiu_alvo = len(ocorrencias) == 0

    return {
        "metricas": {
            "palavras": len(palavras),
            "sentencas": len(sentencas),
            "ocorrencias_pivot": len(ocorrencias),
            "diversidade_lexical": diversidade,
            "diversidade_regime": diversidade_regime,
            "tabelas_carregadas": {c: len(e) for c, e in categorias.items()},
        },
        "ocorrencias": ocorrencias[:20],
        "repetidas": repetidas,
        "repeticoes_proximas": proximas[:10],
        "trigramas_repetidos": trigramas_repetidos[:8],
        "atingiu_alvo": atingiu_alvo,
        "diagnostico": diagnostico,
    }


def formatar_relatorio(resultado):
    if "erro" in resultado:
        return resultado["erro"]
    m = resultado["metricas"]
    linhas = [
        "## Análise de perturbação lexical",
        "",
        f"Palavras: {m['palavras']} | Sentenças: {m['sentencas']} | "
        f"Diversidade lexical ({m['diversidade_regime']}): {m['diversidade_lexical']}",
        f"**Ocorrências de vocabulário pivot: {m['ocorrencias_pivot']}** | alvo: 0",
        "",
        "### Diagnóstico",
        "",
    ]
    linhas += [f"- {d}" for d in resultado["diagnostico"]]
    if resultado["ocorrencias"]:
        linhas += ["", "### Ocorrências pivot (trocar ou cortar)", ""]
        for o in resultado["ocorrencias"]:
            linhas.append(
                f"- Sentença {o['sentenca']} [{o['categoria']}] \"{o['encontrado']}\" "
                f"→ {o['alternativas']} | contexto: \"{o['trecho']}\""
            )
    veredicto = "ALVO ATINGIDO" if resultado["atingiu_alvo"] else "REESCREVER E MEDIR DE NOVO"
    linhas += ["", f"**Veredicto: {veredicto}**"]
    return "\n".join(linhas)


def main():
    entrada = json.load(sys.stdin)
    resultado = analisar(entrada["texto"], entrada.get("secao10", ""))
    resultado["relatorio"] = formatar_relatorio(resultado)
    json.dump(resultado, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
