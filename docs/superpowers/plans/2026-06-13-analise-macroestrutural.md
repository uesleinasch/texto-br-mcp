# Análise Macroestrutural (Fase 5) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar uma Fase 5 de análise macroestrutural ao pipeline texto-br que mede sinais de "estrutura encaixada demais" (assinatura de IA), compõe um score 0-100 e gera um plano de perturbação; a entrega passa a ser a Fase 6.

**Architecture:** Espelha o padrão existente `variancia`/`lexico`/`score`: um analisador Python stdlib puro (`estrutura.py`) com um registry de detectores independentes, embrulhado por um tool MCP JS (`estrutura.js`) via `runPython`, com conhecimento curado em `references/estrutura-macro.md`. Gate adaptativo por tipo na `proxima-fase.js`.

**Tech Stack:** Python 3 (stdlib), Node.js ESM, `node:test`, MCP SDK, zod.

**Spec:** `docs/superpowers/specs/2026-06-13-analise-macroestrutural-design.md`

---

## File Structure

**Novos:**
- `server/analysis/estrutura.py` — outline + registry de detectores + score + relatório + `main()`.
- `server/tools/estrutura.js` — tool `texto_br_estrutura`.
- `references/estrutura-macro.md` — conhecimento, matriz de calibração, checklist.

**Modificados:**
- `server/analysis/texto_util.py` — `parsear_blocos(texto)`.
- `server/knowledge/phases.js` — guidance/sections/checklist da Fase 5, entrega → 6, constantes de calibração.
- `server/session/state.js` — campo `estruturaAtingida`, limites de fase 6.
- `server/tools/proxima-fase.js` — schema `max(6)`, gate da Fase 5, nota de rascunhos → Fase 6.
- `server/tools/checklist.js` — aceitar fase 5.
- `server/content/loader.js` — registrar `estrutura-macro`.
- `server/server.js` — registrar tool + atualizar `INSTRUCTIONS`.
- `server/test/analysis.test.js`, `server/test/content.test.js`, `server/test/e2e.test.js`.
- `server/README.md`, `SKILL.md`.

**Contrato de detector** (válido para todos os detectores; não repetir, referenciar daqui):
```python
{
  "id": str, "nome": str,
  "aplicavel": bool,        # False quando a estrutura-alvo não existe
  "subscore": float,        # 0.0-1.0, 1 = humano/variado
  "peso": int,
  "metricas": dict,
  "diagnostico": [str],
  "perturbacoes": [str],    # só quando subscore baixo
}
```

---

## Task 1: `parsear_blocos` em texto_util.py

**Files:**
- Modify: `server/analysis/texto_util.py`
- Verify: `python3 -c` inline

- [ ] **Step 1: Implementar `parsear_blocos`**

Adicionar ao final de `server/analysis/texto_util.py`:

```python
def parsear_blocos(texto):
    """Lista ordenada de blocos do markdown: heading, paragrafo, lista,
    codigo, citacao. Reusa a lógica de cerca de limpar_markdown (cerca fecha
    só com o mesmo caractere e comprimento >= o de abertura)."""
    blocos = []
    cerca_aberta = None
    buffer_codigo = []
    buffer_prosa = []

    def fechar_prosa():
        if buffer_prosa:
            texto_p = "\n".join(buffer_prosa).strip()
            if texto_p:
                blocos.append({"tipo": "paragrafo", "nivel": 0, "texto": texto_p})
            buffer_prosa.clear()

    for linha in texto.split("\n"):
        m_cerca = re.match(r"^\s*(`{3,}|~{3,})", linha)
        if m_cerca:
            if cerca_aberta is None:
                fechar_prosa()
                cerca_aberta = m_cerca.group(1)
                buffer_codigo = []
            elif m_cerca.group(1)[0] == cerca_aberta[0] and len(m_cerca.group(1)) >= len(cerca_aberta):
                blocos.append({"tipo": "codigo", "nivel": 0, "texto": "\n".join(buffer_codigo)})
                cerca_aberta = None
            continue
        if cerca_aberta is not None:
            buffer_codigo.append(linha)
            continue
        m_h = re.match(r"^\s*(#{1,6})\s+(.*)$", linha)
        if m_h:
            fechar_prosa()
            blocos.append({"tipo": "heading", "nivel": len(m_h.group(1)), "texto": m_h.group(2).strip()})
            continue
        if re.match(r"^\s*([-*+]\s|\d+[.)]\s)", linha):
            fechar_prosa()
            blocos.append({"tipo": "lista", "nivel": 0, "texto": linha.strip()})
            continue
        if re.match(r"^\s*>", linha):
            fechar_prosa()
            blocos.append({"tipo": "citacao", "nivel": 0, "texto": linha.lstrip("> ").strip()})
            continue
        if linha.strip() == "":
            fechar_prosa()
            continue
        buffer_prosa.append(linha)
    fechar_prosa()
    return blocos
```

- [ ] **Step 2: Verificar import e comportamento**

Run:
```bash
cd server/analysis && python3 -c "import texto_util; b=texto_util.parsear_blocos('# T\n\nUm parágrafo aqui.\n\n## A\n\nOutro.\n\n\`\`\`\ncodigo\n\`\`\`'); print([(x['tipo'],x['nivel']) for x in b])"
```
Expected: `[('heading', 1), ('paragrafo', 0), ('heading', 2), ('paragrafo', 0), ('codigo', 0)]`

- [ ] **Step 3: Commit**

```bash
git add server/analysis/texto_util.py
git commit -m "feat(estrutura): parsear_blocos para parsing estrutural de markdown"
```

---

## Task 2: estrutura.py — outline + harness de score + Detector 1 (simetria)

**Files:**
- Create: `server/analysis/estrutura.py`
- Test: `server/test/analysis.test.js`

- [ ] **Step 1: Escrever os testes que falham**

Adicionar ao final de `server/test/analysis.test.js`:

```javascript
// --- Análise macroestrutural ---

const ESTR_IA = `# Hábitos que transformam

## Entendendo o problema

A rotina molda quem somos ao longo dos anos. Pequenas escolhas diárias se acumulam em direções inesperadas. No fim, somos o que repetimos todo santo dia.

## Aplicando a mudança

Comece pequeno e seja consistente com o processo. A constância vence a intensidade em quase tudo. Afinal, ninguém muda de uma vez só.

## Construindo o futuro

O amanhã se constrói no gesto repetido de hoje. Cada dia é um tijolo na parede que você ergue. No fundo, é tudo uma questão de paciência.`;

