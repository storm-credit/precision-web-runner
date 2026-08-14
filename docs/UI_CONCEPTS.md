# UI Concepts

Four concepts were considered for the same responsive web/mobile product.

## Concept 01 — Dark execution console

Characteristics:
- dark background
- red action emphasis
- execution-first feel
- dense status information

Strength:
- strong live-run focus

Weakness:
- feels T1-specific / gaming-specific if over-branded
- less neutral for a general-purpose runner

## Concept 02 — Light dashboard **SELECTED**

Characteristics:
- white/light cards
- green status/action accents
- neutral product branding
- desktop left navigation
- mobile bottom navigation
- task status and execution flow visible together

Why selected:
- easiest to generalize beyond T1
- clear on desktop and mobile
- makes status, target time, and CTA readable
- suitable for future task/recipe management

### Desktop first screen

Must include:
- runner connection state
- current/reference time
- target task/URL summary
- target time
- state
- Test / ARM / Cancel CTA
- compact step list

### Mobile first screen

Priority order:
1. runner/device connected?
2. target/task
3. target time
4. state
5. primary CTA
6. compact progress

Detailed logs and recipe editing may scroll below.

## Concept 03 — Neon workflow builder

Characteristics:
- visually strong node/step workflow
- suited to advanced recipe editing

Strength:
- good future expert mode

Weakness:
- too complex for POC primary screen
- risks making workflow editing look more important than reliable execution

Decision:
- defer ideas to MVP recipe editor, not POC dashboard

## Concept 04 — Mobile-first minimal

Characteristics:
- minimal cards
- highly compact
- quick status/arm controls

Strength:
- excellent phone ergonomics

Weakness:
- not enough space for detailed troubleshooting and execution telemetry

Decision:
- use its compact principles inside Concept 02 mobile layout

## General branding rule

Do not brand the product as a T1 buyer.

Use neutral product language:
- Task
- Target
- Recipe
- Runner
- Schedule
- Test Run
- ARM
- Run Log

T1 appears only as the selected task/adapter.
