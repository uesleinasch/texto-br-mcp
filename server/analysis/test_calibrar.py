import os
import unittest
import calibrar
import metricas

DIR_CORPUS = os.path.join(os.path.dirname(__file__), "..", "..", "references", "Corpus")
_MANIFEST = os.path.join(DIR_CORPUS, "manifest.json")


class TestAUC(unittest.TestCase):
    def test_separacao_perfeita(self):
        scores = [0.9, 0.8, 0.2, 0.1]
        labels = [1, 1, 0, 0]
        self.assertAlmostEqual(calibrar.auc(scores, labels), 1.0)

    def test_sem_separacao(self):
        # cada classe tem um score alto (0.5) e um baixo (0.4): não há
        # separação consistente entre humano/IA -> AUC 0.5.
        scores = [0.5, 0.5, 0.4, 0.4]
        labels = [1, 0, 1, 0]
        self.assertAlmostEqual(calibrar.auc(scores, labels), 0.5)

    def test_empates_contam_meio(self):
        scores = [0.5, 0.5]
        labels = [1, 0]
        self.assertAlmostEqual(calibrar.auc(scores, labels), 0.5)


class TestScorePonderado(unittest.TestCase):
    def test_soma_ponderada_dos_sinais(self):
        chaves = ["a", "b"]
        x = [1.0, 0.5]
        pesos = {"a": 60.0, "b": 40.0}
        self.assertAlmostEqual(calibrar.score_ponderado(x, pesos, chaves), 80.0)


class TestLogistica(unittest.TestCase):
    def test_recupera_sinal_em_dados_separaveis(self):
        # feature 0 separa perfeitamente; feature 1 é ruído
        X = [[2.0, 0.1], [1.5, -0.2], [-1.5, 0.3], [-2.0, -0.1]]
        y = [1, 1, 0, 0]
        Xs, _, _ = calibrar.padronizar(X)
        w, b = calibrar.treinar_logistica(Xs, y, prior=[0.0, 0.0], l2=0.01, lr=0.5, iteracoes=2000)
        self.assertGreater(w[0], abs(w[1]))  # feature discriminante domina

    def test_determinismo(self):
        X = [[2.0, 0.1], [-2.0, -0.1], [1.0, 0.2], [-1.0, -0.2]]
        y = [1, 0, 1, 0]
        Xs, _, _ = calibrar.padronizar(X)
        r1 = calibrar.treinar_logistica(Xs, y, prior=[0.0, 0.0], l2=0.1, lr=0.3, iteracoes=500)
        r2 = calibrar.treinar_logistica(Xs, y, prior=[0.0, 0.0], l2=0.1, lr=0.3, iteracoes=500)
        self.assertEqual(r1, r2)