const ESTR_HUMANO = `# O sábado em que parei de correr

Comecei a meditar num sábado qualquer de 2019, mais por teimosia do que por convicção, e o tédio dos primeiros dias quase me venceu. A cadeira rangia. Eu olhava o relógio do micro-ondas a cada dois minutos achando que tinha passado meia hora.

## O que mudou (e o que não mudou)

Na terceira semana o sono melhorou. Não foi epifania nenhuma, foi só uma noite em que dormi sem rolar na cama, e aí outra, e aí virou hábito sem eu perceber direito quando.

Os colegas notaram antes de mim. Diziam que eu tinha ficado mais paciente nas reuniões intermináveis de quarta, aquelas que não levam a lugar nenhum e que eu detestava com todas as forças.

Hoje ainda perco a paciência no trânsito. Meditar não me fez santo. Só me deu uns segundos a mais entre o estímulo e a besteira que eu ia falar, e às vezes esses segundos bastam, às vezes não bastam coisa nenhuma e eu xingo igual.`;

test('estrutura: texto IA-encaixado reprova com plano de perturbação', async () => {
  const r = await runPython('estrutura.py', JSON.stringify({ texto: ESTR_IA, tipo: 'blog' }));
  assert.equal(r.atingiu_alvo, false, JSON.stringify(r.score));
  assert.ok(r.score.total < 70, `pontuou ${r.score.total}`);
  assert.ok(r.relatorio.includes('Plano de perturbação'));
});

test('estrutura: simetria detecta seções gêmeas e títulos paralelos', async () => {
  const r = await runPython('estrutura.py', JSON.stringify({ texto: ESTR_IA, tipo: 'blog' }));
  const sim = r.detectores.find((d) => d.id === 'simetria_secoes');
  assert.ok(sim.aplicavel);
  assert.ok(sim.subscore < 0.5, `subscore ${sim.subscore}`);
  assert.ok(sim.perturbacoes.length >= 1);
});

test('estrutura: texto humano-variado passa', async () => {
  const r = await runPython('estrutura.py', JSON.stringify({ texto: ESTR_HUMANO, tipo: 'blog' }));
  assert.ok(r.score.total >= 70, `pontuou ${r.score.total}`);
  assert.equal(r.atingiu_alvo, true);
});

test('estrutura: texto curto demais retorna erro', async () => {
  const r = await runPython('estrutura.py', JSON.stringify({ texto: 'Uma frase só.', tipo: 'blog' }));
  assert.ok(r.erro);
});
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `cd server && node --test 'test/*.test.js' 2>&1 | grep -A2 estrutura`
Expected: FAIL (`estrutura.py` não existe → `Analisador falhou`).

- [ ] **Step 3: Criar `server/analysis/estrutura.py` (outline + harness + helpers + Detector 1)**

