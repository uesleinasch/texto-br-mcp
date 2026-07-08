import json
import os
import tempfile
import unittest
from unittest import mock

import corpus_prep as cp

_MANIFEST = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "references", "Corpus", "manifest.json",
)

TIPOS_VALIDOS = {
    "blog", "tecnico", "corporativo", "email", "capitulo", "podcast",
    "video", "explicativo", "geral", "comentario-blog", "comentario-jira",
    "chat", "desconhecido",
}


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

    def test_remove_mobilia_periodica_de_print_preserva_prosa(self):
        cabecalho = "1 de janeiro de 2021 · Título do Artigo"
        rodape = "https://medium.com/artigo-abc 1/18"
        prosa = [
            "Primeiro parágrafo de prosa real do artigo com conteúdo único aqui.",
            "Segundo parágrafo também único e com várias palavras reais escritas.",
            "Terceiro trecho de prosa que não se repete em nenhum lugar do texto.",
            "Quarto bloco de prosa, distinto dos demais, com sua própria frase.",
            "Quinto e último parágrafo de prosa original, encerrando o artigo.",
        ]
        refrao = "E assim seguiu."  # aparece 2x, abaixo do limiar de dedupe
        linhas = []
        for i in range(5):
            linhas.append(cabecalho)  # repetido 5x -> mobília periódica
            linhas.append(prosa[i])
            linhas.append(rodape)  # repetido 5x + contém URL/fração de página
        linhas.append(refrao)
        linhas.append(refrao)
        limpo = cp.limpar_boilerplate("\n".join(linhas))
        self.assertNotIn(cabecalho, limpo)
        self.assertNotIn("medium.com/artigo-abc", limpo)
        self.assertNotIn("1/18", limpo)
        for p in prosa:
            self.assertIn(p, limpo)
        self.assertIn(refrao, limpo)  # refrão 2x (< 3) preservado

    def test_url_inline_removida_sem_truncar_prosa_e_cauda_quebrada(self):
        bruto = "\n".join([
            "veja em https://exemplo.com/foo detalhes",
            "consulte https://exemplo.com/caminho-longo-quebrado-",
            "foo-bar-baz/",
            "Este parágrafo em português tem acentuação e deve ser preservado.",
        ])
        limpo = cp.limpar_boilerplate(bruto)
        # URL inline removida, prosa ao redor preservada (não descartada)
        self.assertIn("veja em detalhes", limpo)
        self.assertNotIn("https://exemplo.com/foo", limpo)
        # prosa antes da URL quebrada mantida
        self.assertIn("consulte", limpo)
        # cauda de URL quebrada pelo pdftotext removida
        self.assertNotIn("foo-bar-baz/", limpo)
        # linha de prosa normal com acento preservada
        self.assertIn("acentuação e deve ser preservado", limpo)

    def test_pontuacao_de_sentenca_colada_na_url_e_preservada(self):
        self.assertEqual(
            cp.limpar_boilerplate("Verifique https://about.gitlab.com/."),
            "Verifique.",
        )
        self.assertEqual(
            cp.limpar_boilerplate("(veja www.x.com)"),
            "(veja)",
        )
        self.assertEqual(
            cp.limpar_boilerplate("a https://x.com, b"),
            "a, b",
        )
        # URL sem pontuação colada: some sem deixar pontuação, espaço colapsado
        self.assertEqual(
            cp.limpar_boilerplate("veja https://x.com aqui"),
            "veja aqui",
        )

    def test_pontuacao_terminal_de_url_em_linha_a_parte_e_reatada(self):
        # (A) URL hifenizada quebrada: a cauda "final/." leva o ponto de volta
        limpo_a = cp.limpar_boilerplate(
            "veja em https://exemplo.com/caminho-longo-\nfinal/.\nNova frase aqui."
        )
        self.assertIn("veja em.", limpo_a)
        self.assertNotIn("final/", limpo_a)
        self.assertIn("Nova frase aqui.", limpo_a)
        # (B) URL sozinha na linha seguinte: o ponto termina a frase anterior
        limpo_b = cp.limpar_boilerplate(
            "Confira o guia oficial\nhttps://exemplo.com/guia/.\nContinua aqui."
        )
        self.assertIn("Confira o guia oficial.", limpo_b)
        self.assertNotIn("exemplo.com", limpo_b)


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


