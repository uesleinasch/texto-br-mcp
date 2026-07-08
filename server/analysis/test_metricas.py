"""Testes unitários das métricas stdlib da Etapa 4."""
import unittest

import metricas

VARIADO = (
    "O mercado abriu em queda acentuada naquela manhã fria de setembro. "
    "Ninguém esperava. Os operadores, atônitos diante das telas vermelhas, "
    "tentavam entender a origem do movimento brusco que derrubava os índices. "
    "Uma trader saiu para fumar. Voltou dez minutos depois com outra teoria, "
    "menos plausível que a primeira, sobre juros americanos e safra de grãos. "
    "O silêncio da tarde contrastava com o caos das primeiras horas do pregão."
)
REPETITIVO = ("A empresa oferece soluções completas para o cliente moderno. " * 12)


class TestRazaoCompressao(unittest.TestCase):
    def test_repetitivo_comprime_mais_que_variado(self):
        rv = metricas.razao_compressao(VARIADO)
        rr = metricas.razao_compressao(REPETITIVO)
        self.assertLess(rr, rv)

    def test_faixa_e_determinismo(self):
        r1 = metricas.razao_compressao(VARIADO)
        r2 = metricas.razao_compressao(VARIADO)
        self.assertEqual(r1, r2)
        self.assertGreater(r1, 0.0)
        self.assertLess(r1, 1.0)

    def test_texto_curto_inaplicavel(self):
        self.assertIsNone(metricas.razao_compressao("Curto demais."))


class TestYuleK(unittest.TestCase):
    def test_vocabulario_pobre_tem_k_maior(self):
        rico = VARIADO.lower().split()
        pobre = ("a empresa oferece valor para o cliente " * 10).split()
        self.assertGreater(metricas.yule_k(pobre), metricas.yule_k(rico))

    def test_poucas_palavras_inaplicavel(self):
        self.assertIsNone(metricas.yule_k(["palavra"] * 49))

    def test_todas_unicas_da_zero(self):
        palavras = [f"palavra{i}" for i in range(100)]
        self.assertAlmostEqual(metricas.yule_k(palavras), 0.0, places=6)