```python
#!/usr/bin/env python3
"""Análise macroestrutural (naturalidade estrutural) para o pipeline texto-br.

Lê JSON no stdin: {"texto": rascunho, "tipo": id do tipo}. Mede sinais
macroestruturais de IA ("estrutura encaixada demais") via um registry de
detectores e compõe um score 0-100. Este script mede e diagnostica; quem
reescreve (perturba a estrutura) é o modelo.

Calibração por tipo: ver CALIBRACAO_ESTRUTURA. Fonte de verdade do conjunto de
gate e dos alvos é knowledge/phases.js (TIPOS_ESTRUTURA_GATE / CALIBRACAO_ESTRUTURA);
os valores são replicados aqui com este comentário apontando para lá.
"""

import json
import re
import statistics
import sys

from texto_util import contar_palavras, dividir_sentencas, parsear_blocos

# Espelha TIPOS_ESTRUTURA_GATE / CALIBRACAO_ESTRUTURA em knowledge/phases.js.
TIPOS_GATE = ["blog", "capitulo", "tecnico", "explicativo", "podcast", "video"]
ALVO_PADRAO = 70

MARCADORES_LICAO = [
    "no fim", "no fim das contas", "no fundo", "afinal", "é isso",
    "talvez seja", "o que importa", "a verdade é", "no final", "resta",
    "moral da história", "e é por isso", "é sobre isso", "se há algo",
]
SIGNPOSTS = [
    "primeiro", "segundo", "terceiro", "em seguida", "depois", "por fim",
    "finalmente", "a seguir", "para começar", "em primeiro lugar",
    "em segundo lugar", "por último", "agora que",
]
CONECTIVOS_INICIAIS = [
    "além disso", "no entanto", "por outro lado", "portanto", "contudo",
    "entretanto", "dessa forma", "desse modo", "por fim", "em suma",
    "em conclusão", "ou seja", "nesse sentido",
]


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def interp(valor, ruim, bom):
    """Mapeia valor para 0-1: <=ruim → 0, >=bom → 1, linear no meio.
    Funciona tanto para bom>ruim quanto bom<ruim."""
    if bom == ruim:
        return 1.0 if valor >= bom else 0.0
    return clamp((valor - ruim) / (bom - ruim))


def primeiro_termo(s):
    m = re.match(r"^[\"'«(]*([\wÀ-ÿ]+)", s.strip())
    return m.group(1).lower() if m else ""


def comeca_com(texto, lista):
    base = texto.strip().lower().lstrip("\"'«( ")
    return any(base.startswith(p) for p in lista)


def contem_marcador(texto, lista):
    base = texto.strip().lower()
    return any(p in base for p in lista)


def montar_outline(blocos):
    """Agrupa blocos em seções. Se há um único # como primeiro heading, é o
    título do documento e o nível de seção é 2; senão é o menor nível presente."""
    headings = [b for b in blocos if b["tipo"] == "heading"]
    titulo = None
    if headings and headings[0]["nivel"] == 1 and sum(h["nivel"] == 1 for h in headings) == 1:
        titulo = headings[0]["texto"]
        nivel_secao = 2
    elif headings:
        nivel_secao = min(h["nivel"] for h in headings)
    else:
        nivel_secao = None

    secoes = []
    atual = None
    for b in blocos:
        if b["tipo"] == "heading" and titulo is not None and b["texto"] == titulo and not secoes and atual is None:
            continue  # pula o título do documento
        if b["tipo"] == "heading" and nivel_secao is not None and b["nivel"] == nivel_secao:
            atual = {"titulo": b["texto"], "nivel": b["nivel"], "paragrafos": [], "subsecoes": []}
            secoes.append(atual)
        elif b["tipo"] == "heading" and nivel_secao is not None and b["nivel"] > nivel_secao:
            if atual is not None:
                atual["subsecoes"].append(b["texto"])
        elif b["tipo"] == "paragrafo":
            if atual is not None:
                atual["paragrafos"].append(b["texto"])
            else:
                secoes.append({"titulo": None, "nivel": 0, "paragrafos": [b["texto"]], "subsecoes": [], "_sem_heading": True})
                atual = secoes[-1] if not headings else None
    # Quando não há headings, junta tudo numa pseudo-seção de parágrafos soltos:
    if nivel_secao is None:
        paras = [b["texto"] for b in blocos if b["tipo"] == "paragrafo"]
        secoes = [{"titulo": None, "nivel": 0, "paragrafos": paras, "subsecoes": [], "_sem_heading": True}]

    for s in secoes:
        s["palavras"] = sum(contar_palavras(p) for p in s["paragrafos"])
    return {"titulo": titulo, "nivel_secao": nivel_secao, "secoes": secoes,
            "tem_headings": bool(headings)}


def paragrafos_de_prosa(outline):
    return [p for s in outline["secoes"] for p in s["paragrafos"]]


# ----- Detector 1: Simetria de seções (peso 25) -----
def detector_simetria(outline, blocos, tipo):
    secoes = [s for s in outline["secoes"] if s.get("titulo")]
    base = {"id": "simetria_secoes", "nome": "Simetria de seções", "peso": 25}
    if len(secoes) < 3:
        return {**base, "aplicavel": False, "subscore": 1.0, "metricas": {"secoes": len(secoes)},
                "diagnostico": ["Menos de 3 seções: simetria de seções não se aplica."],
                "perturbacoes": []}

    palavras = [s["palavras"] for s in secoes]
    media = statistics.mean(palavras)
    cv_tam = statistics.pstdev(palavras) / media if media else 0.0

    titulos = [s["titulo"] for s in secoes]
    frac_ger = sum(1 for t in titulos if primeiro_termo(t).endswith("ndo")) / len(titulos)
    frac_perg = sum(1 for t in titulos if t.strip().endswith("?")) / len(titulos)
    primeiros = [primeiro_termo(t) for t in titulos]
    frac_mesmo = max(primeiros.count(p) for p in set(primeiros)) / len(primeiros)
    paralelismo = max(frac_ger, frac_perg, frac_mesmo)

    n_sub = [len(s["subsecoes"]) for s in secoes]
    if all(n == n_sub[0] for n in n_sub) and n_sub[0] >= 2:
        sub_sub = 0.0
    else:
        msub = statistics.mean(n_sub) if n_sub else 0
        cv_sub = (statistics.pstdev(n_sub) / msub) if msub else 1.0
        sub_sub = interp(cv_sub, ruim=0.1, bom=0.5)

    s_tam = interp(cv_tam, ruim=0.15, bom=0.45)
    s_tit = 1.0 - interp(paralelismo, ruim=0.85, bom=0.4)  # paralelismo alto → baixo
    subscore = round((s_tam + s_tit + sub_sub) / 3, 3)

    diag, pert = [], []
    if s_tam < 0.6:
        diag.append(f"Seções de tamanho uniforme (CV {cv_tam:.2f}): {palavras} palavras.")
        pert.append("Deixe uma seção respirar (corte ~metade) e outra ir fundo (dobre); funda as menores.")
    if paralelismo >= 0.5:
        diag.append(f"Títulos com forma paralela ({paralelismo:.0%}): {titulos}.")
        pert.append("Reescreva >= 2 títulos com forma gramatical diferente (pergunta, frase nominal, imperativo).")
    if sub_sub < 0.5:
        diag.append("Número de subseções por seção uniforme.")
        pert.append("Varie a profundidade: deixe uma seção sem subseções e outra com mais.")
    return {**base, "aplicavel": True, "subscore": subscore,
            "metricas": {"secoes": len(secoes), "cv_tamanho": round(cv_tam, 3),
                         "paralelismo_titulos": round(paralelismo, 3), "palavras_por_secao": palavras},
            "diagnostico": diag or ["OK: seções com variação saudável."], "perturbacoes": pert}


DETECTORES = [detector_simetria]


def calcular(texto, tipo):
    blocos = parsear_blocos(texto)
    outline = montar_outline(blocos)
    paras = paragrafos_de_prosa(outline)
    if len(paras) < 4:
        return {"erro": "Texto com menos de 4 parágrafos de prosa; análise macroestrutural não se aplica."}

    alvo = ALVO_PADRAO
    resultados = [d(outline, blocos, tipo) for d in DETECTORES]
    aplic = [r for r in resultados if r["aplicavel"]]
    if not aplic:
        total = 100.0
    else:
        soma_peso = sum(r["peso"] for r in aplic)
        total = round(sum(r["peso"] * r["subscore"] for r in aplic) / soma_peso * 100, 1)
    atingiu = total >= alvo or not aplic

    return {
        "score": {"total": total, "alvo": alvo, "tipo": tipo, "gate": tipo in TIPOS_GATE},
        "atingiu_alvo": atingiu,
        "detectores": resultados,
        "outline": {"secoes": len(outline["secoes"]), "tem_headings": outline["tem_headings"]},
    }


def formatar_relatorio(resultado):
    if "erro" in resultado:
        return resultado["erro"]
    s = resultado["score"]
    veredicto = "ALVO ATINGIDO" if resultado["atingiu_alvo"] else "REESCREVER E MEDIR DE NOVO"
    linhas = [
        "## Score de naturalidade estrutural", "",
        f"**Total: {s['total']} / 100** | alvo >= {s['alvo']} | tipo: {s['tipo']} "
        f"({'gate' if s['gate'] else 'advisory'}) | veredicto: {veredicto}", "",
        "| Detector | subscore | peso | pts |", "| --- | --- | --- | --- |",
    ]
    for r in resultado["detectores"]:
        if r["aplicavel"]:
            pts = round(r["peso"] * r["subscore"], 1)
            linhas.append(f"| {r['nome']} | {r['subscore']} | {r['peso']} | {pts} |")
        else:
            linhas.append(f"| {r['nome']} | não se aplica | {r['peso']} | — |")
    linhas += ["", "### Diagnóstico", ""]
    for r in resultado["detectores"]:
        for d in r["diagnostico"]:
            linhas.append(f"- [{r['nome']}] {d}")
    pert = sorted([r for r in resultado["detectores"] if r["aplicavel"] and r["perturbacoes"]],
                  key=lambda r: r["subscore"])
    if pert and not resultado["atingiu_alvo"]:
        linhas += ["", "## Plano de perturbação", "",
                   "Priorizado pelos detectores mais fracos. Aplique e meça de novo:", ""]
        for r in pert:
            for p in r["perturbacoes"]:
                linhas.append(f"- {p}")
    linhas += ["", f"**Veredicto: {veredicto}**"]
    return "\n".join(linhas)


def main():
    entrada = json.load(sys.stdin)
    resultado = calcular(entrada["texto"], entrada.get("tipo", "geral"))
    resultado["relatorio"] = formatar_relatorio(resultado)
    json.dump(resultado, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Rodar os 4 testes da Task 2**

Run: `cd server && node --test 'test/*.test.js' 2>&1 | grep -E "estrutura|pass|fail"`
Expected: os 4 testes `estrutura: ...` passam. Se `ESTR_HUMANO` não chegar a 70 só com o Detector 1, ajustar limiares de `interp` no `detector_simetria` (são iniciais/ajustáveis por design) até as fixtures separarem corretamente.

- [ ] **Step 5: Commit**

```bash
git add server/analysis/estrutura.py server/test/analysis.test.js
git commit -m "feat(estrutura): outline + score + detector de simetria de seções"
```

---

## Task 3: Detector 2 — Inflação de subtópicos (peso 20)

**Files:**
- Modify: `server/analysis/estrutura.py`
- Test: `server/test/analysis.test.js`

- [ ] **Step 1: Teste que falha**

Adicionar em `analysis.test.js`:

```javascript
test('estrutura: inflação de subtópicos detecta seções finas', async () => {
  const md = `# Guia\n\n## A\n\nUma linha curta só aqui.\n\n## B\n\nOutra linha curta aqui.\n\n## C\n\nMais uma curtíssima.\n\n## D\n\nE a última bem curta.`;
  const r = await runPython('estrutura.py', JSON.stringify({ texto: md, tipo: 'blog' }));
  const inf = r.detectores.find((d) => d.id === 'inflacao_subtopicos');
  assert.ok(inf.aplicavel);
  assert.ok(inf.subscore < 0.6, `subscore ${inf.subscore}`);
});
```

- [ ] **Step 2: Rodar para falhar**

Run: `cd server && node --test 'test/*.test.js' 2>&1 | grep "inflação"`
Expected: FAIL (`inf` é `undefined` → throw).

- [ ] **Step 3: Implementar `detector_subtopicos` e registrá-lo**

Adicionar a função antes de `DETECTORES =` e incluí-la na lista:

```python
# ----- Detector 2: Inflação de subtópicos (peso 20) -----
FATOR_DENSIDADE = {"tecnico": 1.8}  # tecnico tolera mais headings