@unittest.skipUnless(os.path.exists(_MANIFEST), "corpus não preprocessado")
class TestTiposManifesto(unittest.TestCase):
    def test_tipos_sao_ids_validos(self):
        with open(_MANIFEST, encoding="utf-8") as f:
            manifesto = json.load(f)
        for e in manifesto:
            self.assertIn(e["tipo"], TIPOS_VALIDOS, msg=e["arquivo"])

    def test_maioria_classificada(self):
        # best-effort: a curadoria da Etapa 4 classificou ao menos 80% dos textos
        with open(_MANIFEST, encoding="utf-8") as f:
            manifesto = json.load(f)
        desconhecidos = sum(1 for e in manifesto if e["tipo"] == "desconhecido")
        self.assertLessEqual(desconhecidos, len(manifesto) // 5,
                             msg=f"{desconhecidos}/{len(manifesto)} sem tipo")


class TestConstruirManifesto(unittest.TestCase):
    def _escrever(self, caminho, conteudo):
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)

    def test_txt_standalone_e_ingerido(self):
        """Um .txt sem .pdf irmão (ex.: web-*.txt, gerado-*.txt) deve ser
        ingerido como arquivo-fonte, classificado pela pasta que o contém."""
        with tempfile.TemporaryDirectory() as tmp:
            human = os.path.join(tmp, "Human")
            os.makedirs(human)
            self._escrever(
                os.path.join(human, "web-999.txt"),
                "Prosa standalone de teste com bastante conteúdo textual aqui mesmo.",
            )
            entradas = cp.construir_manifesto(tmp)
            arquivos = {e["arquivo"] for e in entradas}
            self.assertIn("Human/web-999.txt", arquivos)
            entrada = next(e for e in entradas if e["arquivo"] == "Human/web-999.txt")
            self.assertEqual(entrada["classe"], "humano")

    def test_txt_companheiro_de_pdf_nao_e_contado_em_dobro(self):
        """Um .txt que é companheiro de um .pdf de mesmo nome-base (gerado pelo
        próprio script a partir do PDF) não deve gerar entrada duplicada."""
        with tempfile.TemporaryDirectory() as tmp:
            human = os.path.join(tmp, "Human")
            os.makedirs(human)
            self._escrever(os.path.join(human, "texto-999.pdf"), "conteudo binario fake")
            self._escrever(os.path.join(human, "texto-999.txt"), "texto extraído anteriormente")
            with mock.patch.object(
                cp, "extrair_pdf",
                return_value="Texto extraído do PDF de teste com prosa suficiente.",
            ):
                entradas = cp.construir_manifesto(tmp)
            relacionados = [e for e in entradas if e["arquivo"] == "Human/texto-999.txt"]
            self.assertEqual(len(relacionados), 1)

    def test_proveniencia_sidecar_mescla_fonte_e_data(self):
        """Se proveniencia.json mapeia um arquivo, fonte/data_verificada da
        entrada vêm do sidecar, sobrepondo os defaults mecânicos."""
        with tempfile.TemporaryDirectory() as tmp:
            human = os.path.join(tmp, "Human")
            os.makedirs(human)
            self._escrever(
                os.path.join(human, "web-998.txt"),
                "Prosa standalone de teste com conteúdo suficiente para o teste.",
            )
            with open(os.path.join(tmp, "proveniencia.json"), "w", encoding="utf-8") as f:
                json.dump({
                    "Human/web-998.txt": {
                        "fonte": "https://exemplo.com/artigo",
                        "data_verificada": "2020-01-01 (Wayback 20200101000000)",
                    }
                }, f)
            entradas = cp.construir_manifesto(tmp)
            entrada = next(e for e in entradas if e["arquivo"] == "Human/web-998.txt")
            self.assertEqual(entrada["fonte"], "https://exemplo.com/artigo")
            self.assertEqual(
                entrada["data_verificada"], "2020-01-01 (Wayback 20200101000000)"
            )


if __name__ == "__main__":
    unittest.main()
