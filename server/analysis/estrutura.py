#!/usr/bin/env python3
"""Análise macroestrutural (naturalidade estrutural) para o pipeline texto-br.

Lê JSON no stdin: {"texto": rascunho, "tipo": id do tipo}. Mede sinais
macroestruturais de IA ("estrutura encaixada demais") via um registry de
detectores e os compõe num score 0-100. Este script mede e diagnostica; quem
reescreve (perturba a estrutura) é o modelo.

Detectores (peso): simetria de seções (25), inflação de subtópicos (20),
parágrafo-lição/kicker uniforme (20), frases de efeito em sequência (15),
progressão sinalizada (20). Só os aplicáveis entram no score, re-normalizado
pelos pesos aplicáveis. Alvo: score >= 70.

Calibração por tipo: o conjunto de gate (TIPOS_GATE) e o alvo replicam
TIPOS_ESTRUTURA_GATE / ALVO de knowledge/phases.js (fonte de verdade lá).
"""

import json
import re
import statistics
import sys

from texto_util import (
    CONECTIVOS_INICIAIS,
    clamp,
    contar_palavras,
    dividir_sentencas,
    parsear_blocos,
    primeiro_termo,
)

# Espelha TIPOS_ESTRUTURA_GATE em knowledge/phases.js.
TIPOS_GATE = ["blog", "capitulo", "tecnico", "explicativo", "podcast", "video"]
ALVO_PADRAO = 70

MARCADORES_LICAO = [
    "no fim das contas", "no fim", "no fundo", "afinal", "é isso",
    "talvez seja", "o que importa", "a verdade é", "no final", "resta",
    "moral da história", "e é por isso", "é sobre isso", "se há algo",
]
SIGNPOSTS = [
    "primeiro", "terceiro", "em seguida", "por fim",
    "finalmente", "a seguir", "para começar", "em primeiro lugar",
    "em segundo lugar", "por último", "agora que",
]
# Signposts que exigem desambiguação: só contam como progressão sinalizada
# nas formas enumerativas ("Segundo, ..." / "Em segundo lugar") ou sequenciais
# explícitas ("Depois, ..." / "Depois disso"). Fora dessas formas, "segundo" é
# preposição de citação de fonte ("segundo o IBGE") e "depois" é advérbio comum
# ("depois de anos") — não são progressão sinalizada.
SIGNPOSTS_AMBIGUOS = [
    (re.compile(r"^segundo\s*,", re.IGNORECASE), "segundo"),
    (re.compile(r"^em segundo lugar\b", re.IGNORECASE), "segundo"),
    (re.compile(r"^depois\s*,", re.IGNORECASE), "depois"),
    (re.compile(r"^depois disso\b", re.IGNORECASE), "depois"),
]
def interp(valor, ruim, bom):
    """Qualidade 0-1: valor no ponto `ruim` → 0, no ponto `bom` → 1, linear no
    meio (clampado). Funciona com bom > ruim e bom < ruim."""
    if bom == ruim:
        return 1.0 if valor >= bom else 0.0
    return clamp((valor - ruim) / (bom - ruim))


def comeca_com(texto, lista):
    base = texto.strip().lower().lstrip("\"'«( ")
    return any(base.startswith(p) for p in lista)


def comeca_com_signpost(texto):
    """Como comeca_com(texto, SIGNPOSTS), mas testa primeiro os signposts
    ambíguos (regex) antes de cair na lista simples que perdeu "segundo"/
    "depois"."""
    base = texto.strip().lstrip("\"'«( ")
    if any(padrao.match(base) for padrao, _ in SIGNPOSTS_AMBIGUOS):
        return True
    return comeca_com(texto, SIGNPOSTS)


def contem_marcador(texto, lista):
    base = texto.strip().lower()
    return any(p in base for p in lista)


