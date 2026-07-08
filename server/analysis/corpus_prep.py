#!/usr/bin/env python3
"""Preprocessamento do corpus rotulado (offline). Extrai PDFs via pdftotext,
limpa boilerplate, detecta gênero e monta references/Corpus/manifest.json.

Uso: python3 corpus_prep.py [--dir ../../references/Corpus]
Requer o binário `pdftotext` (poppler) no PATH para os .pdf."""

import json
import os
import re
import subprocess
import sys
from collections import Counter

TIPOS_VALIDOS = [
    "blog", "tecnico", "corporativo", "email", "capitulo", "podcast", "video",
    "explicativo", "geral", "comentario-blog", "comentario-jira", "chat",
]


def extrair_pdf(caminho):
    """Extrai texto de um PDF via pdftotext -layout. Levanta se pdftotext faltar."""
    try:
        out = subprocess.run(
            ["pdftotext", "-layout", caminho, "-"],
            capture_output=True, text=True, check=True,
        )
    except FileNotFoundError:
        raise RuntimeError("pdftotext não encontrado no PATH (instale poppler-utils).")
    return out.stdout


def limpar_boilerplate(texto):
    """Remove capa/marca, URLs, números/frações de página e mobília periódica.

    Em PDFs web-print o cabeçalho (data + título) e o rodapé (URL + fração de
    página tipo "1/18") se repetem a cada página, muitas vezes colados na mesma
    linha que conteúdo. Além das linhas que são só ruído, removemos qualquer
    linha que contenha URL ou fração de página no fim, e qualquer linha que se
    repita 3+ vezes no documento (cabeçalho/rodapé periódico). Prosa real quase
    nunca repete uma linha verbatim 3+ vezes; um refrão que apareça < 3 vezes é
    preservado."""
    linhas_brutas = texto.split("\n")
    # contagem por linha (stripped, não vazia) para o dedupe de mobília periódica
    contagem = Counter(s for s in (l.strip() for l in linhas_brutas) if s)
    linhas = []
    for linha in linhas_brutas:
        s = linha.strip()
        if not s:
            linhas.append("")
            continue
        if re.search(r"https?://|www\.", s):
            continue  # URL (marca / rodapé de print) em qualquer posição da linha
        if re.fullmatch(r"\d{1,4}", s):
            continue  # número de página solto
        if re.search(r"\d+\s*/\s*\d+\s*$", s):
            continue  # fração de página no fim da linha ("1/18")
        if re.fullmatch(r"[-—_·•]{1,}", s):
            continue  # régua/ornamento
        if contagem[s] >= 3:
            continue  # cabeçalho/rodapé periódico repetido
        linhas.append(linha)
    # colapsa 3+ quebras em 2
    return re.sub(r"\n{3,}", "\n\n", "\n".join(linhas)).strip()


def _palavras(texto):
    return re.findall(r"[\wÀ-ÿ]+(?:[-'][\wÀ-ÿ]+)*", texto)


def detectar_genero(texto):
    """Heurística: poesia = muitas linhas curtas com quebra deliberada."""
    linhas = [l for l in texto.split("\n") if l.strip()]
    if len(linhas) < 3:
        return "prosa"
    palavras_por_linha = [len(_palavras(l)) for l in linhas]
    curtas = sum(1 for n in palavras_por_linha if 1 <= n <= 9)
    frac_curtas = curtas / len(linhas)
    tem_pontuacao_final = sum(l.rstrip()[-1:] in ".!?…" for l in linhas) / len(linhas)
    # muitas linhas curtas + poucas terminando em pontuação de sentença => verso
    if frac_curtas >= 0.6 and tem_pontuacao_final < 0.4:
        return "poesia"
    return "prosa"


def entrada_manifesto(arquivo, classe, genero, tipo, palavras, fonte,
                      data_verificada, data_coleta):
    return {
        "arquivo": arquivo,
        "classe": classe,
        "genero": genero,
        "tipo": tipo if tipo in TIPOS_VALIDOS else "desconhecido",
        "palavras": palavras,
        "incluir_calibracao": genero == "prosa" and palavras >= 30,
        "fonte": fonte,
        "data_verificada": data_verificada,
        "data_coleta": data_coleta,
    }


def _ler_texto(caminho):
    if caminho.lower().endswith(".pdf"):
        return limpar_boilerplate(extrair_pdf(caminho))
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def construir_manifesto(dir_corpus, data_coleta="2026-07-08"):
    """Percorre Human/ e IA/, extrai PDFs para .txt, e monta o manifesto."""
    entradas = []
    for classe, sub in (("humano", "Human"), ("ia", "IA")):
        d = os.path.join(dir_corpus, sub)
        if not os.path.isdir(d):
            continue
        for nome in sorted(os.listdir(d)):
            if nome.startswith(".") or nome.endswith(".txt"):
                continue
            caminho = os.path.join(d, nome)
            if not os.path.isfile(caminho):
                continue
            texto = _ler_texto(caminho)
            arquivo_rel = f"{sub}/{nome}"
            if nome.lower().endswith(".pdf"):
                txt_path = os.path.splitext(caminho)[0] + ".txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(texto)
                arquivo_rel = f"{sub}/{os.path.basename(txt_path)}"
            fonte = "gerado" if classe == "ia" else "local"
            entradas.append(entrada_manifesto(
                arquivo=arquivo_rel, classe=classe,
                genero=detectar_genero(texto), tipo="desconhecido",
                palavras=len(_palavras(texto)), fonte=fonte,
                data_verificada=None, data_coleta=data_coleta,
            ))
    manifesto_path = os.path.join(dir_corpus, "manifest.json")
    with open(manifesto_path, "w", encoding="utf-8") as f:
        json.dump(entradas, f, ensure_ascii=False, indent=2)
    return entradas


def main():
    dir_corpus = "../../references/Corpus"
    if "--dir" in sys.argv:
        dir_corpus = sys.argv[sys.argv.index("--dir") + 1]
    entradas = construir_manifesto(dir_corpus)
    incl = sum(1 for e in entradas if e["incluir_calibracao"])
    print(f"{len(entradas)} textos; {incl} elegíveis para calibração.")
    for c in ("humano", "ia"):
        n = sum(1 for e in entradas if e["classe"] == c and e["incluir_calibracao"])
        print(f"  {c}: {n} de prosa elegíveis")


if __name__ == "__main__":
    main()
