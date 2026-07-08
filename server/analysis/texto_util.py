"""Utilitários comuns aos analisadores do texto-br (limpeza e tokenização)."""

import re

ABREVIACOES = [
    "Sr.", "Sra.", "Srta.", "Dr.", "Dra.", "Prof.", "Profa.",
    "etc.", "ex.", "p.", "pp.", "n.", "av.", "tel.", "obs.",
    "vs.", "a.C.", "d.C.", "S.A.", "fig.", "cap.", "art.", "séc.",
]

# A1: fronteira de palavra antes da abreviação + case-insensitive.
# Ordena por comprimento (desc) para "S.A." casar antes de "a.".
_ABREV_RE = [
    (i, re.compile(r"(?<![\wÀ-ÿ])" + re.escape(a), re.IGNORECASE))
    for i, a in sorted(enumerate(ABREVIACOES), key=lambda t: -len(t[1]))
]

# A2/A6: fim de sentença = pontuação final + fechadores opcionais + espaço,
# somente quando a próxima sentença começa com maiúscula, dígito ou abertura
# de citação (reticência seguida de minúscula é intra-sentencial; atribuição
# de fala após travessão continua na mesma sentença).
_FIM_SENTENCA = re.compile(
    r"([.!?…]+[\"»”'\)\]]*)\s+(?=[A-ZÀ-Ý0-9«“\"'(¿])"
)


def limpar_markdown(texto):
    """Remove estruturas de markdown que não são prosa analisável.

    Cercas de código rastreiam o delimitador de abertura (mesma lógica do
    parser.js): uma cerca de N caracteres só fecha com o mesmo caractere e
    comprimento >= N, permitindo cercas de 3 backticks dentro de cercas de 4.
    """
    linhas = []
    cerca_aberta = None
    excluidas = 0
    for linha in texto.split("\n"):
        m = re.match(r"^\s*(`{3,}|~{3,})", linha)
        if m:
            if cerca_aberta is None:
                cerca_aberta = m.group(1)
            elif m.group(1)[0] == cerca_aberta[0] and len(m.group(1)) >= len(cerca_aberta):
                cerca_aberta = None
            excluidas += 1
            continue
        if cerca_aberta is not None:
            excluidas += 1
            continue
        # headings, itens de lista, tabelas e separadores não são sentenças de prosa
        if re.match(r"^\s*(#{1,6}\s|[-*+]\s|\d{1,2}[.)]\s|\||---+\s*$|>)", linha):
            excluidas += 1
            continue
        linhas.append(linha)
    texto = "\n".join(linhas)
    texto = re.sub(r"`[^`]*`", "", texto)  # inline code
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", texto)  # imagens
    texto = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", texto)  # links -> texto
    texto = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", texto)  # ênfase com *
    texto = re.sub(
        r"(?<![\wÀ-ÿ])_{1,3}([^_]+?)_{1,3}(?![\wÀ-ÿ])", r"\1", texto
    )  # ênfase com _ apenas em fronteira de palavra
    return texto, excluidas


def dividir_paragrafos(texto):
    return [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]


def dividir_sentencas(paragrafo):
    protegido = paragrafo.replace("\n", " ")
    for i, rx in _ABREV_RE:
        protegido = rx.sub(f"\x00{i}\x00", protegido)
    partes = _FIM_SENTENCA.split(protegido)
    # re.split com 1 grupo de captura alterna [corpo, separador, corpo, ...]
    brutas = []
    for j in range(0, len(partes), 2):
        corpo = partes[j]
        sep = partes[j + 1] if j + 1 < len(partes) else ""
        brutas.append(corpo + sep)
    sentencas = []
    for parte in brutas:
        for i, _ in _ABREV_RE:
            parte = parte.replace(f"\x00{i}\x00", ABREVIACOES[i])
        parte = parte.strip()
        if parte and contar_palavras(parte) > 0:
            sentencas.append(parte)
    return sentencas


def contar_palavras(sentenca):
    return len(re.findall(r"[\wÀ-ÿ]+(?:[-'][\wÀ-ÿ]+)*", sentenca))


def listar_palavras(texto):
    return re.findall(r"[\wÀ-ÿ]+(?:[-'][\wÀ-ÿ]+)*", texto.lower())


def excerto(sentenca, limite=70):
    return sentenca if len(sentenca) <= limite else sentenca[: limite - 1] + "…"


def parsear_blocos(texto):
    """Lista ordenada de blocos do markdown: heading, paragrafo, lista, codigo,
    citacao. Reusa a lógica de cerca de limpar_markdown (a cerca fecha só com o
    mesmo caractere e comprimento >= o de abertura)."""
    blocos = []
    cerca_aberta = None
    buffer_codigo = []
    buffer_prosa = []

    def fechar_prosa():
        if buffer_prosa:
            texto_p = "\n".join(buffer_prosa).strip()
            if texto_p:
                blocos.append({"tipo": "paragrafo", "nivel": 0, "texto": texto_p})
            buffer_prosa.clear()

    for linha in texto.split("\n"):
        m_cerca = re.match(r"^\s*(`{3,}|~{3,})", linha)
        if m_cerca:
            if cerca_aberta is None:
                fechar_prosa()
                cerca_aberta = m_cerca.group(1)
                buffer_codigo = []
            elif m_cerca.group(1)[0] == cerca_aberta[0] and len(m_cerca.group(1)) >= len(cerca_aberta):
                blocos.append({"tipo": "codigo", "nivel": 0, "texto": "\n".join(buffer_codigo)})
                cerca_aberta = None
            continue
        if cerca_aberta is not None:
            buffer_codigo.append(linha)
            continue
        m_h = re.match(r"^\s*(#{1,6})\s+(.*)$", linha)
        if m_h:
            fechar_prosa()
            blocos.append({"tipo": "heading", "nivel": len(m_h.group(1)), "texto": m_h.group(2).strip()})
            continue
        if re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", linha):
            fechar_prosa()
            continue
        if re.match(r"^\s*([-*+]\s|\d{1,2}[.)]\s)", linha):
            fechar_prosa()
            blocos.append({"tipo": "lista", "nivel": 0, "texto": linha.strip()})
            continue
        if re.match(r"^\s*>", linha):
            fechar_prosa()
            blocos.append({"tipo": "citacao", "nivel": 0, "texto": linha.lstrip("> ").strip()})
            continue
        if linha.strip() == "":
            fechar_prosa()
            continue
        buffer_prosa.append(linha)
    fechar_prosa()
    return blocos
