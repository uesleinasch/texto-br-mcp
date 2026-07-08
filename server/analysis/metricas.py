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