def detector_subtopicos(outline, blocos, tipo):
    base = {"id": "inflacao_subtopicos", "nome": "Inflação de subtópicos", "peso": 20}
    headings = [b for b in blocos if b["tipo"] == "heading"]
    secoes = outline["secoes"]
    n_headings = sum(1 for b in headings if b["nivel"] >= (outline["nivel_secao"] or 2))
    palavras_total = sum(s["palavras"] for s in secoes)
    if n_headings < 1 or palavras_total < 1:
        return {**base, "aplicavel": False, "subscore": 1.0,
                "metricas": {"headings": n_headings}, "diagnostico": ["Sem subtítulos: não se aplica."],
                "perturbacoes": []}

    densidade = n_headings / (palavras_total / 100)
    fator = FATOR_DENSIDADE.get(tipo, 1.0)
    finas = [s for s in secoes if s.get("titulo") and s["palavras"] < 60]
    frac_finas = len(finas) / max(1, sum(1 for s in secoes if s.get("titulo")))

    s_dens = 1.0 - interp(densidade, ruim=3.5 * fator, bom=1.5 * fator)
    s_finas = 1.0 - interp(frac_finas, ruim=0.7, bom=0.3)
    subscore = round((s_dens + s_finas) / 2, 3)

    diag, pert = [], []
    if s_dens < 0.6:
        diag.append(f"Densidade alta de subtítulos: {n_headings} em {palavras_total} palavras "
                    f"(1 a cada {round(palavras_total / n_headings)}).")
        pert.append("Funda subtítulos finos; mantenha só os que marcam viradas reais de assunto.")
    if s_finas < 0.6:
        diag.append(f"{len(finas)} seção(ões) com menos de 60 palavras.")
        pert.append("Rebaixe seções finas a parágrafo com frase-guia, sem heading próprio.")
    return {**base, "aplicavel": True, "subscore": subscore,
            "metricas": {"headings": n_headings, "densidade_por_100w": round(densidade, 2),
                         "frac_secoes_finas": round(frac_finas, 2)},
            "diagnostico": diag or ["OK: densidade de subtítulos saudável."], "perturbacoes": pert}
```

Atualizar: `DETECTORES = [detector_simetria, detector_subtopicos]`.

- [ ] **Step 4: Rodar e ver passar**

Run: `cd server && node --test 'test/*.test.js' 2>&1 | tail -5`
Expected: todos verdes (rever que `ESTR_HUMANO` segue >= 70 e `ESTR_IA` < 70).

- [ ] **Step 5: Commit**

```bash
git add server/analysis/estrutura.py server/test/analysis.test.js
git commit -m "feat(estrutura): detector de inflação de subtópicos"
```

---

## Task 4: Detector 3 — Parágrafo-lição / kicker uniforme (peso 20)

**Files:**
- Modify: `server/analysis/estrutura.py`
- Test: `server/test/analysis.test.js`

- [ ] **Step 1: Teste que falha**

```javascript
test('estrutura: kicker uniforme detectado em ESTR_IA', async () => {
  const r = await runPython('estrutura.py', JSON.stringify({ texto: ESTR_IA, tipo: 'blog' }));
  const k = r.detectores.find((d) => d.id === 'kicker_uniforme');
  assert.ok(k.aplicavel);
  assert.ok(k.subscore < 0.6, `subscore ${k.subscore}`);
});
```

- [ ] **Step 2: Rodar para falhar**

Run: `cd server && node --test 'test/*.test.js' 2>&1 | grep kicker`
Expected: FAIL.

- [ ] **Step 3: Implementar `detector_kicker` e registrá-lo**

```python
# ----- Detector 3: Parágrafo-lição / kicker uniforme (peso 20) -----
def detector_kicker(outline, blocos, tipo):
    base = {"id": "kicker_uniforme", "nome": "Parágrafo-lição (kicker)", "peso": 20}
    elegiveis, com_kicker = 0, 0
    for p in paragrafos_de_prosa(outline):
        ss = dividir_sentencas(p)
        if len(ss) < 2:
            continue
        elegiveis += 1
        ult = contar_palavras(ss[-1])
        corpo = statistics.mean(contar_palavras(s) for s in ss[:-1])
        razao = ult / corpo if corpo else 1.0
        kicker = razao < 0.6 or contem_marcador(ss[-1], MARCADORES_LICAO) or \
            (primeiro_termo(ss[-1]) == "e" and ult <= 8)
        if kicker:
            com_kicker += 1
    if elegiveis < 4:
        return {**base, "aplicavel": False, "subscore": 1.0,
                "metricas": {"paragrafos_elegiveis": elegiveis},
                "diagnostico": ["Menos de 4 parágrafos multi-sentença: não se aplica."], "perturbacoes": []}
    frac = com_kicker / elegiveis
    subscore = round(interp(frac, ruim=0.75, bom=0.4), 3)
    diag, pert = [], []
    if subscore < 0.7:
        diag.append(f"{com_kicker} de {elegiveis} parágrafos fecham numa 'lição' curta ({frac:.0%}).")
        pert.append("Deixe ~3 parágrafos terminarem no meio do raciocínio, sem moral arredondada.")
        pert.append("Mova o fecho de um parágrafo para o início do seguinte.")
    return {**base, "aplicavel": True, "subscore": subscore,
            "metricas": {"paragrafos_elegiveis": elegiveis, "com_kicker": com_kicker, "frac": round(frac, 2)},
            "diagnostico": diag or ["OK: fechos de parágrafo variados."], "perturbacoes": pert}
