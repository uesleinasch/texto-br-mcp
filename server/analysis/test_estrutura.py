import unittest

from estrutura import calcular

# 6 parágrafos sem heading (obriga o detector de progressão a ser aplicável:
# len(paras) >= 6, já que sem títulos com_titulo fica vazio).
BASE = (
    "{s0} O resto do parágrafo segue explicando o contexto da notícia com calma "
    "e um nível razoável de detalhe para o leitor entender o cenário completo.\n\n"
    "{s1} A apuração continuou pela tarde com entrevistas nas ruas do centro.\n\n"
    "{s2} O fechamento da edição aconteceu sem novos fatos relevantes.\n\n"
    "Nada disso mudou a percepção geral do público sobre o caso investigado.\n\n"
    "O caso segue em aberto na delegacia e deve render novos desdobramentos.\n\n"
    "A expectativa agora é que novas provas surjam ao longo da semana que vem."
)


def diagnosticos_de(resultado):
    return [d for det in resultado["detectores"] for d in det["diagnostico"]]


class TestSignposts(unittest.TestCase):
    # A5: "Segundo o IBGE" (citação de fonte) e "Depois de anos" (advérbio comum)
    # não são progressão sinalizada.
    def test_citacao_de_fonte_nao_e_signpost(self):
        texto = BASE.format(
            s0="Segundo o IBGE, a inflação caiu.",
            s1="Segundo analistas, o pior passou.",
            s2="Depois de anos, ele voltou.",
        )
        r = calcular(texto, "blog")
        diagnosticos = diagnosticos_de(r)
        aberturas = [d for d in diagnosticos if "signpost" in d.lower()]
        self.assertEqual(aberturas, [], msg=diagnosticos)

    def test_signpost_enumerativo_real_ainda_detectado(self):
        texto = BASE.format(
            s0="Primeiro, o contexto importa.",
            s1="Segundo, os dados confirmam a tendência.",
            s2="Por fim, a conclusão se impõe.",
        )
        r = calcular(texto, "blog")
        diagnosticos = diagnosticos_de(r)
        aberturas = [d for d in diagnosticos if "signpost" in d.lower()]
        self.assertNotEqual(aberturas, [])


if __name__ == "__main__":
    unittest.main()
