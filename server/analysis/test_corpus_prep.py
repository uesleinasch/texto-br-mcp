import unittest
import corpus_prep as cp


class TestGenero(unittest.TestCase):
    def test_poema_detectado_por_linhas_curtas_e_quebras(self):
        poema = "\n".join([
            "Numa Londres de névoa espessa,", "onde o gás lampeja e hesita,",
            "caminha ela por ruas densas", "de fuligem e de muda vida.",
            "O cetim aperta a cintura,", "a saia arrasta nas calçadas,",
        ])
        self.assertEqual(cp.detectar_genero(poema), "poesia")

    def test_prosa_detectada(self):
        prosa = (
            "O mercado abriu em queda acentuada e ninguém esperava aquilo depois "
            "de uma semana inteira de otimismo. As vendas despencaram ao longo da "
            "tarde inteira, e o pregão virou um caos de ordens canceladas."
        )
        self.assertEqual(cp.detectar_genero(prosa), "prosa")


class TestBoilerplate(unittest.TestCase):
    def test_remove_url_de_marca_e_linhas_de_capa(self):
        bruto = "Manoel Neves\n\nwww.manoelneves.com\n\nO texto de verdade começa aqui e segue por várias linhas de prosa real."
        limpo = cp.limpar_boilerplate(bruto)
        self.assertNotIn("www.manoelneves.com", limpo)
        self.assertIn("texto de verdade", limpo)

    def test_remove_numeros_de_pagina_isolados(self):
        bruto = "Primeira linha de prosa aqui.\n12\nSegunda linha de prosa aqui."
        limpo = cp.limpar_boilerplate(bruto)
        self.assertNotIn("\n12\n", "\n" + limpo + "\n")
        self.assertIn("Primeira linha", limpo)
        self.assertIn("Segunda linha", limpo)


class TestManifesto(unittest.TestCase):
    def test_entrada_tem_todos_os_campos(self):
        entrada = cp.entrada_manifesto(
            arquivo="Human/texto-001.md", classe="humano", genero="prosa",
            tipo="desconhecido", palavras=399, fonte="local", data_verificada=None,
            data_coleta="2026-07-08",
        )
        for campo in ["arquivo", "classe", "genero", "tipo", "palavras",
                      "incluir_calibracao", "fonte", "data_verificada", "data_coleta"]:
            self.assertIn(campo, entrada)
        # prosa entra na calibração; classe válida
        self.assertTrue(entrada["incluir_calibracao"])
        self.assertIn(entrada["classe"], ("humano", "ia"))

    def test_poesia_marcada_fora_da_calibracao(self):
        entrada = cp.entrada_manifesto(
            arquivo="IA/texto-009.md", classe="ia", genero="poesia",
            tipo="desconhecido", palavras=600, fonte="gerado", data_verificada=None,
            data_coleta="2026-07-08",
        )
        self.assertFalse(entrada["incluir_calibracao"])


if __name__ == "__main__":
    unittest.main()