```

Atualizar `DETECTORES` para incluir `detector_kicker`.

- [ ] **Step 4: Rodar e ver passar**

Run: `cd server && node --test 'test/*.test.js' 2>&1 | tail -5`
Expected: todos verdes.

- [ ] **Step 5: Commit**

```bash
git add server/analysis/estrutura.py server/test/analysis.test.js
git commit -m "feat(estrutura): detector de parágrafo-lição (kicker uniforme)"
```

---

## Task 5: Detector 4 — Frases de efeito em sequência (peso 15)

**Files:**
- Modify: `server/analysis/estrutura.py`
- Test: `server/test/analysis.test.js`

- [ ] **Step 1: Teste que falha**

```javascript
test('estrutura: frases de efeito em sequência', async () => {
  const md = `# T\n\nA vida é curta.\n\nO tempo não volta.\n\nCada dia conta.\n\nFaça valer.\n\nAgora desenvolvo um parágrafo de verdade, com mais de uma sentença e alguma respiração, para não ser bordão. Ele segue por aqui sem pressa.`;
  const r = await runPython('estrutura.py', JSON.stringify({ texto: md, tipo: 'blog' }));
  const f = r.detectores.find((d) => d.id === 'frases_efeito');
  assert.ok(f.aplicavel);
  assert.ok(f.subscore < 0.6, `subscore ${f.subscore}`);
});
```

- [ ] **Step 2: Rodar para falhar**

Run: `cd server && node --test 'test/*.test.js' 2>&1 | grep "efeito"`
Expected: FAIL.

- [ ] **Step 3: Implementar `detector_frases_efeito` e registrá-lo**

```python
# ----- Detector 4: Frases de efeito em sequência (peso 15) -----
def detector_frases_efeito(outline, blocos, tipo):
    base = {"id": "frases_efeito", "nome": "Frases de efeito em sequência", "peso": 15}
    paras = paragrafos_de_prosa(outline)
    if len(paras) < 5:
        return {**base, "aplicavel": False, "subscore": 1.0, "metricas": {"paragrafos": len(paras)},
                "diagnostico": ["Menos de 5 parágrafos: não se aplica."], "perturbacoes": []}
    bordao = []
    for p in paras:
        ss = dividir_sentencas(p)
        bordao.append(len(ss) == 1 and contar_palavras(ss[0]) <= 8)
    frac = sum(bordao) / len(bordao)
    maior_corrida = corrida = 0
    for b in bordao:
        corrida = corrida + 1 if b else 0
        maior_corrida = max(maior_corrida, corrida)
    s_frac = interp(frac, ruim=0.45, bom=0.15)
    s_corr = 1.0 if maior_corrida < 2 else (0.4 if maior_corrida == 2 else 0.0)
    subscore = round(min(s_frac, s_corr), 3)
    diag, pert = [], []
    if subscore < 0.7:
        diag.append(f"{sum(bordao)} parágrafos-bordão de {len(paras)} (maior sequência: {maior_corrida}).")
        pert.append("Bordões em sequência: funda ao menos um ao parágrafo vizinho ou desenvolva-o em 2-3 sentenças.")
    return {**base, "aplicavel": True, "subscore": subscore,
            "metricas": {"paragrafos": len(paras), "bordoes": sum(bordao), "maior_sequencia": maior_corrida},
            "diagnostico": diag or ["OK: bordões dosados."], "perturbacoes": pert}
```

Atualizar `DETECTORES`.

- [ ] **Step 4: Rodar e ver passar**

Run: `cd server && node --test 'test/*.test.js' 2>&1 | tail -5`
Expected: todos verdes.

- [ ] **Step 5: Commit**

```bash
git add server/analysis/estrutura.py server/test/analysis.test.js
git commit -m "feat(estrutura): detector de frases de efeito em sequência"
```

---

## Task 6: Detector 5 — Progressão sinalizada (peso 20)

**Files:**
- Modify: `server/analysis/estrutura.py`
- Test: `server/test/analysis.test.js`

- [ ] **Step 1: Teste que falha**

```javascript
test('estrutura: progressão sinalizada (escada de signposts)', async () => {
  const md = `# Plano\n\n## Primeiro passo\n\nPara começar, organize a mesa de trabalho com calma e atenção aos detalhes do dia.\n\n## Em seguida\n\nDepois, defina as três prioridades do dia com calma e atenção aos detalhes.\n\n## Por fim\n\nFinalmente, revise tudo o que foi feito com calma e atenção aos detalhes restantes.`;
  const r = await runPython('estrutura.py', JSON.stringify({ texto: md, tipo: 'blog' }));
  const p = r.detectores.find((d) => d.id === 'progressao_sinalizada');
  assert.ok(p.aplicavel);
  assert.ok(p.subscore < 0.6, `subscore ${p.subscore}`);
});
```

- [ ] **Step 2: Rodar para falhar**

Run: `cd server && node --test 'test/*.test.js' 2>&1 | grep "progressão"`
Expected: FAIL.

- [ ] **Step 3: Implementar `detector_progressao` e registrá-lo**

```python
# ----- Detector 5: Progressão sinalizada (peso 20) -----
def detector_progressao(outline, blocos, tipo):
    base = {"id": "progressao_sinalizada", "nome": "Progressão sinalizada", "peso": 20}
    secoes = outline["secoes"]
    paras = paragrafos_de_prosa(outline)
    if len([s for s in secoes if s.get("titulo")]) < 3 and len(paras) < 6:
        return {**base, "aplicavel": False, "subscore": 1.0, "metricas": {},
                "diagnostico": ["Estrutura insuficiente: não se aplica."], "perturbacoes": []}

    com_titulo = [s for s in secoes if s.get("titulo")]
    titulos_signpost = sum(1 for s in com_titulo if comeca_com(s["titulo"], SIGNPOSTS)
                           or re.match(r"^\d+[.)]?\s", s["titulo"].strip()))
    aberturas_signpost = sum(1 for p in paras if comeca_com(p, SIGNPOSTS))
    aberturas_conectivo = sum(1 for s in com_titulo if s["paragrafos"] and comeca_com(s["paragrafos"][0], CONECTIVOS_INICIAIS))
    intro_outro = False
    if len(com_titulo) >= 3:
        prim, ult = com_titulo[0], com_titulo[-1]
        intro_outro = prim["palavras"] < 0.7 * statistics.mean([s["palavras"] for s in com_titulo]) and \
            any(contem_marcador(p, MARCADORES_LICAO) for p in ult["paragrafos"])

    penal = 0.0
    penal += 0.35 if (titulos_signpost >= 2 or aberturas_signpost >= 3) else 0.0
    penal += 0.30 if aberturas_conectivo >= 2 else 0.0
    penal += 0.25 if intro_outro else 0.0
    subscore = round(clamp(1.0 - penal), 3)

    diag, pert = [], []
    if titulos_signpost >= 2 or aberturas_signpost >= 3:
        diag.append("Escada de signposts (primeiro/depois/por fim) na progressão.")
        pert.append("Remova a numeração e os 'primeiro/depois/por fim' explícitos; deixe a transição implícita.")
    if aberturas_conectivo >= 2:
        diag.append("Seções abrindo em corrente de conectivos lógicos.")
        pert.append("Abra ao menos uma seção direto no concreto, sem conectivo de ligação.")
    if intro_outro:
        diag.append("Primeira e última seção formam moldura intro/conclusão simétrica.")
        pert.append("Quebre a simetria intro/conclusão: comece no meio da ação ou termine sem fechar o laço.")
    return {**base, "aplicavel": True, "subscore": subscore,
            "metricas": {"titulos_signpost": titulos_signpost, "aberturas_signpost": aberturas_signpost,
                         "aberturas_conectivo": aberturas_conectivo, "intro_outro_simetrico": intro_outro},
            "diagnostico": diag or ["OK: progressão sem andaime explícito."], "perturbacoes": pert}
