"""Testes do score: regressão do refactor de sinais e comportamento congelado."""
import unittest

import score

TEXTO_BOM = (
    "O mercado abriu em queda acentuada. Ninguém esperava aquilo depois de uma "
    "semana inteira de otimismo com os índices lá fora batendo recorde atrás de "
    "recorde sem parar. Vendas despencaram. O pregão virou um caos de ordens "
    "canceladas e telefones tocando nas mesas de operação da corretora. "
    "Alguns traders saíram mais cedo. O silêncio no fim do dia dizia tudo sobre "
    "o tamanho do estrago que ficou para trás. E agora, quem paga a conta? "
    "Analistas divergem sobre os próximos passos do banco central brasileiro. "
    "Uns preveem recuperação rápida puxada pelo consumo interno das famílias. "
    "Outros, mais cautelosos, apostam num ajuste longo e doloroso pela frente."
)
SECAO10 = (
    "### 10.1 Verbos pivot\n| Evitar | Trocar por |\n|---|---|\n| abordar | tratar de |\n"
    "### 10.4 Conectores\n| Evitar | Trocar por |\n| além disso | e |\n"
)


class TestSinais(unittest.TestCase):
    def test_sinais_tem_todas_as_chaves_normalizadas(self):
        import variancia, lexico
        ritmo = variancia.analisar(TEXTO_BOM)
        lex = lexico.analisar(TEXTO_BOM, SECAO10)
        s = score.sinais(ritmo, lex, TEXTO_BOM)
        self.assertEqual(set(s.keys()), set(score.CHAVES_SINAIS))
        self.assertEqual(len(score.CHAVES_SINAIS), 14)  # 10 antigos + Bloco A
        for k, v in s.items():
            self.assertGreaterEqual(v, 0.0, k)
            self.assertLessEqual(v, 1.0, k)

    def test_chaves_antigas_preservadas(self):
        for k in score.PESOS:
            self.assertIn(k, score.CHAVES_SINAIS)

    def test_pesos_somam_100(self):
        self.assertAlmostEqual(sum(score.PESOS.values()), 100.0, places=6)

    def test_componente_e_sinal_vezes_peso(self):
        r = score.calcular(TEXTO_BOM, SECAO10)
        comp = r["score"]["componentes"]
        # cada componente <= seu peso (sinal in [0,1])
        for k, v in comp.items():
            self.assertLessEqual(v, score.PESOS[k] + 0.05, k)
        self.assertAlmostEqual(r["score"]["total"], round(sum(comp.values()), 1), places=6)


class TestComportamentoCongelado(unittest.TestCase):
    def test_texto_humano_bom_passa(self):
        r = score.calcular(TEXTO_BOM, SECAO10)
        self.assertGreaterEqual(r["score"]["total"], score.ALVO,
                                 msg=f"score {r['score']['total']} < alvo {score.ALVO}")

    def test_texto_ia_uniforme_reprova(self):
        # prosa uniforme e previsível: burstiness baixo, sem variação
        ia = (" ".join([
            "A empresa oferece soluções completas para o cliente moderno.",
            "A empresa entrega valor real para o cliente moderno.",
            "A empresa garante qualidade total para o cliente moderno.",
            "A empresa promove inovação contínua para o cliente moderno.",
            "A empresa assegura suporte dedicado para o cliente moderno.",
        ]))
        r = score.calcular(ia, SECAO10)
        self.assertLess(r["score"]["total"], score.ALVO)

    def test_pesos_ainda_somam_100(self):
        self.assertAlmostEqual(sum(score.PESOS.values()), 100.0, places=6)
