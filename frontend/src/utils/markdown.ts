import DOMPurify from 'dompurify'
import { marked } from 'marked'

marked.setOptions({
  gfm: true,
  breaks: true,
})

export function renderMarkdown(src: string): string {
  const t = src.trim()
  if (!t) return ''
  try {
    const raw = marked.parse(src, { async: false }) as string
    return DOMPurify.sanitize(raw, {
      ADD_ATTR: ['target', 'rel', 'class', 'checked', 'disabled', 'type'],
      ADD_TAGS: ['input'],
    })
  } catch {
    return DOMPurify.sanitize(`<p>${escapeHtml(src)}</p>`)
  }
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}