```

Atualizar `DETECTORES = [detector_simetria, detector_subtopicos, detector_kicker, detector_frases_efeito, detector_progressao]`.

- [ ] **Step 4: Rodar a suíte de análise inteira**

Run: `cd server && node --test 'test/*.test.js' 2>&1 | grep -E "tests|pass|fail"`
Expected: todos os testes `estrutura: ...` verdes; `ESTR_IA` < 70 e `ESTR_HUMANO` >= 70.

- [ ] **Step 5: Commit**

```bash
git add server/analysis/estrutura.py server/test/analysis.test.js
git commit -m "feat(estrutura): detector de progressão sinalizada; registry completo"
```

---

## Task 7: reference `estrutura-macro.md` + registro no loader + teste de conteúdo

**Files:**
- Create: `references/estrutura-macro.md`
- Modify: `server/content/loader.js`
- Test: `server/test/content.test.js`

- [ ] **Step 1: Criar `references/estrutura-macro.md`**

Conteúdo com seções numeradas `## N.` (mesmo formato das outras references). Mínimo:

```markdown
# Humanização macroestrutural

## 1. O sinal: estrutura encaixada demais

Texto de IA tende a uma arquitetura simétrica e previsível: seções do mesmo
tamanho, títulos da mesma forma, cada parágrafo fechando numa lição, bordões em
sequência, subtópicos em excesso e progressão linear com signposts. Humanizar a
macroestrutura é introduzir assimetria deliberada sem perder a clareza.

## 2. Simetria de seções

Sinal: seções de tamanho quase igual; títulos com a mesma forma gramatical
(todos gerúndio, todos pergunta, mesmo primeiro termo); mesmo número de
subseções em cada uma. Perturbação: deixe uma seção curta e outra longa; funda
seções gêmeas; reescreva títulos com formas variadas; varie a profundidade.

## 3. Inflação de subtópicos

Sinal: muitos subtítulos para pouco texto; seções "finas" de poucas linhas.
Perturbação: funda os subtítulos finos; só mantenha heading onde há virada real
de assunto. Tipos técnicos toleram mais seccionamento.

## 4. Parágrafo-lição (kicker)

Sinal: quase todo parágrafo termina numa frase curta e sentenciosa ("no fim...",
"afinal...", "é isso"). Perturbação: deixe parágrafos terminarem no meio do
raciocínio; mova o fecho para o início do parágrafo seguinte.

## 5. Frases de efeito em sequência

Sinal: vários parágrafos de uma só frase curta de impacto, enfileirados.
Perturbação: funda bordões ao texto vizinho ou desenvolva-os.

## 6. Progressão sinalizada

Sinal: escada de "primeiro/depois/por fim", seções abrindo em conectivo lógico,
intro e conclusão simétricas. Perturbação: torne a transição implícita; comece
no meio da ação; não feche todos os laços.

## 7. Matriz de calibração por tipo

| Tipo | Intensidade | Gate | Alvo |
| --- | --- | --- | --- |
| blog, capitulo, tecnico, explicativo, podcast, video | alta | bloqueia | 70 |
| geral, corporativo | média | advisory | 70 |
| email, comentario-blog, comentario-jira, chat | baixa | advisory | 70 |

Conversacionais quase não têm macroestrutura: a maioria dos detectores não se
aplica e a etapa é praticamente transparente.

## 8. Checklist de saída da Fase 5

- [ ] Seções têm tamanhos visivelmente diferentes (não há molde único).
- [ ] Títulos não compartilham a mesma forma gramatical.
- [ ] Nem todo parágrafo fecha numa "lição"; alguns terminam no meio do raciocínio.
- [ ] Não há sequência de frases de efeito isoladas.
- [ ] Subtítulos só onde há virada real de assunto.
- [ ] A progressão não usa escada de signposts nem moldura intro/conclusão simétrica.
- [ ] O texto continua claro: a assimetria não virou bagunça.
```

- [ ] **Step 2: Registrar no loader**

Em `server/content/loader.js`, adicionar `'estrutura-macro'` ao array `FILES`:

```javascript
const FILES = [
  'tipos-de-texto',
  'gramatica-pt-br',
  'humanizacao-algoritmos',
  'camadas-profundas',
  'humanizacao-discursiva',
  'estrutura-macro',
];
```

- [ ] **Step 3: Teste de conteúdo**

Adicionar a `server/test/content.test.js` (seguir o estilo do arquivo; ajustar nomes de import se necessário):

```javascript
test('estrutura-macro: parseia seções e checklist', () => {
  const s2 = getSection('estrutura-macro', 2);
  assert.ok(s2.includes('Simetria de seções'));
  const chk = getSection('estrutura-macro', 8);
  assert.ok(chk.includes('[ ]'));
});
```

- [ ] **Step 4: Rodar**

Run: `cd server && node --test 'test/*.test.js' 2>&1 | grep -E "estrutura-macro|fail"`
Expected: passa; `validateAll()` no startup sem avisos novos.

- [ ] **Step 5: Commit**

```bash
git add references/estrutura-macro.md server/content/loader.js server/test/content.test.js
git commit -m "feat(estrutura): reference estrutura-macro.md + registro no loader"
```

---

## Task 8: tool `texto_br_estrutura` + registro no servidor

**Files:**
- Create: `server/tools/estrutura.js`
- Modify: `server/server.js`

- [ ] **Step 1: Criar `server/tools/estrutura.js`**

```javascript
import { z } from 'zod';
import { runPython } from './run-python.js';
import { TIPOS_VALIDOS } from '../knowledge/phases.js';

export function register(server, session) {
  server.registerTool(
    'texto_br_estrutura',
    {
      title: 'Análise macroestrutural (naturalidade estrutural)',
      description:
        'Mede sinais macroestruturais de IA num rascunho: simetria de seções, inflação de ' +
        'subtópicos, parágrafo-lição (kicker uniforme), frases de efeito em sequência e ' +
        'progressão sinalizada. Compõe um score 0-100 de naturalidade estrutural (alvo >= 70) ' +
        'e devolve um plano de perturbação priorizado. Use na Fase 5: medir → perturbar a ' +
        'estrutura conforme o plano → medir de novo, até "ALVO ATINGIDO". O tipo calibra a ' +
        'análise e o gate (default: tipo da sessão).',
      inputSchema: {
        texto: z.string().min(1).describe('Rascunho completo a analisar (markdown ou texto puro)'),
        tipo: z.enum(TIPOS_VALIDOS).optional().describe('Tipo de texto; default = tipo da sessão'),
      },
    },
    async ({ texto, tipo }) => {
      try {
        const tipoEfetivo = tipo ?? session?.tipo ?? 'geral';
        const resultado = await runPython('estrutura.py', JSON.stringify({ texto, tipo: tipoEfetivo }));
        if (session && !resultado.erro) {
          session.estruturaAtingida = resultado.atingiu_alvo === true;
          session.persist();
        }
        return { content: [{ type: 'text', text: resultado.relatorio }] };
      } catch (err) {
        return { isError: true, content: [{ type: 'text', text: err.message }] };
      }
    }
  );
}
```

