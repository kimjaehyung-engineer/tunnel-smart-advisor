---
version: "alpha"
name: "Tunnel Smart Advisor"
description: "Design system for an AI-powered tunnel construction risk intelligence and knowledge graph web application. Optimized for React + Vite + TypeScript implementation by coding agents."
colors:
  primary: "#0D1B2A"
  primary-2: "#10243A"
  primary-3: "#1B263B"
  surface: "#FFFFFF"
  surface-muted: "#F8FAFC"
  surface-subtle: "#F1F5F9"
  border: "#E2E8F0"
  border-strong: "#CBD5E1"
  text: "#0F172A"
  text-muted: "#64748B"
  text-soft: "#94A3B8"
  accent: "#2563EB"
  accent-hover: "#1D4ED8"
  risk-critical: "#EF4444"
  risk-high: "#F97316"
  risk-medium: "#F59E0B"
  risk-low: "#10B981"
  info: "#3B82F6"
  success: "#10B981"
  warning: "#F59E0B"
  danger: "#EF4444"
  graph-blue: "#60A5FA"
  graph-green: "#34D399"
  graph-violet: "#A78BFA"
  graph-orange: "#FB923C"
  graph-red: "#F87171"
typography:
  display:
    fontFamily: "Pretendard, Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "32px"
    fontWeight: 700
    lineHeight: "1.2"
    letterSpacing: "-0.03em"
  h1:
    fontFamily: "Pretendard, Inter, system-ui, sans-serif"
    fontSize: "28px"
    fontWeight: 700
    lineHeight: "1.25"
    letterSpacing: "-0.025em"
  h2:
    fontFamily: "Pretendard, Inter, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: "1.3"
    letterSpacing: "-0.02em"
  h3:
    fontFamily: "Pretendard, Inter, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 700
    lineHeight: "1.35"
  body:
    fontFamily: "Pretendard, Inter, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: "1.55"
  body-sm:
    fontFamily: "Pretendard, Inter, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: "1.5"
  label:
    fontFamily: "Pretendard, Inter, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: "1.3"
  metric:
    fontFamily: "Pretendard, Inter, system-ui, sans-serif"
    fontSize: "28px"
    fontWeight: 700
    lineHeight: "1"
rounded:
  sm: "6px"
  md: "10px"
  lg: "14px"
  xl: "18px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  "2xl": "32px"
  "3xl": "48px"
components:
  app-shell:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.text}"
  sidebar:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    width: "112px"
  sidebar-expanded:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    width: "252px"
  sidebar-active-item:
    backgroundColor: "#17365C"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: "10px 12px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
    padding: "20px"
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: "12px 18px"
  button-danger:
    backgroundColor: "{colors.risk-critical}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: "12px 18px"
  input:
    backgroundColor: "#FFFFFF"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "10px 12px"
  table-header:
    backgroundColor: "{colors.surface-subtle}"
    textColor: "{colors.text-muted}"
    rounded: "{rounded.sm}"
---

## Overview
Tunnel Smart Advisor is a professional engineering SaaS interface for tunnel construction risk analysis. The UI must look like a serious internal decision-support system, not a consumer landing page. The visual tone is clean, data-dense, calm, and trustworthy.

Use the first generated analysis workspace reference image as the core visual direction: left dark navy navigation, white workspace, card-based analytical panels, compact controls, risk cards, knowledge graph panels, and clear Korean enterprise UI labels.

Primary navigation pages:
1. 대시보드
2. 분석 워크스페이스
3. 지식 라이브러리
4. 과거 분석
5. 리포트
6. 알림

The generated page reference images should be used as layout targets:
- dashboard_page.png for 대시보드
- the first generated image for 분석 워크스페이스
- knowledge_library_page.png for 지식 라이브러리
- history_analysis_page.png for 과거 분석
- reports_page.png for 리포트
- notifications_page.png for 알림

## Colors
The base palette is navy, white, and slate. Use navy for product identity and navigation, white for content surfaces, slate for text hierarchy, and blue for neutral actions.

Risk colors must be semantically consistent:
- Critical / 최상위 위험: `risk-critical` red
- High / 높음: `risk-high` orange
- Medium / 보통: `risk-medium` amber
- Low / 낮음: `risk-low` green

Do not overuse red. Red is reserved for actual high-risk warnings, top-ranked risk cards, destructive actions, and critical badges. For standard primary actions, use blue.

## Typography
Use Pretendard first. Fall back to Inter and system sans-serif. Korean text must feel compact and legible in dense tables. Avoid decorative fonts.

Recommended hierarchy:
- Page title: h1
- Section/card title: h3
- Table body and form controls: body or body-sm
- KPI numbers: metric
- Badges, table headers, metadata: label

Keep letter spacing tight only on large headings. Do not use all-caps Korean labels.

## Layout
Use a fixed dark sidebar and a fluid main workspace.

