# Business Documentation: [Feature]

> **Status:** Draft / Active
> **Target Audience:** Product, QA, Business

## 1. Executive Summary
*   **User Value:** [What problem does this solve for the user?]
*   **Business Goal:** [How does this help the company?]

---

## 2. Business Logic (The "Laws")

### 2.1 Core Rules
1.  **Rule:** [e.g. User must be 18+]
2.  **Rule:** [e.g. Order total > $50 for free shipping]

### 2.2 Edge Cases
*   [What happens if user loses internet?]
*   [What happens if payment fails?]

---

## 3. Scenarios (Given / When / Then)

### 3.1 Scenario: Happy Path
*   **Given:** User is logged in.
*   **When:** User clicks "Buy".
*   **Then:** Order is placed and email sent.

### 3.2 Scenario: Failure Path
*   **Given:** User has insufficient funds.
*   **When:** User clicks "Buy".
*   **Then:** Show error "X".

---

## 4. UI/UX Requirements
*   **Design Link:** [Figma]
*   **Tone of Voice:** Friendly / Professional.

---

## 5. Analytics & Metrics
*   **KPI:** Conversion Rate.
*   **Event to Track:** `button_click`, `purchase_success`.
