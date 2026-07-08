"""Testes do score: regressão do refactor de sinais e comportamento congelado."""
import unittest

import score

# Trecho de prosa humana real do corpus (references/Corpus/Human/texto-001.md,
# classe "humano" no manifest.json). Trocado na Task 13: com o ALVO recalibrado
# para 93.6 (p75 das probabilidades humanas no modelo logístico), apenas ~24%
# dos 29 textos humanos do corpus atingem o alvo — o antigo TEXTO_BOM sintético
# pontuava 90.4, abaixo do novo alvo. Este texto pontua 98.7.
# Nota: por estar NO corpus/referência, este é um smoke test in-reference (o
# modelo já "viu" este texto no fit); não prova generalização — isso é
# responsabilidade de test_separacao.py (LOO-CV honesto, sem vazamento).
TEXTO_BOM = (
    "Há poucos dias assisti a uma palestra sobre motivação e liderança com o Dr. "
    "Jamiro Wanderley e em determinado momento ele falou uma coisa que não sabia "
    "e que vou compartilhar com você hoje.\n\n"
    "Ele falou a respeito da natureza dos girassóis. Como o próprio nome diz, "
    "eles giram de acordo com a inclinação do sol, em outras palavras, eles "
    "“perseguem a luz”.\n\n"
    "Provavelmente essa parte você sabia, mas tem outra que talvez não!\n\n"
    "Você já se fez essa perguntinha? E nos dias nublados e chuvosos, quando o "
    "sol fica totalmente encoberto pelas nuvens, o que acontece?\n\n"
    "Interessante essa pergunta, não é? Talvez você tenha pensado que a flor de "
    "girassol fica murchinha e olhando para baixo. Acertei? Pois é, está errado! "
    "Sabe o que acontece? Elas se voltam umas para as outras para dividirem "
    "entre si as suas energias.\n\n"
    "Eu fiquei impressionado com a perfeição da natureza e levei essa reflexão "
    "para a nossa vida.\n\n"
    "Todos nós queremos essa luz, buscamos essa luz de diversas maneiras: na "
    "família, nos amigos, na religião, no trabalho e por aí vai. Mas sempre "
    "acontecem os dias nublados, os dias de tristeza, não tem como fugir deles. "
    "Nessa hora, a maioria das pessoas fica acabrunhada, de cabeça baixa e as "
    "mais fragilizadas às vezes chegam até a ficarem deprimidas.\n\n"
    "A natureza tem tanto a nos ensinar! Que tal fazer como os lindos "
    "girassóis? Na hora da dor, do desespero, da angústia, porque não olhar "
    "para dentro de si mesmo com total sinceridade e saber que lá dentro "
    "também existe uma luz, e essa luz pode ser compartilhada com quem "
    "amamos?\n\n"
    "Sentimentos difíceis e dolorosos que são reprimidos acabam mais cedo ou "
    "mais tarde se transformando em uma doença, você quer esperar que um "
    "doença lhe acometa para só então se abrir para os outros? Não queira "
    "tornar as coisas mais difíceis! Veja os girassóis! Eles não ficam "
    "pensando: “O sol se escondeu, então eu vou ficar aqui triste, de "
    "cabeça baixa, esperando que ele volte…”. Nada disso! Na mesma "
    "hora eles acionam sua luz interna e compartilham com os outros…\n\n"
    "Portanto! Que hoje você se encante com a beleza perfeita da natureza, que "
    "em sua simplicidade, nos dá uma verdadeira aula de como viver melhor e "
    "com mais harmonia.\n\n"
    "Se quiser também assistir a esse vídeo do Dr. Jamiro, recomendo "
    "fortemente, é muito bacana o que ele fala ao longo da palestra."
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
        self.assertEqual(len(score.CHAVES_SINAIS), 17)  # 10 antigos + Bloco A/zipf + Bloco B
        for k, v in s.items():
            self.assertGreaterEqual(v, 0.0, k)
            self.assertLessEqual(v, 1.0, k)

    def test_referencia_padrao_e_a_congelada(self):
        import variancia, lexico
        ritmo = variancia.analisar(TEXTO_BOM)
        lex = lexico.analisar(TEXTO_BOM, SECAO10)
        s_padrao = score.sinais(ritmo, lex, TEXTO_BOM)
        s_explicito = score.sinais(ritmo, lex, TEXTO_BOM, referencia=score.REFERENCIA)
        self.assertEqual(s_padrao, s_explicito)

    def test_chaves_antigas_preservadas(self):
        for k in score.PESOS_MANUAIS:
            self.assertIn(k, score.CHAVES_SINAIS)

    def test_total_e_probabilidade_vezes_100(self):
        r = score.calcular(TEXTO_BOM, SECAO10)
        self.assertGreaterEqual(r["score"]["total"], 0.0)
        self.assertLessEqual(r["score"]["total"], 100.0)
        self.assertIn("sinais", r["score"])
        self.assertNotIn("maximos", r["score"])
        self.assertEqual(set(r["score"]["componentes"].keys()), set(score.MODELO["chaves"]))


class TestComportamentoCongelado(unittest.TestCase):
    def test_modelo_congelado_fiel_ao_json(self):
        import json, os
        caminho = os.path.join(os.path.dirname(__file__), "..", "..",
                               "references", "Corpus", "modelo-calibrado.json")
        with open(caminho, encoding="utf-8") as f:
            m = json.load(f)
        self.assertEqual(score.MODELO["chaves"], m["chaves"])
        self.assertEqual(score.MODELO["coeficientes"], m["coeficientes"])
        self.assertEqual(score.MODELO["intercepto"], m["intercepto"])
        self.assertEqual(score.MODELO["medias"], m["medias"])
        self.assertEqual(score.MODELO["desvios"], m["desvios"])
        # ALVO deriva do p75 PRECISO (4 casas) das probabilidades humanas, não
        # do campo grosseiro alvo_p75_humano_prob (arredondado a 1 casa na
        # escala 0-100 da antiga rota aditiva — cf. comentário em calibrar.py
        # sobre alvo_p75_humano_prob_precisa).
        self.assertAlmostEqual(score.ALVO, round(m["alvo_p75_humano_prob_precisa"] * 100, 1), places=6)

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
