---
name: design-taste-frontend
description: Minimalist Product UI Design Skill tailored for enterprise SaaS dashboards (ViziCheck). Enforces clean layout hierarchy, strict 1px solid borders, muted enterprise color systems, high information density, and anti-slop frontend standards.
---

# Minimalist Product UI Design Skill (ViziCheck Enterprise Edition)

## Design System & Tokens (Approved Source of Truth)

This skill enforces the official ViziCheck enterprise design system. Do NOT deviate or introduce unapproved styles.

### 1. Color Palette
- **Primary:** `#2563EB` (Enterprise Blue — actions, active navigation, focus rings)
- **Secondary / Shell:** `#0F172A` (Deep Slate — persistent enterprise sidebar, dark top navigation)
- **Neutral / Text:**
  - Headings / Dark Text: `#0F172A`
  - Body Text: `#334155` (Slate-700)
  - Muted Text / Captions: `#64748B` (Slate-500)
- **Canvas & Surfaces:**
  - Background Canvas: `#F8FAFC` (Slate-50)
  - Card / Panel Surface: `#FFFFFF` (Pure White)
  - Sidebar Accent / Hover: `#1E293B` (Slate-800)
- **Borders & Dividers:**
  - Subtle 1px Border: `#E2E8F0` (Slate-200)
- **Semantic Statuses:**
  - Success: `#16A34A` (Green — Approved, Active, Checked-In)
  - Warning: `#F59E0B` (Amber — Pending Approval, Expiring Soon)
  - Danger: `#DC2626` (Red — Rejected, Blacklisted, Overstay, Cancelled)

### 2. Typography
- **Font Family:** `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Scale:**
  - Page Heading: `32px` (`text-3xl font-bold tracking-tight`)
  - Section Subheading: `24px` (`text-2xl font-semibold tracking-tight`)
  - Card / Modal Title: `18px` (`text-lg font-semibold`)
  - Standard Body: `14px` (`text-sm font-normal text-slate-700`)
  - Captions & Meta: `12px` (`text-xs font-medium text-slate-500`)

### 3. Style Dials
- `DESIGN_VARIANCE`: **Low** (stick strictly to approved enterprise tokens, avoid random decorative flair)
- `MOTION_INTENSITY`: **Minimal** (instant transitions, subtle 150ms opacity/color changes, no floating spring animations)
- `VISUAL_DENSITY`: **High** (compact enterprise tables, dense information cards, tight vertical rhythm)

---

## Component Guidelines (Minimalist Enterprise Standard)

### 1. Enterprise Sidebar
- Persistent `#0F172A` deep slate background.
- Clean ViziCheck Shield + Checkmark branding at the top.
- Navigation links using 14px font, `#94A3B8` default text with subtle hover background (`#1E293B`).
- Active link marked with `#2563EB` background or left indicator bar with bright white text (`#FFFFFF`).
- Role badge and tenant name clearly visible in header / footer area.

### 2. Main Workspace
- `#F8FAFC` background canvas.
- Page header with clear breadcrumbs, title, description, and primary action buttons.
- Content structured using white cards (`#FFFFFF`) with subtle 1px `#E2E8F0` solid borders.
- Radii: `rounded-lg` (8px) for cards, `rounded-md` (6px) for inputs/buttons. No exaggerated bubble corners.
- Shadows: Minimal `shadow-sm` or border-only. Avoid heavy blurred drop-shadows.

### 3. Data Tables
- Strict 1px border around the table container.
- Table headers in muted slate (`bg-slate-50 text-slate-600 font-semibold text-xs uppercase tracking-wider`).
- Alternating or clean hoverable rows (`hover:bg-slate-50/75`).
- Sticky filter bar with search input, status dropdowns, and date range filters.
- Pagination bar at the bottom with item counters ("Showing 1 to 10 of 142 results").

### 4. Status Badges
Status badges must be compact pills with high-contrast text and subtle background tint:
- **Approved / Checked-In:** `bg-green-50 text-green-700 border border-green-200`
- **Pending:** `bg-amber-50 text-amber-700 border border-amber-200`
- **Rejected / Blacklisted:** `bg-red-50 text-red-700 border border-red-200`
- **Cancelled / Inactive:** `bg-slate-100 text-slate-600 border border-slate-200`

### 5. Forms & Modals
- Clean floating overlay modals with backdrop blur (`bg-slate-900/50 backdrop-blur-xs`).
- Form controls with 1px `#E2E8F0` border, `focus:ring-2 focus:ring-blue-600 focus:border-transparent`.
- Explicit validation error labels in `#DC2626` text right below input fields.

