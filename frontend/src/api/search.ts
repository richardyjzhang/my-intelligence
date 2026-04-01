import request from '@/utils/request'

export interface DocumentSearchResult {
  documentId: number
  title: string
  tags: string[]
  fileName: string
  score: number
  titleHighlight?: string
  contentHighlights?: string[]
}

export interface FragmentSearchResult {
  fragmentId: number
  title: string
  content: string
  tags: string[]
  titleHighlight?: string
  contentHighlight?: string
}

export interface SearchResult {
  documents: DocumentSearchResult[]
  fragments: FragmentSearchResult[]
}

interface Result<T> {
  code: number
  message: string
  data: T
}

export function search(keyword: string, tagIds?: number[]): Promise<Result<SearchResult>> {
  const params: Record<string, any> = { keyword }
  if (tagIds && tagIds.length > 0) params.tagIds = tagIds.join(',')
  return request.get('/search', { params })
}