def montar_outline(blocos):
    """Agrupa blocos em seções. Se há um único `#` como primeiro heading, é o
    título do documento e o nível de seção é 2; senão é o menor nível presente.
    Parágrafos antes da primeira seção viram uma seção sem título (lead)."""
    headings = [b for b in blocos if b["tipo"] == "heading"]
    titulo = None
    nivel_secao = None
    if headings:
        niveis1 = [b for b in headings if b["nivel"] == 1]
        if headings[0]["nivel"] == 1 and len(niveis1) == 1:
            titulo = headings[0]["texto"]
            nivel_secao = 2
        else:
            nivel_secao = min(h["nivel"] for h in headings)

    secoes = []
    atual = None
    for b in blocos:
        if b["tipo"] == "heading":
            if titulo is not None and b is headings[0]:
                continue  # título do documento
            if nivel_secao is not None and b["nivel"] == nivel_secao:
                atual = {"titulo": b["texto"], "nivel": b["nivel"], "paragrafos": [], "subsecoes": []}
                secoes.append(atual)
            elif nivel_secao is not None and b["nivel"] > nivel_secao and atual is not None:
                atual["subsecoes"].append(b["texto"])
        elif b["tipo"] == "paragrafo":
            if atual is not None:
                atual["paragrafos"].append(b["texto"])
            else:
                atual = {"titulo": None, "nivel": 0, "paragrafos": [b["texto"]], "subsecoes": []}
                secoes.append(atual)

    if nivel_secao is None:
        paras = [b["texto"] for b in blocos if b["tipo"] == "paragrafo"]
        secoes = [{"titulo": None, "nivel": 0, "paragrafos": paras, "subsecoes": []}]

    for s in secoes:
        s["palavras"] = sum(contar_palavras(p) for p in s["paragrafos"])
    return {"titulo": titulo, "nivel_secao": nivel_secao, "secoes": secoes,
            "tem_headings": bool(headings)}


def paragrafos_de_prosa(outline):
    return [p for s in outline["secoes"] for p in s["paragrafos"]]


# ----- Detector 1: Simetria de seções (peso 25) -----
def detector_simetria(outline, blocos, tipo):
    base = {"id": "simetria_secoes", "nome": "Simetria de seções", "peso": 25}
    secoes = [s for s in outline["secoes"] if s.get("titulo")]
    if len(secoes) < 3:
        return {**base, "aplicavel": False, "subscore": 1.0, "metricas": {"secoes": len(secoes)},
                "diagnostico": ["Menos de 3 seções: simetria de seções não se aplica."],
                "perturbacoes": []}

    palavras = [s["palavras"] for s in secoes]
    media = statistics.mean(palavras)
    cv_tam = statistics.pstdev(palavras) / media if media else 0.0

    titulos = [s["titulo"] for s in secoes]
    frac_ger = sum(1 for t in titulos if primeiro_termo(t).endswith("ndo")) / len(titulos)
    frac_perg = sum(1 for t in titulos if t.strip().endswith("?")) / len(titulos)
    primeiros = [primeiro_termo(t) for t in titulos]
    frac_mesmo = max(primeiros.count(p) for p in set(primeiros)) / len(primeiros)
    paralelismo = max(frac_ger, frac_perg, frac_mesmo)

    n_sub = [len(s["subsecoes"]) for s in secoes]
    if all(n == n_sub[0] for n in n_sub) and n_sub[0] >= 2:
        sub_sub = 0.0
    else:
        msub = statistics.mean(n_sub) if n_sub else 0
        cv_sub = (statistics.pstdev(n_sub) / msub) if msub else 1.0
        sub_sub = interp(cv_sub, ruim=0.1, bom=0.5)

    s_tam = interp(cv_tam, ruim=0.15, bom=0.45)
    s_tit = interp(paralelismo, ruim=0.85, bom=0.4)  # paralelismo alto → 0
    subscore = round((s_tam + s_tit + sub_sub) / 3, 3)

    diag, pert = [], []
    if s_tam < 0.6:
        diag.append(f"Seções de tamanho uniforme (CV {cv_tam:.2f}): palavras {palavras}.")
        pert.append("Deixe uma seção respirar (corte ~metade) e outra ir fundo (dobre); funda as gêmeas.")
    if s_tit < 0.6:
        diag.append(f"Títulos com forma paralela ({paralelismo:.0%}): {titulos}.")
        pert.append("Reescreva >= 2 títulos com forma gramatical diferente (pergunta, frase nominal, imperativo).")
    if sub_sub < 0.5:
        diag.append("Número de subseções por seção uniforme.")
        pert.append("Varie a profundidade: deixe uma seção sem subseções e outra com mais.")
    return {**base, "aplicavel": True, "subscore": subscore,
            "metricas": {"secoes": len(secoes), "cv_tamanho": round(cv_tam, 3),
                         "paralelismo_titulos": round(paralelismo, 3), "palavras_por_secao": palavras},
            "diagnostico": diag or ["OK: seções com variação saudável."], "perturbacoes": pert}


