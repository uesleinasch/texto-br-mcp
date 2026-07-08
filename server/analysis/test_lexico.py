import unittest

from lexico import analisar

# Trecho real de references/humanizacao-algoritmos.md (seção 10: header "Evitar"/
# "Trocar por", separador de traços) — não o formato "Pivot"/"Alternativas" do
# rascunho inicial, que o parser não reconheceria como cabeçalho a descartar.
SECAO10 = """### 10.1 Verbos pivot de LLM

| Evitar       | Trocar por                                   |
| ------------ | --------------------------------------------- |
| abordar      | tratar de, falar de, encarar                 |
| estabelecer  | criar, definir, montar, fixar                |

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

    # Fix pós-review: pretérito perfeito (3ª pessoa singular e plural) também
    # é flexão real de verbo pivot e precisa casar — sem reabrir a porta para
    # derivados nominais ("abordagem").
    def test_preterito_terceira_singular_casa(self):
        texto = TEXTO_LIMPO + " O comitê estabeleceu novas regras."
        r = analisar(texto, SECAO10)
        encontrados = [o["encontrado"].lower() for o in r["ocorrencias"]]
        self.assertIn("estabeleceu", encontrados)
        self.assertNotIn("abordagem", encontrados)

    def test_preterito_terceira_plural_casa(self):
        texto = TEXTO_LIMPO + " Os autores abordaram o tema."
        r = analisar(texto, SECAO10)
        encontrados = [o["encontrado"].lower() for o in r["ocorrencias"]]
        self.assertIn("abordaram", encontrados)
        self.assertNotIn("abordagem", encontrados)


if __name__ == "__main__":
    unittest.main()
