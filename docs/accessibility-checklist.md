# GroundStack Manual Accessibility Checklist

Use this checklist with the automated Playwright axe scan. Automated scans do not prove WCAG
conformance.

- Keyboard navigation: tab through landing, navigation drawer, chat composer, citation dialog,
  feedback controls, tables, and destructive confirmations.
- Screen reader behavior: verify page headings, navigation labels, async chat announcements, dialog
  title, and form validation messages.
- Focus management: skip link reaches main content, source dialog receives focus, Escape closes it,
  and focus returns to the citation button.
- Zoom: review at 200% browser zoom on desktop and mobile-width layout with no horizontal page
  scrolling.
- Contrast: verify text, focus rings, status labels, and disabled states against the neutral palette.
- Reduced motion: enable reduced motion and confirm no interaction depends on animation.
- Mobile: open and close the navigation drawer, submit chat, inspect citations, and confirm touch
  targets remain usable.
- Error states: test API unavailable, rate limited, insufficient evidence, model unavailable, and
  forbidden admin routes with request IDs visible when returned by the API.
