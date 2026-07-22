# GULA UI/UX Constitution

## Design Principles

### 1. Arabic First
RTL layout is the default, not an afterthought. Arabic typography, date formats, number formats, and cultural conventions are primary. English is secondary. All UI components support RTL natively.

### 2. Clinical Efficiency
Every additional click is a tax on clinical productivity. Interfaces minimize clicks for common tasks. Defaults are intelligent. Repetitive data entry is eliminated through smart defaults, auto-complete, and data reuse.

### 3. Progressive Disclosure
Show what is needed. Hide what is not. Complex functionality is accessible but not overwhelming. Novice users see simplified interfaces. Expert users can access advanced features through progressive disclosure.

### 4. Consistent Patterns
Same actions appear in consistent locations. Same terminology is used throughout. Same visual patterns indicate same behaviors. Users should never wonder "where is the save button?"

### 5. Accessibility (WCAG 2.1 AA minimum)
- Keyboard navigable
- Screen reader compatible
- Sufficient color contrast
- Focus indicators visible
- Error messages clear and actionable
- Touch targets minimum 44x44px

### 6. Responsive
Desktop, tablet, and mobile are supported. Critical workflows (result review, order entry, patient lookup) are fully functional on tablets for bedside and laboratory use.

### 7. Offline Resilience
The application degrades gracefully without connectivity. Critical workflows continue offline with synchronization when connectivity returns. Users are clearly informed of offline mode.

### 8. Performance Perception
Loading states, skeleton screens, and optimistic updates create the perception of speed. No operation blocks the UI for more than 200ms without feedback.

## Component Library

9. **Single component library** is used across the entire frontend. No duplicate components for the same purpose.

10. **Components are stateless** where possible. State management is centralized in the application layer.

11. **Form components** validate inline, provide clear error messages in Arabic and English, and support keyboard navigation.

## Navigation

12. **Dynamic menus** are driven by backend permissions. Menu items appear and disappear based on what the user is authorized to do.

13. **Breadcrumbs** show the current location in the application hierarchy.

14. **Global search** is accessible from any screen.

## Dashboards

15. **Dashboards are user-configurable** where appropriate. Widgets can be added, removed, rearranged, and configured to user preferences.

16. **Dashboard widgets** are backed by dedicated API endpoints that return structured data, not rendered HTML.

## Notifications

17. **Critical notifications** interrupt the current workflow with clear action paths. Non-critical notifications are collected in a notification center.

18. **Notification delivery** respects user presence: in-app for active users, push for mobile, email for time-sensitive, SMS for critical alerts.

## Backend Authority

19. The backend is the single source of truth for all business logic and data. The frontend displays and validates, but never independently enforces business rules. See Article 05.15 (Backend Authority).
