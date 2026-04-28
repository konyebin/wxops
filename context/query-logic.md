# Billing Analyst Query Logic

## Overview

This file defines the reasoning paths the billing-analyst agent must follow when handling the five standard billing and usage queries. Each query maps to a specific data-fetch sequence, filter set, and output format. Follow these paths exactly — do not invent alternative approaches without noting the deviation.

All rate calculations must reference `billingcontext_data.md`. All report column references must reference `collab_reports.md`.

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
   - From CDR: filter rows where `Called number` matches a known service number
   - Sum `Duration` per service number per month → minutes per SN
   - For each SN: if minutes > 250 → overage = minutes − 250; apply `A-AUD-PSTN-SN` rate
   - Separate local vs non-local service numbers; apply `-NL` SKU for non-local

5. **International minutes by destination**
   - From CDR: filter `Call type` = `SIP_INTERNATIONAL`
   - Group by `International Country`
   - Sum `Duration` per country → minutes per destination
   - Apply destination-specific rate from `billingcontext_data.md` international rate tiers

6. **Build the estimated bill table**

```
| SKU | Description | QTY | Unit | Rate | Amount |
|-----|-------------|-----|------|------|--------|
| A-AUD-U-TN | Local TN Uncommitted | [days] | TN/day | ⚠️ EXPERIMENTAL | [calc] |
| A-AUD-U-TN-NL | Non-Local TN Uncommitted | [days] | TN/day | ⚠️ EXPERIMENTAL | [calc] |
| A-AUD-U-SN | Service Number Bundle | [days] | number/day | ⚠️ EXPERIMENTAL | [calc] |
| A-AUD-PSTN-SN | Service Number Overage | [minutes] | per min | ⚠️ EXPERIMENTAL | [calc] |
| A-AUD-PSTN-INT | International Calling | [minutes] | per min | ⚠️ EXPERIMENTAL | [calc] |
| ... | ... | ... | ... | ⚠️ EXPERIMENTAL | [calc] |
```

> ⚠️ Flag every rate in the output table with **EXPERIMENTAL**. These are estimates only. The real rates are on the customer's invoice from Cisco.

7. **Present totals**
   - Subtotal (excl. tax)
   - Note that tax cannot be estimated without knowing the exact TN provisioning locations and applicable jurisdiction rates
   - Note the arrears lag: international and overage charges from this period will appear on the *next* invoice, not the current one

---

## Query 2 — Show Data for Overages

**Goal:** Identify which users/numbers are generating overage charges and quantify the overage.

Two distinct overage mechanisms exist:

### Trigger A — Uncommitted Users (A-AUD-OCP1-U)

1. Pull **Calling Detailed Call History** for the billing period
2. Filter: `PSTN vendor name` = `"Cisco Calling Plans"`
3. Extract unique `User UUID` values from filtered rows
4. Cross-reference with the Recurring Charges section of the invoice:
   - Users in CDR who have **no corresponding committed Outbound Calling Plan** in Recurring Charges → uncommitted users
   - These users map to `A-AUD-OCP1-U` overage
5. For each uncommitted user: count the number of days with call activity in the period
6. Calculate: `user-days × daily rate (A-AUD-OCP1-U)`
7. Output:

```
| User UUID | User Name | Days Active | Estimated Overage |
|-----------|-----------|-------------|-------------------|
```

> **Note:** Identifying "committed vs uncommitted" requires the invoice's Recurring Charges section or a CCW subscription export. If not available, flag all active CCP users for manual review.

### Trigger B — Service Number Minutes > 250 (A-AUD-PSTN-SN / -NL)

1. Pull **Calling Detailed Call History** for the billing period
2. Filter: `Called number` = known service numbers (from TN Inventory report)
   - Alternatively filter: `Call type` in (`SIP_INBOUND`, `SIP_TOLLFREE`) where the Called number is a service number
3. Group rows by `Called number` (service number)
4. Sum `Duration` per service number → total minutes per SN for the period
5. Apply the 250 min/month threshold:
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

1. Pull CDR, filter `Call type` = `SIP_TOLLFREE` + `Direction` = `TERMINATING`
2. Group by `Called number` (toll-free number)
3. Sum `Duration` per toll-free number
4. Compare against included minutes for the toll-free bundle (check invoice for included amount)
5. Calculate overage: total − included → apply `A-AUD-PSTN-IBTF` rate

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
