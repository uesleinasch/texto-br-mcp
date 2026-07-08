"""Métricas stdlib da Etapa 4 para o detector de texto-IA.

Funções puras e determinísticas; sem numpy, sem I/O, sem fitting. As que
exigem estatísticas de referência (burrows_delta, cross_entropy_trigramas)
recebem a referência como parâmetro: o runtime passa o artefato congelado
(referencia_humana.json) e a calibração passa a referência do fold — mesma
função, zero vazamento no LOO-CV.

Convenção de inaplicabilidade: texto/lista aquém do mínimo estatístico da
métrica retorna None (o chamador mapeia para o sinal neutro 0.5).
"""
import math
import zlib
from collections import Counter

from texto_util import limpar_markdown, listar_palavras


def razao_compressao(texto):
    """Bytes comprimidos / bytes crus (zlib nível 9, UTF-8). Texto repetitivo
    comprime mais (razão menor); prosa humana variada comprime menos.
    None se < 200 bytes."""
    dados = texto.encode("utf-8")
    if len(dados) < 200:
        return None
    return len(zlib.compress(dados, 9)) / len(dados)


def yule_k(palavras):
    """Yule's K = 10^4 * (sum(m^2 * V_m) - N) / N^2, onde V_m é o número de
    types com frequência m e N o total de tokens. K menor = vocabulário mais
    rico; robusto ao tamanho do texto. None se < 50 palavras."""
    n = len(palavras)
    if n < 50:
        return None
    freq = Counter(palavras)
    vm = Counter(freq.values())
    s2 = sum(m * m * v for m, v in vm.items())
    return 1e4 * (s2 - n) / (n * n)


def burstiness_goh_barabasi(comprimentos):
    """Burstiness de Goh–Barabási: B = (sigma - mu)/(sigma + mu) sobre os
    comprimentos de sentença, limitado em [-1, 1). Complementa o sigma/mu de
    variancia.py: B é limitado e comparável entre textos de escalas diferentes.
    None se < 3 sentenças."""
    if len(comprimentos) < 3:
        return None
    mu = sum(comprimentos) / len(comprimentos)
    var = sum((c - mu) ** 2 for c in comprimentos) / len(comprimentos)
    sigma = math.sqrt(var)
    if sigma + mu == 0:
        return None
    return (sigma - mu) / (sigma + mu)


def autocorrelacao_lag1(comprimentos):
    """Autocorrelação de lag 1 dos comprimentos de sentença: escrita humana
    tende a alternar longa/curta (anticorrelação); texto uniforme ou em rampa
    monótona não. None se < 4 sentenças ou variância zero."""
    n = len(comprimentos)
    if n < 4:
        return None
    mu = sum(comprimentos) / n
    den = sum((c - mu) ** 2 for c in comprimentos)
    if den == 0:
        return None
    num = sum(
        (comprimentos[i] - mu) * (comprimentos[i + 1] - mu) for i in range(n - 1)
    )
    return num / den


def zipf_ajuste(palavras):
    """Ajuste de mínimos quadrados de log(freq) ~ log(rank) sobre a
    distribuição de frequências. Retorna (inclinacao, r2): inclinacao ~ -1 e
    r2 alto = aderência à lei de Zipf. None se < 50 palavras ou < 10 types."""
    if len(palavras) < 50:
        return None
    freqs = sorted(Counter(palavras).values(), reverse=True)
    if len(freqs) < 10:
        return None
    xs = [math.log(r) for r in range(1, len(freqs) + 1)]
    ys = [math.log(f) for f in freqs]
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    ss_res = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return b, r2


# Palavras funcionais pt-BR para o Burrows' Delta: itens gramaticais de alta
# frequência, quase livres de conteúdo — o perfil de uso é assinatura de
# autoria/registro, não de assunto. Lista fixa e congelada (ordem estável).
PALAVRAS_FUNCIONAIS = [
    "a", "à", "ainda", "além", "ao", "aos", "aquilo", "as", "às", "até",
    "cada", "com", "como", "contra", "da", "das", "de", "depois", "desde",
    "dessa", "desse", "do", "dos", "e", "é", "ela", "ele", "em", "embora",
    "enquanto", "entre", "era", "essa", "esse", "esta", "este", "eu", "foi",
    "há", "isso", "isto", "já", "mais", "mas", "menos", "mesmo", "minha",
    "muito", "na", "nas", "nem", "no", "nos", "nós", "não", "ou", "outra",
    "outro", "para", "pela", "pelas", "pelo", "pelos", "por", "porque",
    "pouco", "quando", "quase", "que", "se", "sem", "ser", "seu", "sob",
    "sobre", "sua", "são", "também", "tanto", "todo", "toda", "tão", "um",
    "uma", "você",
]


def frequencias_funcionais(palavras, funcionais):
    """Frequência relativa de cada palavra funcional no texto (tokens já em
    minúsculas, via texto_util.listar_palavras). None se a lista for vazia."""
    n = len(palavras)
    if n == 0:
        return None
    contagem = Counter(p for p in palavras if p in set(funcionais))
    return {w: contagem.get(w, 0) / n for w in funcionais}


def _trigramas_char(texto):
    """Char-trigramas do texto normalizado (minúsculas, espaços colapsados)."""
    limpo = " ".join(texto.lower().split())
    return [limpo[i:i + 3] for i in range(len(limpo) - 2)]


def construir_referencia(textos, top_n=5000):
    """Estatísticas de referência 'humanas' a partir de textos crus (markdown
    é limpo aqui dentro): modelo de char-trigramas com suavização de Laplace
    (top_n mais frequentes; o resto cai em logp_oov) e média/desvio da
    frequência relativa de cada palavra funcional por texto. Mesma função
    para o artefato congelado do runtime e para a referência por fold do
    LOO-CV (calibrar.py) — determinística."""
    limpos = [limpar_markdown(t)[0] for t in textos]
    contagem = Counter()
    for t in limpos:
        contagem.update(_trigramas_char(t))
    vocab = len(contagem)
    total = sum(contagem.values())
    mais = sorted(contagem.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
    logprobs = {
        tri: math.log((c + 1) / (total + vocab))
        for tri, c in sorted(mais)
    }
    logp_oov = math.log(1.0 / (total + vocab))
    por_texto = [
        f for f in (
            frequencias_funcionais(listar_palavras(t), PALAVRAS_FUNCIONAIS)
            for t in limpos
        ) if f is not None
    ]
    funcionais = {}
    for w in PALAVRAS_FUNCIONAIS:
        valores = [f[w] for f in por_texto]
        media = sum(valores) / len(valores)
        var = sum((v - media) ** 2 for v in valores) / len(valores)
        funcionais[w] = {"media": media, "desvio": math.sqrt(var)}
    return {
        "logprobs": logprobs,
        "logp_oov": logp_oov,
        "funcionais": funcionais,
        "n_textos": len(textos),
        "top_n": top_n,
    }
