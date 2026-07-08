"""Testes unitários da tokenização pt-BR (casos reproduzidos na auditoria 2026-07-07)."""
import unittest

from texto_util import dividir_sentencas, limpar_markdown, parsear_blocos


class TestDividirSentencas(unittest.TestCase):
    # A1: proteção de abreviação não pode casar sufixo de palavra comum
    def test_palavra_terminada_em_sufixo_de_abreviacao_quebra_sentenca(self):
        for texto, esperado in [
            ("Ele abriu o app. Depois fechou tudo.", 2),      # "app." contém "p."
            ("Comprou um hífen. Não sabia usar.", 2),          # "hífen." contém "n."
            ("Comeu o pastel. Ficou feliz.", 2),               # "pastel." contém "tel."
            ("Usou luva de látex. Ficou seguro.", 2),          # "látex." contém "ex."
        ]:
            with self.subTest(texto=texto):
                self.assertEqual(len(dividir_sentencas(texto)), esperado)

    # A1/A6: abreviações reais continuam protegidas (e agora case-insensitive)
    def test_abreviacoes_reais_nao_quebram(self):
        for texto in [
            "O Dr. Silva chegou cedo e atendeu todos os pacientes da fila.",
            "Veja, p. ex., o caso do porto de Santos no ano passado.",
            "O dr. Silva chegou cedo.",                        # minúscula
            "A empresa virou S.A. no ano passado e cresceu.",  # nova na lista
            "Isso foi em 44 a.C. segundo os registros.",       # nova na lista
        ]:
            with self.subTest(texto=texto):
                self.assertEqual(len(dividir_sentencas(texto)), 1)

    # A2: pontuação seguida de aspas/parêntese fecha a sentença
    def test_pontuacao_com_aspas_quebra(self):
        self.assertEqual(
            len(dividir_sentencas('Ele disse "acabou." Depois saiu de casa.')), 2
        )
        self.assertEqual(
            len(dividir_sentencas("Ela gritou (era tarde!) Ninguém ouviu nada.")), 2
        )

    # A6: reticência intra-sentencial (seguida de minúscula) NÃO quebra
    def test_reticencia_intra_sentencial_nao_quebra(self):
        self.assertEqual(len(dividir_sentencas("Ele foi… e voltou depois.")), 1)

    def test_reticencia_final_quebra(self):
        self.assertEqual(len(dividir_sentencas("Ele foi… Voltou depois.")), 2)

    # A6: atribuição de fala após travessão não vira sentença própria
    def test_travessao_atribuicao_nao_quebra(self):
        self.assertEqual(
            len(dividir_sentencas("— Olá, tudo bem? — perguntou ela.")), 1
        )


class TestLimparMarkdown(unittest.TestCase):
    # A3: prosa iniciada por número de 3+ dígitos não é lista
    def test_prosa_iniciada_por_ano_nao_e_descartada(self):
        prosa, _ = limpar_markdown("1994. Foi o ano do real. Tudo mudou.")
        self.assertIn("Foi o ano do real", prosa)

    def test_item_de_lista_numerada_continua_excluido(self):
        prosa, excluidas = limpar_markdown("1. primeiro item\n2. segundo item")
        self.assertEqual(prosa.strip(), "")
        self.assertEqual(excluidas, 2)

    # A6: snake_case sobrevive à remoção de ênfase
    def test_snake_case_preservado(self):
        prosa, _ = limpar_markdown("A função foo_bar_baz retorna o valor.")
        self.assertIn("foo_bar_baz", prosa)

    def test_enfase_com_underscore_em_fronteira_ainda_removida(self):
        prosa, _ = limpar_markdown("Isso é _importante_ para o time.")
        self.assertIn("importante", prosa)
        self.assertNotIn("_importante_", prosa)

    def test_enfase_com_asterisco_removida(self):
        prosa, _ = limpar_markdown("Isso é **muito** relevante.")
        self.assertIn("muito", prosa)
        self.assertNotIn("**", prosa)


class TestParsearBlocos(unittest.TestCase):
    # A6: régua horizontal não vira parágrafo
    def test_regua_horizontal_nao_e_paragrafo(self):
        blocos = parsear_blocos("Um parágrafo inteiro aqui.\n\n---\n\nOutro parágrafo.")
        paragrafos = [b for b in blocos if b["tipo"] == "paragrafo"]
        self.assertEqual(len(paragrafos), 2)
        for p in paragrafos:
            self.assertNotEqual(p["texto"], "---")

    # A3: prosa iniciada por ano não vira "lista" na macroestrutura
    def test_prosa_com_ano_e_paragrafo(self):
        blocos = parsear_blocos("1994. Foi o ano do real. Tudo mudou naquele país.")
        self.assertEqual(blocos[0]["tipo"], "paragrafo")


class TestHelpersCompartilhados(unittest.TestCase):
    def test_clamp(self):
        from texto_util import clamp
        self.assertEqual(clamp(1.5), 1.0)
        self.assertEqual(clamp(-0.5), 0.0)
        self.assertEqual(clamp(0.3), 0.3)
        self.assertEqual(clamp(5, 0, 10), 5)

    def test_primeiro_termo(self):
        from texto_util import primeiro_termo
        self.assertEqual(primeiro_termo('"Quando" ele saiu'), "quando")
        self.assertEqual(primeiro_termo("(Ontem) choveu"), "ontem")
        self.assertEqual(primeiro_termo(""), "")

    def test_conectivos_uniao_superconjunto(self):
        from texto_util import CONECTIVOS_INICIAIS
        # a união preserva os itens que hoje vivem em cada módulo
        for item in ["além disso", "no entanto", "adicionalmente", "vale ressaltar", "é importante", "assim sendo"]:
            self.assertIn(item, CONECTIVOS_INICIAIS)

    def test_stopwords_contem_basicas(self):
        from texto_util import STOPWORDS
        for p in ["de", "que", "a", "o", "não", "porque"]:
            self.assertIn(p, STOPWORDS)


if __name__ == "__main__":
    unittest.main()
