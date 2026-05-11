# Billing Analyst Query Logic

## Overview

This file defines the reasoning paths the billing-analyst agent must follow when handling the five standard billing and usage queries. Each query maps to a specific data-fetch sequence, filter set, and output format. Follow these paths exactly — do not invent alternative approaches without noting the deviation.

All rate calculations must reference `billingcontext_data.md`. All report column references must reference `collab_reports.md`.

**Working directory:** The billing-analyst agent must always operate out of `/Users/konyebin/wxops/report_bot/`. Read and write all scripts and output files relative to that directory.

**Dashboard:** When the user asks for a dashboard, launch it immediately — do not just print instructions. Run:
```
cd /Users/konyebin/wxops && .venv/bin/streamlit run report_bot/billing_dashboard.py
```
Run this as a background process so it doesn't block, then tell the user to open http://localhost:8501.

Sources used during construction of this document are listed in the Sources section below.

---

## Sources

| Title | URL |
|-------|-----|
| Understand Your Cisco Calling Plan Bill | https://help.webex.com/en-us/article/nw4s9rm/Understand-Your-Cisco-Calling-Plan-Bill |
| Reports for Your Cloud Collaboration Portfolio | https://help.webex.com/en-us/article/nmug598/Reports-for-Your-Cloud-Collaboration-Portfolio |
| Get Started with the Cisco Calling Plans | https://help.webex.com/en-us/article/nousk9ab/Get-Started-with-the-Cisco-Calling-Plans |
| Webex Calling Detailed Call History API Reference | https://developer.webex.com/docs/api/v1/reports-detailed-call-history/get-detailed-call-history |
| Understand Detailed Call History Report for Webex Calling | https://www.cisco.com/c/en/us/support/docs/unified-communications/webex-calling/220377-understand-detailed-call-history-report.html |

---

## Query 1 — Create a Sample Bill

**Goal:** Produce a synthetic estimated invoice for a customer org covering a specified billing period.

### Steps

1. **Load billing rules**
   - Read `billingcontext_data.md`
   - Identify which SKUs are Recurring (committed, in advance) vs Usage/Overage (uncommitted, in arrears)
   - Note: Recurring = committed Outbound Calling Plans only. Everything else is Usage/Overage.

2. **TN charge calculation**
   - Fetch the **Telephone Number Inventory** report (point-in-time)
   - Count TNs by type: `Number type` = primary/secondary; `Country` for local vs non-local classification
   - If provisioning history is available (e.g., from audit log or prior invoices), reconstruct the per-day TN count for the period
   - Calculate TN charge: `count of TNs × days provisioned × daily rate`
   - Apply local rate (`A-AUD-U-TN`) to local numbers; non-local rate (`A-AUD-U-TN-NL`) to non-local numbers
   - Use the QTY formula: sum of provisioning days across all TNs (e.g., 2 TNs × 30 days + 1 TN × 15 days = QTY 75)

3. **Minute usage from CDR**
   - Fetch **Calling Detailed Call History** for the billing period
   - Filter: `PSTN vendor name` = `"Cisco Calling Plans"` → these are the CCP-billable call records
   - Sum `Duration` field (seconds) / 60 → total CCP minutes
   - Sub-filter by `Call type` for each charge category:
     - `SIP_NATIONAL` + `Direction` = `ORIGINATING` → domestic outbound minutes (included in plan)
     - `SIP_INBOUND` + `Direction` = `TERMINATING` → inbound minutes
     - `SIP_INTERNATIONAL` → international minutes (billable per minute)
     - `SIP_TOLLFREE` + `Direction` = `TERMINATING` → inbound toll-free minutes

4. **Service number overage calculation**
   - The bundle includes **250 minutes per service number per month** (inbound + outbound combined); this is a per-SN threshold, not a pooled org-wide bucket
   - From CDR: filter rows where `Called number` OR `Calling number` matches a known service number
   - Sum `Duration` per service number across both directions → total minutes per SN
   - For each SN: if total minutes > 250 → overage = total − 250; apply `A-AUD-PSTN-SN` rate
   - Separate local vs non-local service numbers; apply `-NL` SKU for non-local