Desktop layout:
- Sidebar: 112px collapsed or 252px expanded.
- Main content max width: none; use full viewport for engineering dashboards.
- Page padding: 24px.
- Card gap: 16px to 24px.
- Card radius: 14px.
- Main grid: 12-column grid.

Common layouts:
- 대시보드: KPI cards at top, trend/summary panels in the middle, recent analysis and alerts at bottom.
- 분석 워크스페이스: condition input area at top, semantic search below, then split analysis result + graph/risk panels.
- 지식 라이브러리: search/filter header, category sidebar, document table, tags and source metadata.
- 과거 분석: filter toolbar, sortable history table, action icons for view/download/re-run.
- 리포트: KPI summary, report search/filter, report table, generate-report action.
- 알림: tabbed notification list grouped by severity and read state.

Responsive behavior:
- At tablet widths, keep sidebar compact and reduce multi-column panels to two columns.
- At mobile widths, sidebar becomes a bottom or drawer navigation; cards stack vertically.

## Elevation & Depth
Use subtle shadows only. Engineering software should look precise and stable.

Card shadow:
`0 1px 2px rgba(15, 23, 42, 0.06), 0 1px 3px rgba(15, 23, 42, 0.08)`

Focused/selected analysis card shadow:
`0 8px 24px rgba(15, 23, 42, 0.10)`

Avoid glassmorphism, heavy blur, neon gradients, and decorative effects.

## Shapes
Use rounded rectangles consistently. Inputs, buttons, cards, badges, and table rows should share the same radius family.

- Input/button: 10px
- Card/container: 14px
- Large hero/graph panel: 18px
- Badge/chip: pill

Knowledge graph nodes can use circles or soft pills. Risk center nodes should be visually stronger than connected context nodes.

## Components

### Sidebar
The sidebar is the main product anchor. Use dark navy background, white icons/text, and a stronger blue active state. Navigation labels:
- 대시보드
- 분석 워크스페이스
- 지식 라이브러리
- 과거 분석
- 리포트
- 알림

Bottom utility items:
- 설정
- 도움말

### Header
Use compact page headers. Include title, short explanatory subtitle, and optional right-side controls such as project selector, user menu, export, or create button.

### Cards
Cards should be white with a light border. Each card needs a clear title, optional subtitle, and a focused content area. Avoid putting too many unrelated widgets in one card.

### Forms
Analysis inputs use labeled selects and text areas. The primary analysis action should be visually dominant. Use inline validation and concise helper text.

### Tables
Tables are critical. Use dense but readable rows, sticky header where useful, clear sort affordances, and right-aligned numeric risk scores. Include status badges, source counts, and action buttons.

### Risk Cards
Risk cards should show:
- Rank
- Severity badge
- Risk title
- Matched conditions
- Score
- Confidence/source count
- Tags
- Primary action: 상세 보기

Top risk card may use a red accent border. Lower risks should not all look critical.

### Knowledge Graph
Use graph panels to explain relationships among process, ground condition, location, method, equipment, risk, and mitigation. The central selected risk node should be largest. Related nodes should be grouped by category color.

### Alerts
Notifications should be scannable. Show category icon, title, short description, timestamp, severity/read state, and optional action. Critical alerts use red accents but not full red backgrounds.

## Do's and Don'ts

Do:
- Keep the UI sober, compact, and engineering-oriented.
- Prioritize information hierarchy over visual decoration.
- Use cards, tables, and graphs as the primary layout language.
- Use Korean labels naturally and consistently.
- Keep risk severity colors consistent across all screens.
- Make every page feel like part of one product.

Don't:
- Do not use oversized hero banners on internal screens.
- Do not use bright pink/magenta as the primary CTA.
- Do not make every risk item red.
- Do not use vague AI-themed decoration instead of useful analysis surfaces.
- Do not hide important engineering evidence behind decorative UI.
- Do not create inconsistent spacing, border radius, or typography per page.

## Agent Prompt Guide
When implementing or redesigning UI, follow this sequence:

1. First, create the shared app shell: fixed dark navy sidebar, main workspace, page header, card, button, input, badge, table, and KPI components.
2. Then implement each page using the corresponding reference image and the page layout rules in this file.
3. Preserve the current backend/API assumptions; this is a UI redesign unless explicitly asked otherwise.
4. Use mock data only where API data is not yet available, and isolate it in a clearly named mock data file.
5. Prefer reusable components over one-off CSS.
6. Use semantic HTML and accessible labels for all form controls.
7. Ensure all tables, cards, and graph panels remain readable at 1440px desktop width.
8. Validate that the six sidebar items route to six distinct pages.

Example implementation instruction:
"Redesign the Tunnel Smart Advisor frontend according to DESIGN.md. Use the attached page reference images as visual targets. Keep the analysis workspace based on the first generated reference image. Build reusable React components for AppShell, Sidebar, PageHeader, MetricCard, RiskCard, DataTable, FilterBar, KnowledgeGraphPanel, ReportTable, NotificationList, and Badge."