# ----- Detector 2: Inflação de subtópicos (peso 20) -----
FATOR_DENSIDADE = {"tecnico": 1.8}  # documentação técnica tolera mais headings


def detector_subtopicos(outline, blocos, tipo):
    base = {"id": "inflacao_subtopicos", "nome": "Inflação de subtópicos", "peso": 20}
    nivel_secao = outline["nivel_secao"] or 2
    n_headings = sum(1 for b in blocos if b["tipo"] == "heading" and b["nivel"] >= nivel_secao)
    com_titulo = [s for s in outline["secoes"] if s.get("titulo")]
    palavras_total = sum(s["palavras"] for s in outline["secoes"])
    if n_headings < 1 or palavras_total < 1:
        return {**base, "aplicavel": False, "subscore": 1.0, "metricas": {"headings": n_headings},
                "diagnostico": ["Sem subtítulos: inflação de subtópicos não se aplica."],
                "perturbacoes": []}

    densidade = n_headings / (palavras_total / 100)
    fator = FATOR_DENSIDADE.get(tipo, 1.0)
    finas = [s for s in com_titulo if s["palavras"] < 60]
    frac_finas = len(finas) / max(1, len(com_titulo))

    s_dens = interp(densidade, ruim=3.5 * fator, bom=1.5 * fator)  # densidade alta → 0
    s_finas = interp(frac_finas, ruim=0.7, bom=0.3)  # muitas finas → 0
    subscore = round((s_dens + s_finas) / 2, 3)

    diag, pert = [], []
    if s_dens < 0.6:
        diag.append(f"Densidade alta de subtítulos: {n_headings} em {palavras_total} palavras "
                    f"(1 a cada {round(palavras_total / n_headings)}).")
        pert.append("Funda subtítulos finos; mantenha só os que marcam virada real de assunto.")
    if s_finas < 0.6:
        diag.append(f"{len(finas)} seção(ões) com menos de 60 palavras.")
        pert.append("Rebaixe seções finas a parágrafo com frase-guia, sem heading próprio.")
    return {**base, "aplicavel": True, "subscore": subscore,
            "metricas": {"headings": n_headings, "densidade_por_100w": round(densidade, 2),
                         "frac_secoes_finas": round(frac_finas, 2)},
            "diagnostico": diag or ["OK: densidade de subtítulos saudável."], "perturbacoes": pert}


# ----- Detector 3: Parágrafo-lição / kicker uniforme (peso 20) -----
def detector_kicker(outline, blocos, tipo):
    base = {"id": "kicker_uniforme", "nome": "Parágrafo-lição (kicker)", "peso": 20}
    elegiveis, com_kicker = 0, 0
    for p in paragrafos_de_prosa(outline):
        ss = dividir_sentencas(p)
        if len(ss) < 2:
            continue
        elegiveis += 1
        ult = contar_palavras(ss[-1])
        corpo = statistics.mean(contar_palavras(s) for s in ss[:-1])
        razao = ult / corpo if corpo else 1.0
        kicker = (razao < 0.6 or contem_marcador(ss[-1], MARCADORES_LICAO)
                  or (primeiro_termo(ss[-1]) == "e" and ult <= 8))
        if kicker:
            com_kicker += 1
    if elegiveis < 4:
        return {**base, "aplicavel": False, "subscore": 1.0,
                "metricas": {"paragrafos_elegiveis": elegiveis},
                "diagnostico": ["Menos de 4 parágrafos multi-sentença: kicker não se aplica."],
                "perturbacoes": []}
    frac = com_kicker / elegiveis
    subscore = round(interp(frac, ruim=0.75, bom=0.4), 3)  # muitos kickers → 0
    diag, pert = [], []
    if subscore < 0.7:
        diag.append(f"{com_kicker} de {elegiveis} parágrafos fecham numa 'lição' curta ({frac:.0%}).")
        pert.append("Deixe ~3 parágrafos terminarem no meio do raciocínio, sem moral arredondada.")
        pert.append("Mova o fecho de um parágrafo para o início do parágrafo seguinte.")
    return {**base, "aplicavel": True, "subscore": subscore,
            "metricas": {"paragrafos_elegiveis": elegiveis, "com_kicker": com_kicker, "frac": round(frac, 2)},
            "diagnostico": diag or ["OK: fechos de parágrafo variados."], "perturbacoes": pert}