5. **International minutes by destination**
   - From CDR: filter `Call type` = `SIP_INTERNATIONAL`
   - Group by `International Country`
   - Sum `Duration` per country → minutes per destination
   - Apply destination-specific rate from `billingcontext_data.md` international rate tiers

6. **Build the estimated bill table**

Only include SKUs with confirmed rates from the invoice sample. SKUs marked "NOT IN INVOICE" in `billingcontext_data.md` must be **omitted entirely** from the estimate — do not show them as $0.00 or unknown, just leave them out until rates are confirmed.

Confirmed SKUs to include:
```
| SKU | Description | QTY | Unit | Rate | Amount |
|-----|-------------|-----|------|------|--------|
| A-AUD-U-TN | Local TN Uncommitted | [TN-days] | TN/day | $0.03 | [calc] |
| A-AUD-U-IBTF | Inbound Toll-Free Number Bundle | [num-days] | number/day | $0.16 | [calc] |
| A-AUD-OCP1-U | Outbound Calling Plan Uncommitted | [user-days] | user/day | $0.1315 | [calc] |
| A-AUD-PSTN-IBTF | Inbound Toll-Free Minutes Overage | [minutes] | per min | $0.03 | [calc] |
| A-AUD-PSTN-INT | International Metered Calling | [minutes] | per min | $0.0272 | [calc] |
```

SKUs to omit until rates are confirmed: `A-AUD-U-TN-NL`, `A-AUD-U-SN`, `A-AUD-U-SN-NL`, `A-AUD-PSTN-SN`, `A-AUD-PSTN-SN-NL`, `A-AUD-PSTN-INT-NL`.

> ⚠️ Flag every rate in the output table with **EXPERIMENTAL**. These are estimates only. The real rates are on the customer's invoice from Cisco.

7. **Present totals**
   - Subtotal (excl. tax)
   - Note that tax cannot be estimated without knowing the exact TN provisioning locations and applicable jurisdiction rates
   - Note the arrears lag: international and overage charges from this period will appear on the *next* invoice, not the current one

8. **Always follow the line-item table with a detailed plain-English explanation of each charge.** Cover:

   **Telephone Number Charges (local and non-local)**
   - Explain that Cisco charges per TN per day regardless of whether it rings — it is a line rental fee
   - Show the formula explicitly: `TN count × days in period × daily rate = amount`
   - Explain the local vs non-local split: local = org's primary country (e.g., USA), non-local = all other countries, non-local rate is higher
   - Flag the point-in-time caveat: TN inventory is a snapshot; mid-period adds/removes would lower the actual QTY

   **Uncommitted Users (`A-AUD-OCP1-U`)**
   - Explain what committed vs uncommitted means: the CCW order locks in N committed seats billed monthly in advance; any user beyond N who makes/receives a CCP call is billed as uncommitted at a daily rate
   - Explain the call-order method: rank all unique CDR users (filtered to `PSTN vendor name = "Cisco Calling Plans"` and `User type = "User"`) by earliest call timestamp; first N = committed, the rest = uncommitted
   - Show which specific users were uncommitted and how many active days each had
   - Flag that N = 15 is a default assumption and must be confirmed from the CCW order

   **International Minutes (`A-AUD-PSTN-INT`)**
   - Explain that domestic calls (SIP_NATIONAL, SIP_MOBILE) are included in the plan — no per-minute charge
   - International calls are metered; show destination, minutes, tier, and rate
   - Note any unusual destinations (e.g., destination = "US" from a non-US location routing as international)

   **Zero-dollar lines**
   - For every $0.00 line, explain WHY it is zero (threshold not reached, no numbers of that type, etc.)
   - Service number overage: state the 250 min/month threshold and show the actual minutes vs threshold for the busiest SN
   - Toll-free: confirm no TF numbers in inventory and no SIP_TOLLFREE rows in CDR

   **What is missing from the estimate**
   - Always close with a table of what could not be calculated and where to find it:

   | Missing piece | Why missing | Where to find it |
   |---|---|---|
   | Recurring committed plan charges | Set in CCW order, not in CDR/TN data | Customer's CCW subscription or prior invoice |
   | Taxes | Requires per-TN jurisdiction data | Annexure section of a real invoice |
   | Mid-period TN changes | TN inventory is a snapshot | Audit log or prior invoice's TN block |
   | Actual contracted rates | Rates are from published rate sheets | Customer's rate card |

