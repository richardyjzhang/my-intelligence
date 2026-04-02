import { TOKEN_KEY } from '@/utils/request'

export type ChatMode = 'auto' | 'casual' | 'doc_search' | 'knowledge_qa'

export type ChatIntent = 'casual' | 'doc_search' | 'knowledge_qa'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatStreamCallbacks {
  onMeta?: (data: { requestId: string; model: string; intent?: ChatIntent }) => void
  onReasoningDelta?: (content: string) => void
  onAnswerDelta?: (content: string) => void
  onDone?: (data: {
    sources?: { title: string; documentId: number; fileName?: string }[]
  }) => void
  onError?: (message: string) => void
}

export function chatStream(
  query: string,
  history: ChatMessage[],
  callbacks: ChatStreamCallbacks,
  options?: { mode?: ChatMode },
): AbortController {
  const controller = new AbortController()
  const token = localStorage.getItem(TOKEN_KEY) || ''

  const body: Record<string, unknown> = { query, history }
  if (options?.mode && options.mode !== 'auto') {
    body.mode = options.mode
  }

  fetch('/api/qa/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: token,
    },
    body: JSON.stringify(body),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        callbacks.onError?.(`HTTP ${response.status}`)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        callbacks.onError?.('无法读取响应流')
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          const lines = part.split('\n')
          let eventName = ''
          let data = ''

          for (const line of lines) {
            if (line.startsWith('event:')) eventName = line.slice(6).trim()
            else if (line.startsWith('data:')) data = line.slice(5).trim()
          }

          if (!eventName || !data) continue

          try {
            const parsed = JSON.parse(data)
            switch (eventName) {
              case 'meta':
                callbacks.onMeta?.(parsed)
                break
              case 'reasoning_delta':
                callbacks.onReasoningDelta?.(parsed.content)
                break
              case 'answer_delta':
                callbacks.onAnswerDelta?.(parsed.content)
                break
              case 'done':
                callbacks.onDone?.(parsed)
                break
              case 'error':
                callbacks.onError?.(parsed.message)
                break
            }
          } catch {
            // skip invalid JSON
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        callbacks.onError?.(err.message || '请求失败')
      }
    })

  return controller
}
