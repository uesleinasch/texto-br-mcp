import unittest

from lexico import analisar

# Trecho real de references/humanizacao-algoritmos.md (seção 10: header "Evitar"/
# "Trocar por", separador de traços) — não o formato "Pivot"/"Alternativas" do
# rascunho inicial, que o parser não reconheceria como cabeçalho a descartar.
SECAO10 = """### 10.1 Verbos pivot de LLM

| Evitar       | Trocar por                                   |
| ------------ | --------------------------------------------- |
| abordar      | tratar de, falar de, encarar                 |

### 10.4 Conectores pivot

| Evitar                | Trocar por (ou cortar)                         |
| --------------------- | ----------------------------------------------- |
| Além disso            | E, Outra coisa, Some-se, Tem mais              |
"""

# A6: "abordagem" (derivado nominal de "abordar") e "além dissonante" (onde
# "dissonante" começa com as mesmas letras de "disso") não podem disparar os
# pivots "abordar" e "além disso".
TEXTO_LIMPO = (
    "A abordagem escolhida pela equipe funcionou bem naquele contexto difícil. "
    "O som ficou além dissonante do que o ensaio normal costuma soar naquela sala. "
    "Nada mais aconteceu de estranho naquela noite fria. "
    "Todos foram embora satisfeitos com o resultado final da apresentação."
)


class TestFronteiras(unittest.TestCase):
    def test_derivado_nominal_nao_casa_verbo_pivot(self):
        r = analisar(TEXTO_LIMPO, SECAO10)
        encontrados = [o["encontrado"].lower() for o in r.get("ocorrencias", [])]
        self.assertNotIn("abordagem", encontrados)

    def test_pivot_sem_fronteira_final_nao_casa_dentro_de_palavra(self):
        # "abordagem" e "além dissonante" não podem disparar os pivots.
        r = analisar(TEXTO_LIMPO, SECAO10)
        self.assertEqual(r.get("ocorrencias", []), [])

    def test_pivot_real_flexionado_ainda_casa(self):
        texto = TEXTO_LIMPO + " O relatório aborda o problema central. Além disso, resume tudo."
        r = analisar(texto, SECAO10)
        encontrados = " ".join(o["encontrado"].lower() for o in r["ocorrencias"])
        self.assertIn("aborda", encontrados)
        self.assertIn("além disso", encontrados)


if __name__ == "__main__":
    unittest.main()
