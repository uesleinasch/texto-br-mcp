// Fatia markdown por headings. Linhas dentro de cercas de código (```) são
// ignoradas na detecção de headings — as references usam templates com `#`
// dentro de blocos de código, que não podem encerrar uma seção.

function* headingLines(lines) {
  let openFence = null; // null = fora de cerca; senão, o delimitador que abriu
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const fence = line.match(/^\s*(`{3,}|~{3,})/);
    if (fence) {
      if (openFence === null) {
        openFence = fence[1];
      } else if (
        fence[1][0] === openFence[0] &&
        fence[1].length >= openFence.length
      ) {
        // só fecha com o mesmo caractere e comprimento >= o de abertura
        // (cercas de 4 backticks podem conter cercas de 3 sem encerrar)
        openFence = null;
      }
      continue;
    }
    if (openFence !== null) continue;
    const m = line.match(/^(#{1,3})\s+(.*)$/);
    if (m) yield { index: i, level: m[1].length, text: m[2].trim() };
  }
}

// Retorna Map<string, string> de seções numeradas (`## N. Título`) → corpo
// completo da seção (do heading até o próximo heading de nível <= 2).
export function parseNumberedSections(rawMarkdown) {
  const lines = rawMarkdown.split('\n');
  const headings = [...headingLines(lines)];
  const sections = new Map();

  for (let h = 0; h < headings.length; h++) {
    const { index, level, text } = headings[h];
    if (level !== 2) continue;
    const num = text.match(/^(\d+)\./);
    if (!num) continue;

    let end = lines.length;
    for (let j = h + 1; j < headings.length; j++) {
      if (headings[j].level <= 2) {
        end = headings[j].index;
        break;
      }
    }
    sections.set(num[1], lines.slice(index, end).join('\n').trim());
  }
  return sections;
}

// Extrai um bloco iniciado por heading nível 1 com texto exato
// (ex.: "Apêndice: Decisão rápida de tipo") até o próximo heading nível 1.
export function extractH1Block(rawMarkdown, headingText) {
  const lines = rawMarkdown.split('\n');
  const headings = [...headingLines(lines)];

  const start = headings.find((h) => h.level === 1 && h.text === headingText);
  if (!start) return null;

  let end = lines.length;
  for (const h of headings) {
    if (h.index > start.index && h.level === 1) {
      end = h.index;
      break;
    }
  }
  return lines.slice(start.index, end).join('\n').trim();
}

// Extrai um bloco iniciado por heading nível 2 com texto exato
// (ex.: "Princípios gerais aplicáveis a todos os tipos") até o próximo
// heading de nível <= 2 (não inclui esse próximo heading).
export function extractH2Block(rawMarkdown, headingText) {
  const lines = rawMarkdown.split('\n');
  const headings = [...headingLines(lines)];

  const start = headings.find((h) => h.level === 2 && h.text === headingText);
  if (!start) return null;

  let end = lines.length;
  for (const h of headings) {
    if (h.index > start.index && h.level <= 2) {
      end = h.index;
      break;
    }
  }
  return lines.slice(start.index, end).join('\n').trim();
}