- [ ] **Step 2: Registrar em `server.js`**

Adicionar o import (junto aos outros, após `registerLexico`):
```javascript
import { register as registerEstrutura } from './tools/estrutura.js';
```
E a chamada (após `registerScore(server, session);` ou junto às análises):
```javascript
  registerEstrutura(server, session);
```

- [ ] **Step 3: Smoke test do tool via análise existente**

Run: `cd server && node --test 'test/*.test.js' 2>&1 | grep -E "fail|tests "`
Expected: suíte segue verde (o tool é fino; estrutura.py já testado).

- [ ] **Step 4: Commit**

```bash
git add server/tools/estrutura.js server/server.js
git commit -m "feat(estrutura): tool texto_br_estrutura registrada no servidor"
```

---

## Task 9: Renumeração de fase (entrega 5 → 6) e gate da Fase 5

**Files:**
- Modify: `server/knowledge/phases.js`
- Modify: `server/session/state.js`
- Modify: `server/tools/proxima-fase.js`
- Modify: `server/tools/checklist.js`

- [ ] **Step 1: `phases.js` — guidance, sections, checklist, constantes**

(a) No comentário/header e onde menciona "5 entrega", trocar para refletir 6 fases de trabalho + entrega na 6.

(b) Em `PHASE_GUIDANCE`, **renomear a chave `5` (entrega) para `6`** e inserir a nova `5`:

```javascript
  5: {
    name: 'Análise macroestrutural',
    instruction: `Antes da entrega, desencaixe a macroestrutura. Texto de IA tende a uma arquitetura simétrica demais (seções gêmeas, títulos paralelos, parágrafos que sempre fecham numa "lição", bordões em sequência, subtópicos demais, progressão linear com signposts).

1. Chame texto_br_estrutura com o rascunho atual (ele usa o tipo da sessão para calibrar e medir).
2. Aplique o plano de perturbação que ele devolver, corrigindo os detectores mais fracos primeiro. NUNCA degrade a clareza: a assimetria serve ao texto, não o contrário.
3. Meça de novo. Repita até "ALVO ATINGIDO" (score >= 70) ou, no máximo, 3 iterações.

Critério de saída: checklist de texto_br_checklist(5) verificado. Em tipos longos (blog, capitulo, tecnico, explicativo, podcast, video) o gate exige o alvo atingido para avançar; nos demais é advisory. Depois chame texto_br_proxima_fase passando a versão atual em "rascunho".`,
  },
  6: {
    name: 'Entrega',
    instruction: `Entregue APENAS o texto final em Markdown limpo:

- Sem preâmbulos ("Aqui está...", "Segue abaixo...").
- Sem comentários após o texto.
- Sem auto-elogios sobre o processo nem anúncios de fases.
- Apenas o texto.

Se o usuário pedir explicitamente, mostre também o rascunho da Fase 1 para comparação. Em qualquer outro caso, mostrar o rascunho é violação do workflow.`,
  },
```

(c) Em `PHASE_SECTIONS`: trocar `5: []` por:
```javascript
  5: [
    { file: 'estrutura-macro', section: '1' },
    { file: 'estrutura-macro', section: '2' },
    { file: 'estrutura-macro', section: '3' },
    { file: 'estrutura-macro', section: '4' },
    { file: 'estrutura-macro', section: '5' },
    { file: 'estrutura-macro', section: '6' },
    { file: 'estrutura-macro', section: '7' }, // matriz de calibração
    // checklist (seção 8) só via texto_br_checklist(5)
  ],
  6: [],
```

(d) Em `PHASE_SECTIONS_CONVERSACIONAL`, adicionar payload enxuto:
```javascript
  5: [
    { file: 'estrutura-macro', section: '4' }, // kicker
    { file: 'estrutura-macro', section: '7' }, // matriz de calibração
  ],
```

(e) Em `CHECKLISTS`, adicionar:
```javascript
  5: { file: 'estrutura-macro', section: '8' },
```

(f) Adicionar a constante de gate (perto de `TIPOS_CONVERSACIONAIS`):
```javascript
// Tipos longos onde a Fase 5 (macroestrutura) bloqueia a entrega até o alvo.
// Fonte de verdade replicada em analysis/estrutura.py (TIPOS_GATE).
export const TIPOS_ESTRUTURA_GATE = ['blog', 'capitulo', 'tecnico', 'explicativo', 'podcast', 'video'];
```

- [ ] **Step 2: `state.js` — campo e limites de fase 6**

- Adicionar `'estruturaAtingida'` ao array `CAMPOS`.
- Adicionar `estruturaAtingida: null,` aos defaults do objeto.
- Em `start()`, adicionar `this.estruturaAtingida = null;`.
- Em `advance()`: trocar `if (this.currentPhase >= 5)` por `>= 6` e a mensagem `'Fase 5 (entrega)'` por `'Fase 6 (entrega)'`.
- Em `goTo()`: trocar `fase > 5` por `fase > 6` e a mensagem `'use um inteiro de 1 a 5'` por `'1 a 6'`.

- [ ] **Step 3: `proxima-fase.js` — schema, gate da Fase 5, nota → Fase 6**

- Import: adicionar `TIPOS_ESTRUTURA_GATE` à lista importada de `phases.js`.
- Schema `fase`: `.max(5)` → `.max(6)`.
- Depois do bloco do gate da Fase 2 (ainda dentro do `else` que chama `advance()`), adicionar o gate da Fase 5:

```javascript
          if (
            session.currentPhase === 5 &&
            TIPOS_ESTRUTURA_GATE.includes(session.tipo) &&
            !forcar &&
            session.estruturaAtingida !== true
          ) {
            return {
              isError: true,
              content: [
                {
                  type: 'text',
                  text:
                    'Gate da Fase 5: a naturalidade estrutural ainda não atingiu o alvo ' +
                    `(score < 70 para o tipo "${session.tipo}"). Rode texto_br_estrutura com o ` +
                    'rascunho atual, aplique o plano de perturbação até "ALVO ATINGIDO" e tente ' +
                    'avançar de novo. Para avançar mesmo assim (a pedido do usuário), use forcar: true.',
                },
              ],
            };
          }
```