---

## Query 2 — Show Data for Overages

**Goal:** Identify which users/numbers are generating overage charges and quantify the overage.

Two distinct overage mechanisms exist:

### Trigger A — Uncommitted Users (A-AUD-OCP1-U)

1. Pull **Calling Detailed Call History** for the billing period
2. Filter: `PSTN vendor name` = `"Cisco Calling Plans"` AND `User type` = `"User"`
3. Extract unique `User UUID` values, ordered by their **earliest call timestamp** in the period (ascending)
4. **Determine committed vs uncommitted by call order:**
   - The first N unique users to place or receive a CCP-billable call are deemed **committed** (where N = the committed seat count; default assumption is 15 unless told otherwise)
   - All remaining unique users beyond position N are deemed **uncommitted**
   - This approximates CCW committed plan allocation without requiring a CCW export
5. For each uncommitted user: count the number of distinct calendar days with CCP call activity in the period
6. Calculate: `uncommitted user-days × daily rate (A-AUD-OCP1-U)`
7. Output:

```
| Rank | User UUID | User Name | First Call Date | Days Active | Status | Estimated Overage |
|------|-----------|-----------|-----------------|-------------|--------|-------------------|
```

> **Assumption:** In the absence of a CCW subscription export or invoice Recurring Charges block, committed users are determined by call order — the first N callers in the period are treated as having committed seats. This is an approximation; actual committed users are defined by the CCW subscription, not call timing.

### Trigger B — Service Number Minutes > 250 (A-AUD-PSTN-SN / -NL)

The 250 min/month threshold is **per service number** (not pooled across all SNs). Both inbound and outbound minutes count toward the threshold.

1. Pull **Calling Detailed Call History** for the billing period
2. Filter: rows where `Called number` OR `Calling number` matches a known service number (from TN Inventory report)
3. Group rows by service number (match against either column)
4. Sum `Duration` per service number across both directions → total minutes per SN for the period
5. Apply the 250 min/month threshold per SN:
   - If total minutes ≤ 250 → no overage
   - If total minutes > 250 → overage minutes = total − 250
6. Classify each SN as local or non-local (from TN Inventory `Number type` and `Country`)
7. Apply rate: `A-AUD-PSTN-SN` for local; `A-AUD-PSTN-SN-NL` for non-local
8. Output:

```
| Service Number | Type | Total Minutes | Included | Overage Minutes | Rate | Estimated Charge |
|---------------|------|---------------|----------|-----------------|------|-----------------|
```

### Trigger C — Inbound Toll-Free Minutes (A-AUD-PSTN-IBTF)

The toll-free bundle includes a set number of inbound minutes **per number** (not pooled). A one-time activation fee also applies in the first month the number is provisioned.

1. Pull CDR, filter `Call type` = `SIP_TOLLFREE` + `Direction` = `TERMINATING`
2. Group by `Called number` (toll-free number)
3. Sum `Duration` per toll-free number
4. Compare against included minutes for the toll-free bundle (check invoice for included amount — threshold is per number, not org-wide)
5. Calculate overage: total − included → apply `A-AUD-PSTN-IBTF` rate
6. Flag any toll-free numbers newly provisioned in the period — these carry a one-time activation fee on first month's invoice

---

## Query 3 — Count Cisco Calling Plan Users

**Goal:** Determine how many distinct users are active on Cisco Calling Plans in a billing period.

### Steps

1. Pull **Calling Detailed Call History** for the full billing period
2. Filter: `PSTN vendor name` = `"Cisco Calling Plans"` → keep only CCP-billable call records
3. Count unique `User UUID` values in the filtered dataset
   - **Use `User UUID`, not `User` display name** — UUIDs are stable; display names can change or be duplicates
4. Separate by `User type`:
   - `User` → standard Webex Calling users
   - `VirtualLine` → virtual lines (counted separately from users)
   - Any other values → flag for review; do not assume they are user licences

5. **Cross-reference with Telephone Number Inventory**
   - Pull TN Inventory report
   - Count TNs assigned to each `User type`
   - Verify: unique CDR user count ≈ TN assignment count (discrepancies may indicate unassigned numbers or users without numbers)

