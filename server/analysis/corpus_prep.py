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


_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_URL_CORTADA_RE = re.compile(r"(?:https?://|www\.)\S*-$")  # URL hifenizada no fim
_ACENTO_RE = re.compile(r"[À-ÿ]")


def _eh_fragmento_url(token):
    """True se o token parece a continuação de um caminho de URL quebrado pelo
    pdftotext (contém '/', sem espaços, sem acento pt-BR, charset de path). NÃO
    trata fração de página ('1/18'). Conservador para não pegar 'CI/CD', 'e/ou'."""
    return (
        "/" in token
        and re.fullmatch(r"\d+\s*/\s*\d+", token) is None
        and _ACENTO_RE.search(token) is None
        and re.fullmatch(r"[\w][\w./%-]*", token) is not None
    )


def limpar_boilerplate(texto):
    """Remove capa/marca, URLs, números/frações de página e mobília periódica.

    Em PDFs web-print o cabeçalho (data + título) e o rodapé (URL + fração de
    página tipo "1/18") se repetem a cada página. URLs longas são quebradas pelo
    pdftotext em várias linhas; por isso NÃO descartamos a linha inteira que
    contém URL (isso truncaria a prosa e deixaria a cauda da URL órfã). Em vez
    disso: (1) removemos o token de URL inline, preservando a prosa ao redor, e
    só descartamos a linha se o que sobrar for vazio/pontuação; (2) quando uma
    URL é hifenizada no fim da linha, descartamos o fragmento de caminho que
    inicia a linha seguinte (a cauda da URL); (3) removemos frações de página no
    fim; (4) fazemos dedupe de linhas que se repetem 3+ vezes (mobília
    periódica). Prosa real quase nunca repete uma linha verbatim 3+ vezes; um
    refrão com < 3 ocorrências é preservado."""
    linhas_brutas = texto.split("\n")
    # contagem por linha (stripped, não vazia) para o dedupe de mobília periódica
    contagem = Counter(s for s in (l.strip() for l in linhas_brutas) if s)
    linhas = []
    esperar_cauda = False  # linha anterior terminou com URL hifenizada
    for linha in linhas_brutas:
        s = linha.strip()
        if not s:
            linhas.append("")
            continue
        if contagem[s] >= 3:
            esperar_cauda = False
            continue  # cabeçalho/rodapé periódico repetido
        if re.fullmatch(r"\d{1,4}", s):
            esperar_cauda = False
            continue  # número de página solto
        if re.search(r"\d+\s*/\s*\d+\s*$", s):
            esperar_cauda = False
            continue  # fração de página no fim da linha ("1/18")
        if re.fullmatch(r"[-—_·•]{1,}", s):
            esperar_cauda = False
            continue  # régua/ornamento

        texto_linha = s
        modificada = False

        # (2) cauda de URL quebrada: fragmento de caminho no início desta linha
        if esperar_cauda:
            partes = texto_linha.split(None, 1)
            cabeca = partes[0].rstrip(".,;:") if partes else ""
            if cabeca and _eh_fragmento_url(cabeca):
                texto_linha = partes[1] if len(partes) > 1 else ""
                modificada = True
                if not texto_linha.strip():
                    esperar_cauda = False
                    continue
        esperar_cauda = False

        # fragmento de caminho de URL isolado ocupando a linha inteira
        if (" " not in texto_linha and "/" in texto_linha
                and re.fullmatch(r"\d+\s*/\s*\d+", texto_linha) is None
                and _ACENTO_RE.search(texto_linha) is None
                and re.fullmatch(r"[\w][\w./%-]*", texto_linha) is not None
                and (len(texto_linha) >= 12 or "." in texto_linha)):
            continue

        # (1) remove URLs inline preservando a prosa ao redor
        if _URL_RE.search(texto_linha):
            esperar_cauda = bool(_URL_CORTADA_RE.search(texto_linha))
            texto_linha = re.sub(r"\s+", " ", _URL_RE.sub(" ", texto_linha)).strip()
            modificada = True
            if not texto_linha or re.fullmatch(r"\W+", texto_linha):
                continue  # linha era só URL/pontuação

        linhas.append(texto_linha if modificada else linha)
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
