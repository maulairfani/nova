import { Fragment, ReactNode } from "react";

/** Inline markdown only (bold, italic, inline code) — no block structure. */
function renderInline(text: string): ReactNode {
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  const parts = text.split(pattern);

  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} style={{ background: "var(--nova-bg)", padding: "1px 5px", borderRadius: 4, fontSize: "0.9em" }}>
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

/** Minimal markdown: headings (#-####), bullet/numbered lists, paragraphs,
 * each rendering their inline content via renderInline — avoids pulling in
 * a full markdown library for a chat bubble's worth of formatting, but
 * still handles the block structure the KB documents (and Nova's answers
 * quoting them) actually use. */
export function renderInlineMarkdown(text: string): ReactNode {
  const lines = text.split("\n");
  const blocks: ReactNode[] = [];
  let list: { type: "ul" | "ol"; items: string[] } | null = null;

  const flushList = () => {
    if (!list) return;
    const items = list.items;
    blocks.push(
      list.type === "ul" ? (
        <ul key={blocks.length} style={{ margin: "4px 0 8px", paddingLeft: 22 }}>
          {items.map((item, i) => (
            <li key={i} style={{ marginBottom: 2 }}>
              {renderInline(item)}
            </li>
          ))}
        </ul>
      ) : (
        <ol key={blocks.length} style={{ margin: "4px 0 8px", paddingLeft: 22 }}>
          {items.map((item, i) => (
            <li key={i} style={{ marginBottom: 2 }}>
              {renderInline(item)}
            </li>
          ))}
        </ol>
      )
    );
    list = null;
  };

  for (const line of lines) {
    const headingMatch = /^(#{1,4})\s+(.*)$/.exec(line);
    const bulletMatch = /^[-*]\s+(.*)$/.exec(line);
    const numberedMatch = /^\d+\.\s+(.*)$/.exec(line);

    if (headingMatch) {
      flushList();
      const level = headingMatch[1].length;
      const fontSize = level <= 2 ? 17 : 15;
      blocks.push(
        <div key={blocks.length} style={{ font: `600 ${fontSize}px/1.4 var(--font-figtree),sans-serif`, margin: "10px 0 4px" }}>
          {renderInline(headingMatch[2])}
        </div>
      );
      continue;
    }
    if (bulletMatch) {
      if (!list || list.type !== "ul") {
        flushList();
        list = { type: "ul", items: [] };
      }
      list.items.push(bulletMatch[1]);
      continue;
    }
    if (numberedMatch) {
      if (!list || list.type !== "ol") {
        flushList();
        list = { type: "ol", items: [] };
      }
      list.items.push(numberedMatch[1]);
      continue;
    }
    flushList();
    if (line.trim() === "") {
      blocks.push(<div key={blocks.length} style={{ height: 8 }} />);
    } else {
      blocks.push(<div key={blocks.length}>{renderInline(line)}</div>);
    }
  }
  flushList();

  return blocks;
}
