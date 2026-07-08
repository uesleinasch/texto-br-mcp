#!/usr/bin/env python3
"""Gera server/analysis/referencia_humana.json a partir do lado humano do
corpus (classe "humano" com incluir_calibracao true). Offline, stdlib,
determinístico: mesmo corpus => mesmo artefato byte-a-byte.

Uso: python3 referencia_prep.py [--dir ../../references/Corpus]
"""
import json
import os
import sys

import metricas

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "referencia_humana.json")


def textos_humanos(dir_corpus):
    with open(os.path.join(dir_corpus, "manifest.json"), encoding="utf-8") as f:
        manifesto = json.load(f)
    textos = []
    for e in manifesto:
        if e["classe"] == "humano" and e["incluir_calibracao"]:
            with open(os.path.join(dir_corpus, e["arquivo"]), encoding="utf-8") as f:
                textos.append(f.read())
    return textos


def main():
    dir_corpus = "../../references/Corpus"
    if "--dir" in sys.argv:
        dir_corpus = sys.argv[sys.argv.index("--dir") + 1]
    textos = textos_humanos(dir_corpus)
    ref = metricas.construir_referencia(textos)
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(ref, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    print(f"referência: {ref['n_textos']} textos humanos, "
          f"{len(ref['logprobs'])} trigramas, {len(ref['funcionais'])} funcionais -> {SAIDA}")


if __name__ == "__main__":
    main()
