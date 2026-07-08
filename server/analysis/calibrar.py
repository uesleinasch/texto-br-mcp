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
import statistics
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
    """Baseline com os pesos MANUAIS (fixos, pré-calibração) — reproduzível do
    repo independente do estado atual de score.PESOS (que Task 6 congelou nos
    valores calibrados)."""
    X, y, nomes, chaves = matriz_features(dir_corpus, secao10)
    scores = [score_ponderado(x, score.PESOS_MANUAIS, chaves) for x in X]
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


def padronizar(X):
    d = len(X[0])
    medias = [sum(row[j] for row in X) / len(X) for j in range(d)]
    desvios = []
    for j in range(d):
        var = sum((row[j] - medias[j]) ** 2 for row in X) / len(X)
        desvios.append(math.sqrt(var) or 1.0)  # evita divisão por zero
    Xs = [[(row[j] - medias[j]) / desvios[j] for j in range(d)] for row in X]
    return Xs, medias, desvios


def treinar_logistica(Xs, y, prior, l2=1.0, lr=0.3, iteracoes=3000):
    """Regressão logística por gradiente descendente, determinística (init em
    `prior`). L2 puxa os coeficientes para `prior` (conservador), não para 0."""
    n, d = len(Xs), len(Xs[0])
    w = list(prior)
    b = 0.0
    for _ in range(iteracoes):
        gw = [0.0] * d
        gb = 0.0
        for i in range(n):
            z = b + sum(w[j] * Xs[i][j] for j in range(d))
            p = 1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z))))
            err = p - y[i]
            for j in range(d):
                gw[j] += err * Xs[i][j]
            gb += err
        for j in range(d):
            w[j] -= lr * (gw[j] / n + l2 * (w[j] - prior[j]) / n)
        b -= lr * (gb / n)
    return w, b


def coef_para_pesos(coef, chaves, piso=2.0):
    """Mapeia a contribuição discriminativa (coef positivo = sinal indica humano)
    para 100 pontos, com piso por componente (preserva o breakdown) e soma 100.
    Coeficiente <= 0 (sinal que não indica humano no corpus) fica só no piso —
    não se recompensa um sinal anticorrelacionado. Caso degenerado (nenhum
    coeficiente positivo): distribui os 100 pontos uniformemente entre as chaves."""
    contrib = [max(0.0, c) for c in coef]
    if not any(contrib):
        # Caso degenerado: nenhum sinal com evidência positiva no corpus.
        # Sem base para diferenciar, distribui uniformemente (não despeja o
        # resíduo num único componente arbitrário).
        uniforme = round(100.0 / len(chaves), 1)
        pesos = {k: uniforme for k in chaves}
        resto = round(100.0 - sum(pesos.values()), 1)
        kfirst = chaves[0]
        pesos[kfirst] = round(pesos[kfirst] + resto, 1)
        return pesos
    total = sum(contrib)
    livre = 100.0 - piso * len(chaves)
    brutos = {k: piso + livre * (contrib[i] / total) for i, k in enumerate(chaves)}
    # arredonda para 1 casa e corrige o resíduo no maior peso
    pesos = {k: round(v, 1) for k, v in brutos.items()}
    resto = round(100.0 - sum(pesos.values()), 1)
    kmax = max(pesos, key=pesos.get)
    pesos[kmax] = round(pesos[kmax] + resto, 1)
    return pesos


def separacao_loocv(dir_corpus):
    """AUC honesto: para cada amostra, treina nos N-1 restantes e prevê a que
    ficou de fora. Reflete generalização, não ajuste in-sample."""
    X, y, nomes, chaves = matriz_features(dir_corpus)
    # prior fixo (pesos manuais, não os calibrados) — cada fold não pode ver
    # informação derivada do corpus inteiro, senão vaza held-out para o prior.
    prior = [score.PESOS_MANUAIS[k] / 10.0 for k in chaves]
    preditos = []
    for i in range(len(X)):
        Xtr = [X[j] for j in range(len(X)) if j != i]
        ytr = [y[j] for j in range(len(X)) if j != i]
        Xs, medias, desvios = padronizar(Xtr)
        w, b = treinar_logistica(Xs, ytr, prior=prior, l2=1.0, lr=0.3, iteracoes=1500)
        xi = [(X[i][j] - medias[j]) / desvios[j] for j in range(len(chaves))]
        z = b + sum(w[j] * xi[j] for j in range(len(chaves)))
        preditos.append(1.0 / (1.0 + math.exp(-max(-60.0, min(60.0, z)))))
    return round(auc(preditos, y), 3)


def melhor_alvo(scores, labels):
    """Threshold que maximiza o índice J de Youden (TPR - FPR)."""
    candidatos = sorted(set(scores))
    pos = sum(labels)
    neg = len(labels) - pos
    melhor, melhor_j = candidatos[0], -1.0
    for t in candidatos:
        tp = sum(1 for s, l in zip(scores, labels) if l == 1 and s >= t)
        fp = sum(1 for s, l in zip(scores, labels) if l == 0 and s >= t)
        tpr = tp / pos if pos else 0.0
        fpr = fp / neg if neg else 0.0
        j = tpr - fpr
        if j > melhor_j:
            melhor_j, melhor = j, t
    return round(melhor, 1)


def p75_humano(scores, labels):
    """Percentil 75 dos scores humanos (label 1) sob os pesos calibrados.
    Usa statistics.quantiles(..., n=4, method="inclusive")[2] — interpolação
    linear padrão (equivalente a PERCENTILE.INC/numpy default), determinística
    e estável a partir da própria stdlib."""
    hum = sorted(s for s, l in zip(scores, labels) if l == 1)
    if len(hum) < 2:
        return round(hum[0], 1) if hum else float("nan")
    return round(statistics.quantiles(hum, n=4, method="inclusive")[2], 1)


def _emitir_fit(dir_corpus):
    X, y, nomes, chaves = matriz_features(dir_corpus)
    Xs, medias, desvios = padronizar(X)
    # prior fixo (pesos manuais) — reproduz os pesos congelados em score.PESOS
    # independente de recalibrações futuras. Escala do prior no espaço padronizado.
    prior = [score.PESOS_MANUAIS[k] / 10.0 for k in chaves]
    w, b = treinar_logistica(Xs, y, prior=prior, l2=1.0, lr=0.3, iteracoes=3000)
    pesos = coef_para_pesos(w, chaves, piso=2.0)
    scores = [score_ponderado(x, pesos, chaves) for x in X]
    alvo_youden = melhor_alvo(scores, y)
    alvo_p75 = p75_humano(scores, y)
    saida = {
        "pesos": pesos, "chaves": chaves,
        "alvo_youden": alvo_youden,
        "alvo_p75_humano": alvo_p75,
        "alvo_politica": "p75_humano",
        "auc_calibrado_in_sample": round(auc(scores, y), 3),
        "coeficientes_padronizados": {k: round(w[i], 4) for i, k in enumerate(chaves)},
    }
    with open(os.path.join(dir_corpus, "pesos-calibrados.json"), "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"fit: AUC in-sample {saida['auc_calibrado_in_sample']} | alvo_youden {alvo_youden} | "
          f"alvo_p75_humano {alvo_p75}")
    print("pesos:", json.dumps(pesos, ensure_ascii=False))


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
