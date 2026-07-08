#!/usr/bin/env python3
"""Calibração empírica do score sobre o corpus rotulado (offline, stdlib puro).

Modos:
  --baseline  mede a separação humano/IA com os PESOS atuais e emite relatório.
  --fit       ajusta a regressão logística e emite pesos-calibrados.json (Task 5).

Não importa numpy. Determinístico."""

import json
import math
import os
import re
import sys

import lexico
import score
import variancia


def auc(scores, labels):
    """Área sob a ROC (estatística de Mann-Whitney). Empates contam 0.5."""
    pos = [s for s, l in zip(scores, labels) if l == 1]
    neg = [s for s, l in zip(scores, labels) if l == 0]
    if not pos or not neg:
        return float("nan")
    wins = 0.0
    for p in pos:
        for n in neg:
            wins += 1.0 if p > n else (0.5 if p == n else 0.0)
    return wins / (len(pos) * len(neg))


def score_ponderado(x, pesos, chaves):
    return sum(x[i] * pesos[k] for i, k in enumerate(chaves))


def _secao10_real(dir_corpus):
    """Extrai a seção 10 REAL de references/humanizacao-algoritmos.md, para a
    calibração ver o mesmo vocabulário pivot que o runtime (senão o peso de
    sem_pivots descasa). Fallback mínimo se o arquivo/seção não existir."""
    ref = os.path.join(dir_corpus, "..", "humanizacao-algoritmos.md")
    try:
        with open(ref, encoding="utf-8") as f:
            texto = f.read()
    except OSError:
        texto = ""
    m = re.search(r"(?ms)^##\s*10\.\s.*?(?=^##\s*11\.\s|\Z)", texto)
    if m:
        return m.group(0)
    return (  # fallback mínimo se a seção não for encontrada
        "### 10.1 Verbos pivot\n| Evitar | Trocar por |\n|---|---|\n"
        "| abordar | tratar de |\n| destacar | mostrar |\n| garantir | assegurar |\n"
        "### 10.4 Conectores\n| Evitar | Trocar por |\n"
        "| além disso | e |\n| no entanto | mas |\n| portanto | então |\n"
    )


CHAVES = list(score.PESOS.keys())


def matriz_features(dir_corpus, secao10=None):
    secao10 = secao10 if secao10 is not None else _secao10_real(dir_corpus)
    with open(os.path.join(dir_corpus, "manifest.json"), encoding="utf-8") as f:
        manifesto = json.load(f)
    X, y, nomes = [], [], []
    for e in manifesto:
        if not e["incluir_calibracao"]:
            continue
        caminho = os.path.join(dir_corpus, e["arquivo"])
        with open(caminho, encoding="utf-8") as f:
            texto = f.read()
        ritmo = variancia.analisar(texto)
        lex = lexico.analisar(texto, secao10)
        if "erro" in ritmo or "erro" in lex:
            continue  # inaplicável apesar do manifesto; pula com segurança
        s = score.sinais(ritmo, lex)
        X.append([s[k] for k in CHAVES])
        y.append(1 if e["classe"] == "humano" else 0)
        nomes.append(e["arquivo"])
    return X, y, nomes, CHAVES


def relatorio_baseline(dir_corpus, secao10=None):
    X, y, nomes, chaves = matriz_features(dir_corpus, secao10)
    scores = [score_ponderado(x, score.PESOS, chaves) for x in X]
    a = auc(scores, y)
    hum = [s for s, l in zip(scores, y) if l == 1]
    ia = [s for s, l in zip(scores, y) if l == 0]
    # poder discriminativo por componente: AUC univariado do sinal
    disc = {}
    for i, k in enumerate(chaves):
        col = [x[i] for x in X]
        disc[k] = round(auc(col, y), 3)
    return {
        "n_humano": len(hum), "n_ia": len(ia),
        "auc_total": round(a, 3),
        "media_humano": round(sum(hum) / len(hum), 1) if hum else None,
        "media_ia": round(sum(ia) / len(ia), 1) if ia else None,
        "alvo_atual": score.ALVO,
        "discriminacao_por_componente": disc,
    }


def _emitir_baseline(dir_corpus):
    rel = relatorio_baseline(dir_corpus)
    with open(os.path.join(dir_corpus, "baseline-report.json"), "w", encoding="utf-8") as f:
        json.dump(rel, f, ensure_ascii=False, indent=2)
    linhas = [
        "# Relatório de separação baseline (pesos atuais)", "",
        f"- Amostras: {rel['n_humano']} humano / {rel['n_ia']} IA",
        f"- AUC total: **{rel['auc_total']}**",
        f"- Média do score: humano {rel['media_humano']} vs IA {rel['media_ia']} (alvo {rel['alvo_atual']})",
        "", "## Poder discriminativo por componente (AUC univariado)", "",
        "| Componente | AUC |", "| --- | --- |",
    ]
    linhas += [f"| {k} | {v} |" for k, v in sorted(
        rel["discriminacao_por_componente"].items(), key=lambda kv: -kv[1])]
    with open(os.path.join(dir_corpus, "baseline-report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    print(f"baseline: AUC {rel['auc_total']} | humano {rel['media_humano']} vs IA {rel['media_ia']}")


def _emitir_fit(dir_corpus):
    raise NotImplementedError("Task 5")


def main():
    dir_corpus = "../../references/Corpus"
    if "--dir" in sys.argv:
        dir_corpus = sys.argv[sys.argv.index("--dir") + 1]
    if "--baseline" in sys.argv:
        _emitir_baseline(dir_corpus)
    elif "--fit" in sys.argv:
        _emitir_fit(dir_corpus)  # definido na Task 5
    else:
        print("uso: calibrar.py [--baseline|--fit] [--dir <corpus>]")


if __name__ == "__main__":
    main()
