export type Slide = {
  id?: string
  title: string
  body?: string
  kind: 'title' | 'statement' | 'custom' | 'code'
  theme: 'sand' | 'ink' | 'duck'
  section?: string
  notes: string
  source?: string
  sourceLabel?: string
  code?: string
  codeLabel?: string
  language?: 'sql' | 'loop' | 'md'
}