# ----- Detector 4: Frases de efeito em sequência (peso 15) -----
def detector_frases_efeito(outline, blocos, tipo):
    base = {"id": "frases_efeito", "nome": "Frases de efeito em sequência", "peso": 15}
    paras = paragrafos_de_prosa(outline)
    if len(paras) < 5:
        return {**base, "aplicavel": False, "subscore": 1.0, "metricas": {"paragrafos": len(paras)},
                "diagnostico": ["Menos de 5 parágrafos: frases de efeito não se aplica."],
                "perturbacoes": []}
    bordao = []
    for p in paras:
        ss = dividir_sentencas(p)
        bordao.append(len(ss) == 1 and contar_palavras(ss[0]) <= 8)
    frac = sum(bordao) / len(bordao)
    maior_corrida = corrida = 0
    for b in bordao:
        corrida = corrida + 1 if b else 0
        maior_corrida = max(maior_corrida, corrida)
    s_frac = interp(frac, ruim=0.45, bom=0.15)
    s_corr = 1.0 if maior_corrida < 2 else (0.4 if maior_corrida == 2 else 0.0)
    subscore = round(min(s_frac, s_corr), 3)
    diag, pert = [], []
    if subscore < 0.7:
        diag.append(f"{sum(bordao)} parágrafos-bordão de {len(paras)} (maior sequência: {maior_corrida}).")
        pert.append("Funda ao menos um bordão da sequência ao parágrafo vizinho, ou desenvolva-o em 2-3 sentenças.")
    return {**base, "aplicavel": True, "subscore": subscore,
            "metricas": {"paragrafos": len(paras), "bordoes": sum(bordao), "maior_sequencia": maior_corrida},
            "diagnostico": diag or ["OK: bordões dosados."], "perturbacoes": pert}


# ----- Detector 5: Progressão sinalizada (peso 20) -----
def detector_progressao(outline, blocos, tipo):
    base = {"id": "progressao_sinalizada", "nome": "Progressão sinalizada", "peso": 20}
    com_titulo = [s for s in outline["secoes"] if s.get("titulo")]
    paras = paragrafos_de_prosa(outline)
    if len(com_titulo) < 3 and len(paras) < 6:
        return {**base, "aplicavel": False, "subscore": 1.0, "metricas": {},
                "diagnostico": ["Estrutura insuficiente: progressão não se aplica."], "perturbacoes": []}

    titulos_signpost = sum(1 for s in com_titulo if comeca_com_signpost(s["titulo"])
                           or re.match(r"^\d+[.)]?\s", s["titulo"].strip()))
    aberturas_signpost = sum(1 for p in paras if comeca_com_signpost(p))
    aberturas_conectivo = sum(1 for s in com_titulo if s["paragrafos"]
                              and comeca_com(s["paragrafos"][0], CONECTIVOS_INICIAIS))
    intro_outro = False
    if len(com_titulo) >= 3:
        media_pal = statistics.mean([s["palavras"] for s in com_titulo])
        prim, ult = com_titulo[0], com_titulo[-1]
        intro_outro = (prim["palavras"] < 0.7 * media_pal
                       and any(contem_marcador(p, MARCADORES_LICAO) for p in ult["paragrafos"]))

    penal = 0.0
    penal += 0.45 if (titulos_signpost >= 2 or aberturas_signpost >= 3) else 0.0
    penal += 0.30 if aberturas_conectivo >= 2 else 0.0
    penal += 0.25 if intro_outro else 0.0
    subscore = round(clamp(1.0 - penal), 3)

    diag, pert = [], []
    if titulos_signpost >= 2 or aberturas_signpost >= 3:
        diag.append("Escada de signposts (primeiro/depois/por fim) na progressão.")
        pert.append("Remova a numeração e os 'primeiro/depois/por fim' explícitos; deixe a transição implícita.")
    if aberturas_conectivo >= 2:
        diag.append("Seções abrindo em corrente de conectivos lógicos.")
        pert.append("Abra ao menos uma seção direto no concreto, sem conectivo de ligação.")
    if intro_outro:
        diag.append("Primeira e última seção formam moldura intro/conclusão simétrica.")
        pert.append("Quebre a simetria intro/conclusão: comece no meio da ação ou termine sem fechar o laço.")
    return {**base, "aplicavel": True, "subscore": subscore,
            "metricas": {"titulos_signpost": titulos_signpost, "aberturas_signpost": aberturas_signpost,
                         "aberturas_conectivo": aberturas_conectivo, "intro_outro_simetrico": intro_outro},
            "diagnostico": diag or ["OK: progressão sem andaime explícito."], "perturbacoes": pert}