6. Output summary:

```
| User Type | Unique UUID Count | Assigned TNs (TN Inventory) |
|-----------|------------------|------------------------------|
| User | [n] | [n] |
| VirtualLine | [n] | [n] |
| [Other] | [n] | [n] — REVIEW REQUIRED |
| Total | [n] | [n] |
```

> **Gotcha:** A user who placed or received only internal calls (`Call type` = `SIP_ENTERPRISE`) will NOT appear in the CCP-filtered CDR. Only calls routed through Cisco Calling Plans PSTN infrastructure create `PSTN vendor name` = `"Cisco Calling Plans"` records.

---

## Query 4 — Virtual Line Usage

**Goal:** Report on activity levels, minute volumes, and direction breakdown for all virtual lines in the organisation.

### Steps

1. Pull **Calling Detailed Call History** for the billing period
2. Filter: `User type` = `"VirtualLine"`
   - This isolates all call records associated with virtual lines
3. Count unique `User UUID` values → number of distinct virtual lines that were active in the period
4. Sum `Duration` per unique `User UUID` → minutes per virtual line
5. Break down by `Direction`:
   - `ORIGINATING` (outbound) — virtual line made calls
   - `TERMINATING` (inbound) — virtual line received calls
6. Further sub-filter by `Call type` for minute classification (SIP_NATIONAL, SIP_INTERNATIONAL, etc.)
7. If multi-site organisation: group results by `Location`
8. Output:

```
| User UUID | VL Display Name | Location | Outbound Min | Inbound Min | Total Min | Call Types |
|-----------|----------------|----------|-------------|------------|-----------|------------|
```

> ⚠️ **NOTE:** The `User type` value list is not exhaustive. If you encounter `User type` values other than `User` and `VirtualLine`, flag them — do not silently exclude them. Some unknown types may represent virtual lines or call features that should be included in billing analysis.

> **Gotcha:** Virtual lines appear in the `User` column by display name (e.g., `"VL Bally Lakh"`). Do not rely on display name prefixes like "VL" — always filter by `User type` = `VirtualLine` for reliability.

---

## Query 5 — CVI License Accuracy (90-Day Rolling)

**Goal:** Identify whether the number of CVI (VIMT) licences allocated matches actual device usage over the past 90 days. Surface reclaim candidates and compliance risks.

### Steps

1. **Pull VIMT License Report**
   - This gives the current licensed CVI device count (N) and per-device licence status
   - Record: device name, licence type, allocation status, assigned org

2. **Pull VIMT Usage Report**
   - Filter to the last 90 days
   - Extract active device count (M) — devices that have registered usage in the window
   - Record: device, last active date, 90-day usage volume

3. **Compare N vs M**
   - Build a merged device list joining both reports on device identifier
   - Classify each device:

| Condition | Classification | Action |
|-----------|---------------|--------|
| Licensed + used in 90 days | Active | No action required |
| Licensed + **zero usage in 90 days** | Idle — reclaim candidate | Flag for customer review |
| Not licensed + has usage | Unlicenced active device | Compliance risk — escalate immediately |
| Not licensed + no usage | Not provisioned | No action required |

4. **Output table**

```
| Device | Licence Status | Last Active Date | 90-Day Usage | Recommended Action |
|--------|---------------|-----------------|-------------|-------------------|
| [name] | Licensed | [date] | [sessions] | No action |
| [name] | Licensed | None in 90 days | 0 | Reclaim candidate |
| [name] | Unlicenced | [date] | [sessions] | COMPLIANCE RISK |
```

5. **Summary counts**
   - Total licenced devices: N
   - Active (used in 90 days): M
   - Idle (licenced, no usage): N − M
   - Unlicenced active: (flag count)
   - Potential licence savings: (N − M) × per-licence monthly cost

> **Gotcha:** Confirm with the customer before recommending reclaim. Some CVI devices may be intentionally reserved for infrequent-use rooms (e.g., boardrooms, training rooms) and low 90-day usage is expected.

> **Gotcha:** The VIMT Usage Report window is rolling, not calendar-aligned. A device last used 91 days ago will show as inactive even if it was heavily used just outside the window.
