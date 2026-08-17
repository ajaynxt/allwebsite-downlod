# Design System

## Principles

Task clarity, truthful quality language, deliberate hierarchy, low visual noise, and accessible interaction states.

## Tokens

- Surfaces: paper `#f4f0e8`, paper-deep `#e8e1d5`, ink `#121719`, white `#fffdf8`
- Actions: coral `#ff6542`, coral-dark `#d73f22`, cobalt `#3458d4`
- Semantic: success `#176a4a`, danger `#a52e22`, muted `#626968`
- Spacing uses an approximately 4/8-based rhythm with section spacing from 58–120px
- Radius: 8px controls, 16px panels, 28px large surfaces; pills only for compact tags/actions
- Type: system sans for UI, Georgia for editorial display; no remote font dependency
- Motion: 160ms functional transitions; reduced-motion preference removes nonessential animation

## Components and states

- URL form: label, URL field, help, error, idle/loading submit
- Output tabs: Video/Audio with selected state and keyboard-native buttons
- Format option: label, detail, estimate, default/hover/focus/selected states
- Permission control: native checkbox plus actionable validation
- Job status: message, percentage, native progress, ready link or failed message
- FAQ: native details/summary disclosure

## Responsive rules

- Desktop hero uses a primary content column and a small quality note, not a competing visual
- Tablet stacks results and job content
- Mobile turns the URL field action into a full-width second row and all quality choices into one column
- No critical interaction relies on hover

## Governance

Use semantic CSS variables rather than one-off colors. New components must include focus, disabled/loading, error/success, narrow-screen, and reduced-motion behavior.
