import json
import os
import unittest

import calibrar
import score

DIR_CORPUS = os.path.join(os.path.dirname(__file__), "..", "..", "references", "Corpus")
_MANIFEST = os.path.join(DIR_CORPUS, "manifest.json")
BASELINE = os.path.join(DIR_CORPUS, "baseline-report.json")


@unittest.skipUnless(os.path.exists(_MANIFEST), "corpus não preprocessado")
class TestSeparacao(unittest.TestCase):
    def test_pesos_congelados_separam_o_corpus(self):
        X, y, nomes, chaves = calibrar.matriz_features(DIR_CORPUS)
        scores = [calibrar.score_ponderado(x, score.PESOS, chaves) for x in X]
        a = calibrar.auc(scores, y)
        self.assertGreaterEqual(a, 0.8, msg=f"AUC in-sample {a} < 0.8")

    def test_loocv_nao_regride_vs_baseline(self):
        with open(BASELINE, encoding="utf-8") as f:
            baseline_auc = json.load(f)["auc_total"]
        a = calibrar.separacao_loocv(DIR_CORPUS)
        # a reponderação não pode piorar a generalização honesta
        self.assertGreaterEqual(a, baseline_auc - 0.02,
                                 msg=f"LOOCV {a} regrediu vs baseline {baseline_auc}")

    def test_medianas_separadas(self):
        X, y, nomes, chaves = calibrar.matriz_features(DIR_CORPUS)
        scores = [calibrar.score_ponderado(x, score.PESOS, chaves) for x in X]
        hum = sorted(s for s, l in zip(scores, y) if l == 1)
        ia = sorted(s for s, l in zip(scores, y) if l == 0)
        med = lambda xs: xs[len(xs) // 2]
        self.assertGreater(med(hum), med(ia))
