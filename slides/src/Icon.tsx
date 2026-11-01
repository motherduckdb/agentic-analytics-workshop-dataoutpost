import React from 'react'

// Line icons on a 64 x 64 grid. The first ten come from the Jev for analytics deck.
export type IconName =
  | 'write'
  | 'target'
  | 'filter'
  | 'check'
  | 'search'
  | 'bolt'
  | 'layers'
  | 'loop'
  | 'book'
  | 'chat'
  | 'box'
  | 'lock'
  | 'eye'

const paths: Record<IconName, React.ReactNode> = {
  write: (
    <>
      <path d="M13 47l4-15L43 6l15 15-26 26-19 4zM36 13l15 15M17 32l15 15" />
      <path d="M9 59h48" />
    </>
  ),
  target: (
    <>
      <circle cx="32" cy="32" r="25" />
      <circle cx="32" cy="32" r="13" />
      <circle cx="32" cy="32" r="3" />
    </>
  ),
  filter: <path d="M7 10h50L38 33v20l-12 5V33z" />,
  check: (
    <>
      <circle cx="32" cy="32" r="25" />
      <path d="M18 32l10 10 19-21" />
    </>
  ),
  search: (
    <>
      <circle cx="27" cy="27" r="18" />
      <path d="M40 40l17 17" />
    </>
  ),
  bolt: <path d="M36 5L12 36h17l-2 23 25-32H35z" />,
  layers: <path d="M5 20L32 6l27 14-27 14zM5 32l27 14 27-14M5 44l27 14 27-14" />,
  loop: (
    <>
      <path d="M52 26A21 21 0 1 0 53 40" />
      <path d="M54 10v16H38" />
    </>
  ),
  book: (
    <>
      <path d="M32 16c-6-5-15-6-24-4v40c9-2 18-1 24 4 6-5 15-6 24-4V12c-9-2-18-1-24 4z" />
      <path d="M32 16v40" />
    </>
  ),
  chat: <path d="M8 12h48v30H28L16 53V42H8z" />,
  box: (
    <>
      <rect x="9" y="13" width="46" height="38" rx="3" />
      <path d="M9 25h46M17 19h4M25 19h4" />
    </>
  ),
  lock: (
    <>
      <rect x="13" y="28" width="38" height="28" rx="3" />
      <path d="M21 28v-8a11 11 0 0 1 22 0v8M32 39v7" />
    </>
  ),
  eye: (
    <>
      <path d="M4 32s10-17 28-17 28 17 28 17-10 17-28 17S4 32 4 32z" />
      <circle cx="32" cy="32" r="8" />
    </>
  )
}

export function Icon({ name }: { name: IconName }) {
  return (
    <svg
      className="concept-icon"
      viewBox="0 0 64 64"
      fill="none"
      stroke="currentColor"
      strokeWidth="3"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  )
}
