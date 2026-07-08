import unittest
import calibrar


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


if __name__ == "__main__":
    unittest.main()
