import unittest

from variancia import analisar

# 12 sentenças com alta variância; 3 começam com "o" (artigo) — humano normal.
TEXTO_HUMANO = (
    "O mercado abriu em queda. Ninguém esperava aquilo depois de uma semana "
    "inteira de otimismo com os índices lá fora batendo recorde atrás de recorde. "
    "Vendas despencaram. O pregão virou um caos de ordens canceladas e telefones "
    "tocando sem parar nas mesas de operação. Alguns traders saíram. "
    "O silêncio no fim do dia dizia tudo sobre o tamanho do estrago que ficou. "
    "E agora? Analistas divergem sobre os próximos passos do banco central. "
    "Uns preveem recuperação rápida puxada pelo consumo interno das famílias. "
    "Outros não. Cautela virou a palavra da vez nos relatórios matinais. "
    "Difícil discordar."
)


class TestNaoCanonicas(unittest.TestCase):
    # A4: "Mundo"/"Segundo"/"Casos" não são ordem não-canônica
    def test_sem_falsos_positivos(self):
        r = analisar(
            "Mundo estranho é este nosso, cheio de coisas que ninguém consegue "
            "explicar direito. Segundo o relatório, nada mudou por aqui desde "
            "o mês passado. Casos assim se repetem sempre em cidades pequenas "
            "do interior. A vida segue o seu curso normal, sem grandes "
            "sobressaltos ou surpresas."
        )
        # "Segundo o relatório" não é gerúndio nem subordinador; "Mundo" idem.
        self.assertEqual(r["metricas"]["nao_canonicas"], 0)

    def test_gerundio_e_subordinada_reais_contam(self):
        r = analisar(
            "Pensando bem, ele tinha razão sobre quase tudo que discutimos "
            "naquela tarde longa de trabalho. Quando a chuva parou, saímos "
            "direto para a rua sem nem pegar o guarda-chuva. A rua estava "
            "vazia e escura naquela hora da noite, com poucas pessoas "
            "passando por ali."
        )
        self.assertEqual(r["metricas"]["nao_canonicas"], 2)


class TestCriteriosProporcionais(unittest.TestCase):
    # C2: 3 aberturas com artigo "o" em 12 sentenças não reprovam mais
    def test_artigos_iniciais_nao_reprovam(self):
        r = analisar(TEXTO_HUMANO)
        self.assertEqual(r["inicios_repetidos"], {})

    # C2: trio de sentenças curtas de impacto não é "sequência uniforme"
    def test_sentencas_curtas_consecutivas_nao_sao_sequencia(self):
        r = analisar(
            "A reunião durou quatro horas e ninguém chegou a conclusão alguma. "
            "Vendas caíram. Custos subiram. Clima piorou. "
            "No fim, decidiram contratar uma consultoria externa para revisar "
            "todo o planejamento do próximo trimestre com calma."
        )
        self.assertEqual(r["sequencias_uniformes"], [])

    def test_sequencia_uniforme_real_ainda_detectada(self):
        # 4 sentenças médias (~12 palavras) com comprimento quase idêntico
        r = analisar(
            "A equipe revisou os documentos principais durante toda a manhã de ontem. "
            "O relatório final apontou problemas graves em três seções do contrato. "
            "Os advogados sugeriram mudanças pontuais no texto da cláusula quinta. "
            "A diretoria aprovou as alterações depois de uma longa discussão interna."
        )
        self.assertEqual(len(r["sequencias_uniformes"]), 1)

    def test_texto_humano_variado_atinge_alvo(self):
        r = analisar(TEXTO_HUMANO)
        self.assertTrue(
            r["atingiu_alvo"],
            msg=f"burstiness={r['metricas']['burstiness']} diag={r['diagnostico']}",
        )


class TestInaplicavelPorPoucasPalavras(unittest.TestCase):
    # C? (achado Important): 3+ sentenças mas < 30 palavras precisa ser
    # inaplicável, senão diverge do léxico (que já marca inaplicavel < 30
    # palavras) e reintroduz o deadlock do C1 no caminho das tools separadas.
    def test_poucas_sentencas_curtas_e_menos_de_30_palavras_e_inaplicavel(self):
        r = analisar("Oi. Tudo bem? Como você está? Precisamos conversar.")
        self.assertTrue(r.get("inaplicavel"))
        self.assertNotIn("atingiu_alvo", r)

    def test_30_ou_mais_palavras_com_3_ou_mais_sentencas_nao_e_inaplicavel(self):
        # Guarda: mesmo tendo sentenças curtas, se o total de palavras da
        # prosa bate 30+, a análise continua normal (não vira inaplicável
        # por engano).
        r = analisar(
            "A reunião começou tarde e ninguém sabia exatamente qual era o "
            "motivo do atraso registrado. Custos operacionais subiram "
            "bastante durante o trimestre inteiro sem qualquer aviso prévio "
            "da diretoria. No fim, decidiram remarcar a próxima reunião "
            "geral para a semana seguinte com calma."
        )
        self.assertNotIn("inaplicavel", r)
        self.assertIn("atingiu_alvo", r)


if __name__ == "__main__":
    unittest.main()