- Trocar a nota de rascunhos de `if (phase === 5)` para `if (phase === 6)`.
- Atualizar a `description` do tool: sequência agora `... → 5 (análise macroestrutural) → 6 (entrega)`, e mencionar o gate da Fase 5.

- [ ] **Step 4: `checklist.js` — aceitar fase 5**

- Schema: `z.union([z.literal(2), z.literal(3), z.literal(4)])` → incluir `z.literal(5)`.
- Descrição: "fase 2 ... fase 4 ... fase 5 (naturalidade estrutural)".

- [ ] **Step 5: Rodar a suíte**

Run: `cd server && node --test 'test/*.test.js' 2>&1 | grep -E "fail|tests "`
Expected: ainda verde (os testes e2e da Task 10 cobrem a renumeração; aqui garante que nada quebrou).

- [ ] **Step 6: Commit**

```bash
git add server/knowledge/phases.js server/session/state.js server/tools/proxima-fase.js server/tools/checklist.js
git commit -m "feat(estrutura): Fase 5 macroestrutural no pipeline; entrega vira Fase 6 + gate adaptativo"
```

---

## Task 10: e2e — transição 4 → 5 → 6 e gates

**Files:**
- Modify: `server/test/e2e.test.js`

- [ ] **Step 1: Ler o estilo atual do e2e**

Run: `sed -n '1,40p' server/test/e2e.test.js`
Expected: ver como a sessão e os tools são exercitados (instanciação de `SessionState`/server, chamadas de tool).

- [ ] **Step 2: Escrever testes e2e**

Adicionar testes que (seguindo o padrão do arquivo):
- Iniciam sessão `tipo: 'blog'`, avançam até `currentPhase === 5`, e verificam que `proxima_fase` (sem `forcar`, com `estruturaAtingida` falso/nulo) **bloqueia** com mensagem contendo "Gate da Fase 5".
- Com `estruturaAtingida = true`, `proxima_fase` avança para `6`.
- `forcar: true` na Fase 5 avança mesmo com `estruturaAtingida` falso.
- `tipo: 'chat'` (advisory): `proxima_fase` na Fase 5 avança para `6` mesmo sem alvo.
- `texto_br_checklist(5)` retorna o checklist (contém "[ ]").

Modelo (ajustar à API real de invocação de tools do arquivo):
```javascript
test('e2e: gate da Fase 5 bloqueia blog sem alvo e avança com alvo', async () => {
  SessionState.start('tema teste', 'blog', 'medio', false);
  SessionState.goTo(5);
  SessionState.estruturaAtingida = false;
  const bloqueado = await chamarProximaFase({});            // helper do arquivo
  assert.ok(bloqueado.isError);
  assert.ok(bloqueado.content[0].text.includes('Gate da Fase 5'));
  SessionState.estruturaAtingida = true;
  const ok = await chamarProximaFase({ rascunho: 'x' });
  assert.ok(!ok.isError);
  assert.equal(SessionState.currentPhase, 6);
});
```

- [ ] **Step 3: Rodar a suíte completa**

Run: `cd server && npm test`
Expected: todos os testes passam (análise + conteúdo + e2e).

- [ ] **Step 4: Commit**

```bash
git add server/test/e2e.test.js
git commit -m "test(estrutura): e2e da transição de fase 5→6 e gates adaptativos"
```

---

## Task 11: Documentação (INSTRUCTIONS, README, SKILL)

**Files:**
- Modify: `server/server.js` (string `INSTRUCTIONS`)
- Modify: `server/README.md`
- Modify: `SKILL.md`
- Modify: `server/package.json` (descrição)

- [ ] **Step 1: Atualizar `INSTRUCTIONS` em `server.js`**

- Trocar "pipeline de 6 fases (0 ... 5 entrega)" por "pipeline de 7 fases (0 coleta de contexto, 1 redação, 2 humanização de superfície, 3 profunda, 4 discursiva, 5 análise macroestrutural, 6 entrega)".
- No passo 2, acrescentar a Fase 5 (análise macroestrutural) e seu gate adaptativo; trocar "Na Fase 5, entregue..." por "Na Fase 6, entregue...".
- Acrescentar `texto_br_estrutura(texto)` à lista de tools de consulta; trocar "checklist(fase) ... fases 2, 3 e 4" por "2, 3, 4 e 5".

- [ ] **Step 2: Atualizar `server/README.md` e `SKILL.md`**

Refletir as 7 fases e a nova etapa/tool nas descrições do pipeline (procurar por "6 fases" e "5 entrega" / "Fase 5" e ajustar).

Run para localizar ocorrências:
```bash
grep -rn "6 fases\|5 entrega\|Fase 5\|fases 2, 3 e 4" server/README.md SKILL.md server/package.json
```

- [ ] **Step 3: Atualizar a descrição em `package.json`**

Trocar `"... pipeline de 6 fases"` por `"... pipeline de 7 fases"`.

- [ ] **Step 4: Verificação final**

Run: `cd server && npm test`
Expected: tudo verde.

Run: `cd server && node -e "import('./server.js').then(m => { const s = m.createServer(require('./session/state.js')); })" 2>&1 | head -3` (ou simplesmente iniciar o servidor) para garantir que `INSTRUCTIONS` e imports não quebraram.
Expected: sem erro de sintaxe/import.

- [ ] **Step 5: Commit**

```bash
git add server/server.js server/README.md SKILL.md server/package.json
git commit -m "docs(estrutura): pipeline de 7 fases e tool texto_br_estrutura na documentação"
```

---

## Self-Review (preenchido)

**Spec coverage:**
- §4.1 parsing → Task 1 (`parsear_blocos`) + Task 2 (`montar_outline`).
- §4.2 detectores 1-5 → Tasks 2-6.
- §4.3 score composto + calibração → Task 2 (`calcular`) + `CALIBRACAO`/`TIPOS_GATE` (Task 2/9).
- §4.4 relatório + plano de perturbação → Task 2 (`formatar_relatorio`).
- §4.5 degradação graciosa → Task 2 (erro < 4 parágrafos; detectores `aplicavel=False`).
- §5 tool → Task 8.
- §6 renumeração e arquivos → Tasks 7-9, 11.
- §7 testes → Tasks 2-7, 10.

**Placeholder scan:** sem TBD/TODO; código completo nos steps de código; fixtures e asserts concretos.

**Type consistency:** contrato de detector único (topo do plano), `id`s batem entre detector e teste (`simetria_secoes`, `inflacao_subtopicos`, `kicker_uniforme`, `frases_efeito`, `progressao_sinalizada`); `session.estruturaAtingida`, `TIPOS_ESTRUTURA_GATE`/`TIPOS_GATE`, `texto_br_estrutura` consistentes entre Python, tool, state e proxima-fase.

**Notas de execução:** os limiares de `interp` nos detectores são iniciais e ajustáveis — se as fixtures `ESTR_IA`/`ESTR_HUMANO` não separarem na primeira rodada, calibrar os limiares (não os testes) até `ESTR_IA < 70 <= ESTR_HUMANO`.
