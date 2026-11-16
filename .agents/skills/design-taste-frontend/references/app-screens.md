# ViziCheck App Screen Reference Standards

## 1. Role-Specific Dashboards

### Super Admin Dashboard
- **Top Row (Metrics):**
  - Total Active Tenants (with trend badge)
  - Total Registered Visitors (all-time)
  - Today's Visits Across Facilities
  - Active Security Alerts / Overstay Warnings
- **Main Area:**
  - Tenant Activity Breakdown (Cards / Table)
  - System Health & Recent Audit Trail Feed
  - Quick actions: "Add New Tenant", "Manage Platform Users", "Export Audit Report"

### Tenant Admin Dashboard
- **Top Row (Metrics):**
  - Visits Scheduled Today
  - Pending Approvals Requiring Action
  - Available Host Employees
  - Total Completed Visits (This Month)
- **Main Area:**
  - Approval Queue Action List (One-click Approve/Reject with Reason)
  - Today's Expected Visitors Roster
  - Host Availability Status Overview

### Host Dashboard (`HOST_USER`)
- **Top Row (Metrics):**
  - My Visitors Today
  - My Pending Approvals
  - Upcoming Scheduled Visits
- **Main Area:**
  - Pending Visit Requests with quick decision modal
  - Calendar Slot View (Weekly recurring schedule & blackout exceptions)
  - Past Visit History

### Security Console (`SECURITY_OFFICER`)
- **Top Row (Metrics):**
  - Current Visitors Inside Building
  - Today's Total Check-Ins
  - Today's Total Check-Outs
  - Overstay Warnings (>8 Hours without checkout)
- **Main Area:**
  - Quick QR Code Entry/Exit Scanner input
  - Manual Fallback Check-In/Out Modal
  - Live Active Visitors Table with instant "Check Out" button
  - Gate Scan Activity Feed

### Receptionist Console (`RECEPTIONIST`)
- **Top Row (Metrics):**
  - Walk-In Visitors Registered Today
  - Passes Issued Today
  - Currently Waiting in Lobby
- **Main Area:**
  - "Register Walk-In Visitor" Quick Form
  - Visitor Lookup & Digital Badge Generator
  - Check-in Confirmation Modal with Printed Badge Preview

---

## 2. Shared Components Specification

### Metric Card (Bento Style)
```tsx
<div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs">
  <div className="flex items-center justify-between">
    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{label}</span>
    <div className="p-2 bg-blue-50 text-blue-600 rounded-md">{icon}</div>
  </div>
  <div className="mt-3 flex items-baseline gap-2">
    <span className="text-2xl font-bold text-slate-900">{value}</span>
    {trend && <span className="text-xs font-medium text-green-600">{trend}</span>}
  </div>
  {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
</div>
```

### Table Component Container
```tsx
<div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
  <div className="p-4 border-b border-slate-200 flex items-center justify-between gap-4">
    {/* Filter Toolbar: Search input, dropdown filters, export button */}
  </div>
  <div className="overflow-x-auto">
    <table className="w-full text-left border-collapse text-sm">
      <thead className="bg-slate-50 text-slate-600 text-xs font-semibold uppercase tracking-wider border-b border-slate-200">
        {/* Table Headers */}
      </thead>
      <tbody className="divide-y divide-slate-100 text-slate-700">
        {/* Table Rows */}
      </tbody>
    </table>
  </div>
  <div className="p-4 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
    {/* Pagination Controls */}
  </div>
</div>
```

