# GroundStack Design System

## Principles

GroundStack should feel like a technical knowledge workspace: precise, source-aware,
quiet, and trustworthy. The UI uses editorial spacing, readable typography, thin
separators, flat surfaces, and restrained emphasis. It avoids presenting unfinished AI
capabilities as if they were connected.

## Color Tokens

- Canvas: `#f6f1e8`, a warm off-white base.
- Surface: `#fffaf1`, used for controls, sidebar, and upload boundaries.
- Muted surface: `#eee7da`, used for hover and selected navigation states.
- Primary text: `#191713`, near-black ink.
- Secondary text: `#5f5a52`, medium graphite.
- Borders: `#d8cfc0` and `#bfb4a3`, soft neutral dividers.
- Accent: `#486b55`, muted forest green for primary actions, selected state, links, and focus.
- Danger: `#9a443d`, muted red for failures.
- Warning: `#8a6424`, muted ochre for pending work.
- Success: `#486b55`, the same restrained green used only with text labels.

## Typography

Use IBM Plex Sans where available, with system sans-serif fallbacks. Technical metadata,
hashes, IDs, and code-like labels use IBM Plex Mono or a system monospace fallback.

The type scale is compact: page titles are modest, section headings are clear, and body
copy is readable without becoming marketing copy. Uppercase labels are avoided unless
they represent genuine system metadata.

## Spacing And Shape

Spacing follows a 4px rhythm through Tailwind spacing and shared CSS classes. Corner
radii are restrained at 4px or 6px. Controls are rectangular, not pill-shaped. Whitespace,
alignment, and borders are preferred over nested containers.

## Elevation

GroundStack uses flat surfaces. Shadows are reserved for temporary elevated UI such as
future dialogs, menus, or popovers. Persistent page layout does not use glow, ambient
lighting, or decorative shadows.

## Icons

Lucide icons use consistent 16px or 24px sizing. Icons support scanning but do not replace
clear text labels. The brand mark is a one-color stacked-document symbol and avoids
generic AI motifs.

## Status Presentation

State is communicated with text labels: `Connected`, `Processing`, `Failed`,
`Unavailable`, `Loading`, and related explicit words. Color never carries state alone.
Status dots are avoided unless they represent a genuinely live state and include text.

## Component Hierarchy

Shared classes cover buttons, fields, status labels, inline alerts, navigation items,
upload boundaries, page headers, and data tables. This is intentionally small; GroundStack
does not use a large abstract component framework.

## Accessibility Rules

- Maintain WCAG AA contrast.
- Preserve visible keyboard focus.
- Use semantic headings and form labels.
- Keep navigation keyboard-accessible.
- Announce ingestion progress and errors with live regions.
- Render retrieved evidence as flat rows with numbered citations, source metadata,
  and expandable inspection controls.
- Keep touch targets at least 40px where practical.
- Respect `prefers-reduced-motion`.
- Keep long technical strings truncating or wrapping safely.

## Anti-Patterns Avoided

- No neon palette.
- No decorative glow.
- No emojis as icons.
- No purple or multicolor gradients.
- No nested cards.
- No multicolored navigation.
- No meaningless status dots.
- No fabricated data.
