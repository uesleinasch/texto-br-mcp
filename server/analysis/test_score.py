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
    def test_sinais_tem_as_10_chaves_normalizadas(self):
        import variancia, lexico
        ritmo = variancia.analisar(TEXTO_BOM)
        lex = lexico.analisar(TEXTO_BOM, SECAO10)
        s = score.sinais(ritmo, lex)
        self.assertEqual(set(s.keys()), set(score.PESOS.keys()))
        for k, v in s.items():
            self.assertGreaterEqual(v, 0.0, k)
            self.assertLessEqual(v, 1.0, k)

    def test_pesos_somam_100(self):
        self.assertAlmostEqual(sum(score.PESOS.values()), 100.0, places=6)

    def test_componente_e_sinal_vezes_peso(self):
        r = score.calcular(TEXTO_BOM, SECAO10)
        comp = r["score"]["componentes"]
        # cada componente <= seu peso (sinal in [0,1])
        for k, v in comp.items():
            self.assertLessEqual(v, score.PESOS[k] + 0.05, k)
        self.assertAlmostEqual(r["score"]["total"], round(sum(comp.values()), 1), places=6)
