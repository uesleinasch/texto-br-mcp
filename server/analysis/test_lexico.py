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


class TestTrigramasStopwords(unittest.TestCase):
    # A6: trigramas 100% stopword não contam como repetição estrutural
    def test_trigrama_so_de_stopwords_nao_conta(self):
        # "de que a" e "que não se" repetem, mas são stopwords puras
        texto = (
            "Ela sabia de que a casa precisava de reformas urgentes naquele inverno. "
            "Ele achava de que a obra atrasaria mais uma vez sem explicação. "
            "Ninguém entendia de que a demora vinha da falta de material bom. "
            "O tempo passou e a reforma virou assunto encerrado entre eles."
        )
        r = analisar(texto, SECAO10)
        for t in r["trigramas_repetidos"]:
            palavras_t = t.split()
            self.assertFalse(
                all(p in __import__("lexico").STOPWORDS for p in palavras_t),
                msg=f"trigrama de stopwords não deveria contar: {t!r}",
            )

    def test_trigrama_com_conteudo_repetido_ainda_conta(self):
        # trigrama com palavra de conteúdo repetido continua sinalizado
        texto = (
            "O sistema de cache falhou de novo naquela madrugada de plantão longo. "
            "O sistema de cache derrubou o site inteiro por quase uma hora seguida. "
            "Ninguém sabia por que o sistema de cache insistia em cair sob carga. "
            "A equipe decidiu reescrever tudo do zero na semana seguinte com calma."
        )
        r = analisar(texto, SECAO10)
        self.assertIn("sistema de cache", r["trigramas_repetidos"])


class TestRegimeDiversidade(unittest.TestCase):
    def test_regime_mattr_para_texto_longo(self):
        texto = " ".join(f"palavra{i} do texto number {i} aqui" for i in range(40))
        r = analisar(texto, SECAO10)
        self.assertEqual(r["metricas"]["diversidade_regime"], "MATTR-100")

    def test_regime_ttr_bruto_para_texto_curto(self):
        # 30-99 palavras: TTR bruto (abaixo de 100 não há janela)
        texto = (
            "O cachorro correu pelo quintal atrás da bola vermelha durante a tarde toda. "
            "Depois deitou na sombra da mangueira e dormiu profundamente por horas. "
            "Acordou com fome e latiu para a porta da cozinha esperando comida boa."
        )
        r = analisar(texto, SECAO10)
        self.assertEqual(r["metricas"]["diversidade_regime"], "TTR-bruto")


if __name__ == "__main__":
    unittest.main()
