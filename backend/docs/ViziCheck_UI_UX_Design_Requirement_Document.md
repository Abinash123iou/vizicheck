# ViziCheck UI/UX Design Requirement Document (UXDR) v1.0

## Project Overview

### Project Name

ViziCheck

### Project Type

Smart Visitor Management System

### Platform

-   Mobile Application (Primary)
-   Web Application (Secondary)

### Objective

Design a modern, enterprise-grade Visitor Management System that enables
visitor registration, approval workflows, QR-based visitor passes,
check-in/check-out tracking, notifications, and visitor analytics.

The final design should look like a production SaaS product rather than
a college project.

## Target Users

### Visitor

External person visiting the organization.

**Goals:** - Request a visit - Track request status - View visitor
pass - Show QR pass at entry

### Tenant

Employee or host being visited.

**Goals:** - Manage availability - Approve visitors - View upcoming
meetings

### Security Officer

**Goals:** - Verify QR code - Check-in visitors - Check-out visitors -
Monitor active visitors

### Super Admin

**Goals:** - Manage users - Manage tenants - Monitor visitors - Generate
reports - View audit logs

## Design Style

### Design Direction

Enterprise SaaS

**Keywords:** - Professional - Clean - Modern - Minimal - Secure -
Corporate - Scalable

**Reference Companies:** - Microsoft - Atlassian - Notion - Stripe -
Linear - Zoho

## Visual Reference

Use the provided ViziCheck mobile UI image as inspiration.

**Do NOT copy directly.**

Use it for: - Layout ideas - Color consistency - Mobile spacing - Card
design - Navigation structure

## Branding

### Logo

ViziCheck Shield + Checkmark

**Meaning:** - Security - Verification - Approval - Visitor Access

### Color System

  Token        Value
  ------------ -----------
  Primary      `#2563EB`
  Secondary    `#0F172A`
  Success      `#16A34A`
  Warning      `#F59E0B`
  Danger       `#DC2626`
  Background   `#F8FAFC`
  Cards        `#FFFFFF`
  Borders      `#E2E8F0`

## Typography

**Font Family:** Inter

  Text style     Size
  ------------ ------
  Heading        32px
  Subheading     24px
  Card Title     18px
  Body           14px
  Caption        12px

## Mobile Screens

### Authentication

1.  Splash Screen
2.  Login
3.  Register
4.  Forgot Password

### Visitor Module

5.  Visitor Dashboard
6.  Create Visit Request
7.  Request History
8.  Request Details

### Pass Module

9.  My Passes
10. Pass Details
11. QR Pass Screen

### Notifications

12. Notification List

### Profile

13. Profile
14. Edit Profile

## Navigation

### Bottom Navigation

1.  Home
2.  Requests
3.  Passes
4.  Notifications
5.  Profile

## Visitor Dashboard

**Components:** - Welcome Banner - Upcoming Visits - Pending Requests -
Active Passes

**Quick Actions:** - Create Request - View Pass - Request History -
Notifications

## Create Visit Request

**Fields:** - Tenant Selection - Visit Date - Start Time - End Time -
Purpose

**Actions:** - Submit Request - Cancel

## Request History

**Display:** - Request ID - Tenant Name - Date - Status

**Status Badges:** - Pending - Approved - Rejected - Cancelled -
Completed

## QR Pass Screen

**Display:** - Visitor Photo - Visitor Name - Pass Number - Tenant
Name - Department - Visit Date - Visit Time - QR Code - Status Badge

**Actions:** - Download Pass - Share Pass

## Notifications

**Display:** - Notification Title - Message - Time - Read/Unread State

## Profile

**Display:** - User Photo - Name - Email - Phone - Organization

**Actions:** - Edit Profile - Change Password - Logout

## Component Library

**Required Components:** - Buttons - Input Fields - Dropdowns - Date
Picker - Time Picker - Cards - Tables - Status Badges - QR Card -
Notification Card - Empty States - Loading States

## Deliverables

  Phase     Deliverable
  --------- -------------------------
  Phase 1   Design System
  Phase 2   Low Fidelity Wireframes
  Phase 3   High Fidelity Screens
  Phase 4   Interactive Prototype
  Phase 5   Developer Handoff

## Acceptance Criteria

The design will be approved only if:

-   All required screens are designed
-   Design system is complete
-   Mobile navigation is consistent
-   Components are reusable
-   Production-grade appearance
-   Enterprise SaaS quality
-   Matches ViziCheck branding
-   Ready for Flutter implementation

## Mobile UI Design References

The source document includes mobile UI design reference images in its
final section. Refer to the original PDF for those visual references.
