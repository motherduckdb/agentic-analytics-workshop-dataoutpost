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
  // Hands-on slides (id starts with ho-): a time box, steps, an exit check, what to install.
  minutes?: number
  steps?: string[]
  doneWhen?: string
  needs?: string[]
  status?: string
}
