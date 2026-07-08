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


class TestBurstinessGB(unittest.TestCase):
    def test_uniforme_da_menos_um(self):
        # sigma = 0 => B = (0 - mu)/(0 + mu) = -1
        self.assertAlmostEqual(
            metricas.burstiness_goh_barabasi([10, 10, 10, 10]), -1.0, places=6)

    def test_bursty_maior_que_uniforme(self):
        bursty = metricas.burstiness_goh_barabasi([2, 35, 4, 28, 3, 40, 5])
        quase_uniforme = metricas.burstiness_goh_barabasi([10, 11, 10, 9, 10, 11, 10])
        self.assertGreater(bursty, quase_uniforme)

    def test_faixa(self):
        b = metricas.burstiness_goh_barabasi([2, 35, 4, 28, 3])
        self.assertGreaterEqual(b, -1.0)
        self.assertLess(b, 1.0)

    def test_poucas_sentencas_inaplicavel(self):
        self.assertIsNone(metricas.burstiness_goh_barabasi([5, 20]))


class TestAutocorrelacaoLag1(unittest.TestCase):
    def test_alternancia_e_negativa(self):
        # longa-curta-longa-curta: vizinhos anticorrelacionados
        r = metricas.autocorrelacao_lag1([30, 5, 28, 4, 31, 6, 29, 5])
        self.assertLess(r, 0.0)

    def test_tendencia_e_positiva(self):
        r = metricas.autocorrelacao_lag1([5, 8, 11, 14, 17, 20, 23, 26])
        self.assertGreater(r, 0.0)

    def test_constante_inaplicavel(self):
        self.assertIsNone(metricas.autocorrelacao_lag1([10, 10, 10, 10, 10]))

    def test_poucas_sentencas_inaplicavel(self):
        self.assertIsNone(metricas.autocorrelacao_lag1([5, 20, 8]))


class TestZipfAjuste(unittest.TestCase):
    def _zipfiano(self):
        # frequências ~ 1/rank: palavra0 x60, palavra1 x30, palavra2 x20...
        palavras = []
        for r in range(1, 21):
            palavras += [f"palavra{r}"] * max(1, 60 // r)
        return palavras

    def test_slope_negativo_e_r2_alto_em_distribuicao_zipfiana(self):
        resultado = metricas.zipf_ajuste(self._zipfiano())
        self.assertIsNotNone(resultado)
        inclinacao, r2 = resultado
        self.assertLess(inclinacao, -0.5)
        self.assertGreater(r2, 0.9)

    def test_uniforme_tem_r2_menor(self):
        uniforme = [f"palavra{i % 25}" for i in range(200)]
        _, r2_uni = metricas.zipf_ajuste(uniforme)
        _, r2_zipf = metricas.zipf_ajuste(self._zipfiano())
        self.assertLess(r2_uni, r2_zipf)

    def test_poucas_palavras_inaplicavel(self):
        self.assertIsNone(metricas.zipf_ajuste(["a"] * 49))
        self.assertIsNone(metricas.zipf_ajuste(["a", "b"] * 30))  # < 10 types