DETECTORES = [
    detector_simetria,
    detector_subtopicos,
    detector_kicker,
    detector_frases_efeito,
    detector_progressao,
]


def calcular(texto, tipo):
    blocos = parsear_blocos(texto)
    outline = montar_outline(blocos)
    paras = paragrafos_de_prosa(outline)
    if len(paras) < 4:
        return {
            "erro": "Texto com menos de 4 parágrafos de prosa; análise macroestrutural não se aplica.",
            "inaplicavel": True,
        }

    alvo = ALVO_PADRAO
    resultados = [d(outline, blocos, tipo) for d in DETECTORES]
    aplic = [r for r in resultados if r["aplicavel"]]
    if not aplic:
        total = 100.0
    else:
        soma_peso = sum(r["peso"] for r in aplic)
        total = round(sum(r["peso"] * r["subscore"] for r in aplic) / soma_peso * 100, 1)
    atingiu = total >= alvo or not aplic

    return {
        "score": {"total": total, "alvo": alvo, "tipo": tipo, "gate": tipo in TIPOS_GATE},
        "atingiu_alvo": atingiu,
        "detectores": resultados,
        "outline": {"secoes": len(outline["secoes"]), "tem_headings": outline["tem_headings"]},
    }


def formatar_relatorio(resultado):
    if "erro" in resultado:
        return resultado["erro"]
    s = resultado["score"]
    veredicto = "ALVO ATINGIDO" if resultado["atingiu_alvo"] else "REESCREVER E MEDIR DE NOVO"
    linhas = [
        "## Score de naturalidade estrutural", "",
        f"**Total: {s['total']} / 100** | alvo >= {s['alvo']} | tipo: {s['tipo']} "
        f"({'gate' if s['gate'] else 'advisory'}) | veredicto: {veredicto}", "",
        "| Detector | subscore | peso | pts |", "| --- | --- | --- | --- |",
    ]
    for r in resultado["detectores"]:
        if r["aplicavel"]:
            pts = round(r["peso"] * r["subscore"], 1)
            linhas.append(f"| {r['nome']} | {r['subscore']} | {r['peso']} | {pts} |")
        else:
            linhas.append(f"| {r['nome']} | não se aplica | {r['peso']} | — |")
    linhas += ["", "### Diagnóstico", ""]
    for r in resultado["detectores"]:
        for d in r["diagnostico"]:
            linhas.append(f"- [{r['nome']}] {d}")
    pert = sorted([r for r in resultado["detectores"] if r["aplicavel"] and r["perturbacoes"]],
                  key=lambda r: r["subscore"])
    if pert and not resultado["atingiu_alvo"]:
        linhas += ["", "## Plano de perturbação", "",
                   "Priorizado pelos detectores mais fracos. Aplique e meça de novo:", ""]
        for r in pert:
            for p in r["perturbacoes"]:
                linhas.append(f"- {p}")
    linhas += ["", f"**Veredicto: {veredicto}**"]
    return "\n".join(linhas)


def main():
    entrada = json.load(sys.stdin)
    resultado = calcular(entrada["texto"], entrada.get("tipo", "geral"))
    resultado["relatorio"] = formatar_relatorio(resultado)
    json.dump(resultado, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
