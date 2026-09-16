"use client";
import { useMemo } from "react";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

// Lightweight markdown parser — no external deps
function parseMarkdown(text: string): string {
  let html = text;

  // Escape HTML entities first
  html = html
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Code blocks (must come before inline code)
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    const langLabel = lang ? `<span class="md-code-lang">${lang}</span>` : "";
    return `<pre class="md-pre">${langLabel}<code class="md-code-block">${code.trim()}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="md-code-inline">$1</code>');

  // Bold + italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  html = html.replace(/_(.+?)_/g, '<em>$1</em>');

  // Strikethrough
  html = html.replace(/~~(.+?)~~/g, '<del>$1</del>');

  // Headings
  html = html.replace(/^### (.+)$/gm, '<h3 class="md-h3">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 class="md-h2">$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1 class="md-h1">$1</h1>');

  // Horizontal rule
  html = html.replace(/^---+$/gm, '<hr class="md-hr" />');

  // Blockquote
  html = html.replace(/^> (.+)$/gm, '<blockquote class="md-blockquote">$1</blockquote>');

  // Ordered list
  html = html.replace(/((?:^\d+\. .+\n?)+)/gm, (match) => {
    const items = match.trim().split('\n').map(line =>
      line.replace(/^\d+\. (.+)$/, '<li class="md-li">$1</li>')
    ).join('');
    return `<ol class="md-ol">${items}</ol>`;
  });

  // Unordered list
  html = html.replace(/((?:^[-*+] .+\n?)+)/gm, (match) => {
    const items = match.trim().split('\n').map(line =>
      line.replace(/^[-*+] (.+)$/, '<li class="md-li">$1</li>')
    ).join('');
    return `<ul class="md-ul">${items}</ul>`;
  });

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" class="md-link" target="_blank" rel="noopener noreferrer">$1</a>'
  );

  // Paragraphs — wrap lines not already wrapped in block elements
  const blockTags = /^<(h[123]|ul|ol|li|pre|blockquote|hr)/;
  const lines = html.split('\n');
  const processed: string[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.trim() === '') {
      processed.push('');
    } else if (blockTags.test(line.trim())) {
      processed.push(line);
    } else {
      processed.push(`<p class="md-p">${line}</p>`);
    }
    i++;
  }
  html = processed.join('\n');

  return html;
}

export function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  const html = useMemo(() => parseMarkdown(content), [content]);

  return (
    <>
      <style>{`
        .md-content { direction: auto; }
        .md-content .md-h1 { font-size: 1.15rem; font-weight: 700; margin: 0.75rem 0 0.4rem; color: var(--text-primary); line-height: 1.4; }
        .md-content .md-h2 { font-size: 1.05rem; font-weight: 600; margin: 0.65rem 0 0.35rem; color: var(--text-primary); line-height: 1.4; }
        .md-content .md-h3 { font-size: 0.95rem; font-weight: 600; margin: 0.55rem 0 0.3rem; color: var(--text-primary); }
        .md-content .md-p { margin: 0.3rem 0; line-height: 1.7; }
        .md-content .md-p:first-child { margin-top: 0; }
        .md-content .md-p:last-child { margin-bottom: 0; }
        .md-content .md-ul, .md-content .md-ol { margin: 0.4rem 0 0.4rem 1.2rem; padding: 0; }
        .md-content .md-li { margin: 0.2rem 0; line-height: 1.6; }
        .md-content .md-code-inline {
          font-family: 'Courier New', monospace;
          font-size: 0.82em;
          padding: 0.15em 0.4em;
          border-radius: 4px;
          background: rgba(124,111,205,0.15);
          color: #c4b5fd;
          word-break: break-word;
        }
        .md-content .md-pre {
          position: relative;
          margin: 0.6rem 0;
          border-radius: 10px;
          background: rgba(0,0,0,0.35);
          border: 1px solid rgba(255,255,255,0.08);
          overflow: auto;
        }
        .md-content .md-code-lang {
          display: block;
          font-size: 0.7rem;
          color: var(--text-muted);
          padding: 0.5rem 0.75rem 0;
          font-family: 'Courier New', monospace;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .md-content .md-code-block {
          display: block;
          font-family: 'Courier New', monospace;
          font-size: 0.82em;
          padding: 0.5rem 0.75rem 0.75rem;
          color: #e2e8f0;
          white-space: pre-wrap;
          word-break: break-word;
          line-height: 1.6;
        }
        .md-content .md-blockquote {
          border-right: 3px solid var(--accent);
          margin: 0.5rem 0;
          padding: 0.3rem 0.75rem;
          color: var(--text-secondary);
          font-style: italic;
          background: rgba(124,111,205,0.06);
          border-radius: 0 6px 6px 0;
        }
        .md-content .md-hr {
          border: none;
          border-top: 1px solid var(--border-mid);
          margin: 0.75rem 0;
        }
        .md-content .md-link {
          color: var(--accent);
          text-decoration: underline;
          text-underline-offset: 2px;
          word-break: break-all;
        }
        .md-content .md-link:hover { opacity: 0.8; }
        .md-content strong { font-weight: 700; }
        .md-content em { font-style: italic; }
        .md-content del { text-decoration: line-through; opacity: 0.7; }
      `}</style>
      <div
        className={`md-content ${className}`}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </>
  );
}