class TestMapeamentoPesos(unittest.TestCase):
    def test_pesos_somam_100_e_respeitam_piso(self):
        coef = [3.0, 1.0, 0.0]
        chaves = ["a", "b", "c"]
        pesos = calibrar.coef_para_pesos(coef, chaves, piso=2.0)
        self.assertAlmostEqual(sum(pesos.values()), 100.0, places=6)
        self.assertGreaterEqual(pesos["c"], 2.0)  # piso preserva o componente
        self.assertGreater(pesos["a"], pesos["b"])  # mais discriminante, mais peso

    def test_coef_negativo_fica_no_piso(self):
        # sinal anticorrelacionado (coef < 0) não deve ganhar peso além do piso
        coef = [4.0, -3.0]
        chaves = ["bom", "anticorrelacionado"]
        pesos = calibrar.coef_para_pesos(coef, chaves, piso=2.0)
        self.assertAlmostEqual(sum(pesos.values()), 100.0, places=6)
        self.assertAlmostEqual(pesos["anticorrelacionado"], 2.0, places=6)
        self.assertGreater(pesos["bom"], pesos["anticorrelacionado"])

    def test_coef_para_pesos_todos_nao_positivos_distribui_uniforme(self):
        # Caso degenerado: nenhum coeficiente positivo (corpus sem discriminação)
        # Sem base para diferenciar, distribui uniformemente (não despeja o
        # resíduo num único componente arbitrário).
        chaves = ["a", "b", "c", "d"]
        pesos = calibrar.coef_para_pesos([-1.0, -0.5, 0.0, -2.0], chaves, piso=2.0)
        self.assertAlmostEqual(sum(pesos.values()), 100.0, places=6)
        for k in chaves:
            self.assertAlmostEqual(pesos[k], 25.0, places=6,
                                   msg=f"{k} deveria receber 100/4 no caso degenerado")

    def test_degenerado_residuo_de_divisao_nao_exata_vai_para_primeira_chave(self):
        # 3 chaves: 100/3 arredonda para 33.3 cada (soma 99.9); o resto de 0.1
        # deve ir para a PRIMEIRA chave (33.4), mantendo a soma exata em 100.0.
        chaves = ["a", "b", "c"]
        pesos = calibrar.coef_para_pesos([-1.0, 0.0, -0.5], chaves, piso=2.0)
        self.assertAlmostEqual(sum(pesos.values()), 100.0, places=6)
        self.assertAlmostEqual(pesos["a"], 33.4, places=6)
        self.assertAlmostEqual(pesos["b"], 33.3, places=6)
        self.assertAlmostEqual(pesos["c"], 33.3, places=6)

    def test_degenerado_com_uma_chave_recebe_100(self):
        # 1 chave: uniforme = 100.0, resto 0.0 — o único componente leva tudo.
        pesos = calibrar.coef_para_pesos([-1.0], ["unica"], piso=2.0)
        self.assertAlmostEqual(pesos["unica"], 100.0, places=6)


class TestYouden(unittest.TestCase):
    def test_escolhe_corte_que_separa(self):
        scores = [10, 20, 80, 90]
        labels = [0, 0, 1, 1]
        alvo = calibrar.melhor_alvo(scores, labels)
        self.assertTrue(20 < alvo <= 80)


@unittest.skipUnless(os.path.exists(_MANIFEST), "corpus não preprocessado")
class TestReferenciaPorFold(unittest.TestCase):
    def test_fold_de_humano_nao_ve_o_proprio_texto(self):
        corpus = calibrar.carregar_corpus(DIR_CORPUS)
        folds = calibrar.folds_com_referencia(corpus)
        n_humanos_total = sum(1 for e in corpus if e["y"] == 1)
        for i, fold in enumerate(folds):
            esperado = n_humanos_total - (1 if corpus[i]["y"] == 1 else 0)
            self.assertEqual(fold["referencia"]["n_textos"], esperado)

    def test_fold_do_primeiro_humano_bate_com_referencia_recalculada(self):
        # Reforça o teste acima: aqui a comparação é por IGUALDADE PROFUNDA da
        # referência do fold contra metricas.construir_referencia() aplicada
        # aos textos humanos corretos (todos exceto ele) — não só a contagem.
        # Um bug que excluísse o humano ERRADO (mas ainda -1 do total) passaria
        # pelo teste de contagem e não por este.
        corpus = calibrar.carregar_corpus(DIR_CORPUS)
        folds = calibrar.folds_com_referencia(corpus)
        i = next(idx for idx, e in enumerate(corpus) if e["y"] == 1)
        outros_humanos = [e["texto"] for j, e in enumerate(corpus)
                          if e["y"] == 1 and j != i]
        esperado = metricas.construir_referencia(outros_humanos)
        self.assertEqual(folds[i]["referencia"], esperado)


@unittest.skipUnless(os.path.exists(_MANIFEST), "corpus não preprocessado")
class TestLoocvLogistica(unittest.TestCase):
    def test_loocv_logistica_e_determinista_e_valida(self):
        corpus = calibrar.carregar_corpus(DIR_CORPUS)
        folds = calibrar.folds_com_referencia(corpus)
        chaves = list(calibrar.CHAVES[:5])
        a1 = calibrar.loocv_logistica(corpus, folds, chaves, l2=1.0)
        a2 = calibrar.loocv_logistica(corpus, folds, chaves, l2=1.0)
        self.assertEqual(a1, a2)
        self.assertGreaterEqual(a1, 0.0)
        self.assertLessEqual(a1, 1.0)


if __name__ == "__main__":
    unittest.main()
