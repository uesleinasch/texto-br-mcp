import json
import os
import unittest

import calibrar
import score

DIR_CORPUS = os.path.join(os.path.dirname(__file__), "..", "..", "references", "Corpus")
_MANIFEST = os.path.join(DIR_CORPUS, "manifest.json")
BASELINE = os.path.join(DIR_CORPUS, "baseline-report.json")
MODELO_JSON = os.path.join(DIR_CORPUS, "modelo-calibrado.json")


@unittest.skipUnless(os.path.exists(_MANIFEST), "corpus não preprocessado")
class TestSeparacao(unittest.TestCase):
    def test_baseline_manual_preservado(self):
        X, y, nomes, chaves = calibrar.matriz_features(DIR_CORPUS)
        scores = [calibrar.score_ponderado(x, score.PESOS_MANUAIS, chaves) for x in X]
        with open(BASELINE, encoding="utf-8") as f:
            esperado = json.load(f)["auc_total"]
        self.assertAlmostEqual(calibrar.auc(scores, y), esperado, places=3)

    def test_modelo_congelado_separa_o_corpus(self):
        corpus = calibrar.carregar_corpus(DIR_CORPUS)
        probs, y = [], []
        for e in corpus:
            s = score.sinais(e["ritmo"], e["lex"], e["texto"])
            probs.append(score.probabilidade(s))
            y.append(e["y"])
        with open(MODELO_JSON, encoding="utf-8") as f:
            esperado = json.load(f)["auc_in_sample"]
        self.assertAlmostEqual(calibrar.auc(probs, y), esperado, places=3)
        hum = sorted(p for p, l in zip(probs, y) if l == 1)
        ia = sorted(p for p, l in zip(probs, y) if l == 0)
        med = lambda xs: xs[len(xs) // 2]
        self.assertGreater(med(hum), med(ia))

    def test_baseline_report_alvo_atual_bate_com_score_alvo(self):
        # Esse drift já aconteceu uma vez (ALVO recalibrado para 93.6 e o
        # baseline-report.json ficou fossilizado em 74.4). Trava a paridade.
        with open(BASELINE, encoding="utf-8") as f:
            alvo_atual = json.load(f)["alvo_atual"]
        self.assertEqual(
            alvo_atual, score.ALVO,
            msg="baseline-report.json desatualizado: re-rode calibrar.py --baseline "
                "após recalibrar o ALVO")

    def test_loocv_do_modelo_congelado(self):
        with open(MODELO_JSON, encoding="utf-8") as f:
            m = json.load(f)
        corpus = calibrar.carregar_corpus(DIR_CORPUS)
        folds = calibrar.folds_com_referencia(corpus)
        a = calibrar.loocv_logistica(corpus, folds, m["chaves"], m["l2"])
        self.assertAlmostEqual(a, m["auc_loocv"], places=3)
        with open(BASELINE, encoding="utf-8") as f:
            baseline_auc = json.load(f)["auc_total"]
        self.assertGreaterEqual(a, baseline_auc,
                                msg=f"LOO-CV {a} abaixo do baseline manual {baseline_auc}")
