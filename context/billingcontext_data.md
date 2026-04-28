# Cisco Calling Plan — Billing Context

## Overview

**Cisco Calling Plan** is Cisco's managed PSTN service for Webex Calling, available in select countries. Invoices are issued by **CISCO SYSTEMS, INC.** (170 West Tasman Drive, San Jose, CA 95134) on behalf of **Broadsoft Adaption LLC**, the regulated entity that provides PSTN services. Charges appear as two categories: **Recurring Charges** (committed, billed one month in advance) and **Usage/Overage Charges** (uncommitted, billed monthly in arrears). Each subscription receives a single invoice regardless of how many locations it covers.

Sources used during construction of this document are listed in the Sources section below.

---

## Sources

| Title | URL |
|-------|-----|
| Understand Your Cisco Calling Plan Bill | https://help.webex.com/en-us/article/nw4s9rm/Understand-Your-Cisco-Calling-Plan-Bill |
| Get Started with the Cisco Calling Plans | https://help.webex.com/en-us/article/nousk9ab/Get-Started-with-the-Cisco-Calling-Plans |
| View and Download Your Invoice | https://help.webex.com/en-us/article/nxavgdg/View-and-download-your-invoice |
| Cisco Calling Plans International Rates (US) | https://www.webex.com/content/dam/wbx/us/documents/pdf/us-international-rates-updated.pdf |
| Cisco Calling Plans International Rates (Europe) | https://www.webex.com/content/dam/wbx/us/documents/pdf/europe-international-rates.pdf |
| Reports for Your Cloud Collaboration Portfolio | https://help.webex.com/en-us/article/nmug598/Reports-for-Your-Cloud-Collaboration-Portfolio |

---

## Invoice Structure

### Header Fields

| Field | Description |
|-------|-------------|
| **Billed By** | CISCO SYSTEMS, INC., 170 West Tasman Drive, San Jose, CA 95134 (on behalf of Broadsoft Adaption LLC) |
| **Remit To** | Payment address (e.g., PO BOX 12345, CHICAGO IL 60652, Bank of America N.A.) |
| **Invoice Number** | Unique invoice identifier |
| **TRX Date** | Date billing data was extracted; determines the billing period |
| **Amount** | Total invoice amount |
| **PO Number** | Customer purchase order reference |
| **Due Date** | Payment due date (typically TRX Date + 30 days) |
| **Currency** | Billing currency (USD for US) |
| **Terms** | Payment terms (e.g., 30 NET) |
| **Web Order ID** | Order identifier in Cisco Commerce Workspace (CCW) |
| **Customer Number** | Cisco customer account number |
| **Bill To Number (BTN)** | Used for number porting purposes; appears on every invoice page |
| **Bill To** | Partner/VAR billing address |
| **Service To** | End-customer service address |

### Summary of Charges

| Line Item | Description |
|-----------|-------------|
| **Recurring Charges** | Committed monthly charges billed one month in advance |
| **Usage/Overage Charges** | Uncommitted elements billed in arrears (~30 days after period end) |
| **Other Charges** | Activation fees and one-time items |
| **Subtotal (Excl. Tax)** | Sum of all charge categories before tax |
| **Taxes** | Jurisdiction-specific taxes (city, county, state, federal) |
| **Total Amount (Incl. Tax)** | Final amount due |

The invoice also contains an **Annexure** section with tax detail breakdown and a list of billed telephone numbers.

---

## Recurring Charges

Recurring charges are **committed charges** that occur on a repetitive monthly basis. They are billed **one month in advance** relative to the service period.

- This section contains **only committed Outbound Calling Plans**
- **At least ONE committed Outbound Calling Plan must exist per subscription** — this is a platform requirement to enable access to all Cisco Calling Plan services
- Committed plans are ordered via Cisco Commerce Workspace (CCW) or provisioned in Control Hub
- Billing starts: on the service date specified in the CCW order, or immediately upon Control Hub provisioning

---

## Usage/Overage Charges (Arrears)

Uncommitted elements are billed **monthly in arrears**, generally appearing on the invoice approximately **30 days after the billing period ends**.

### Overage Triggers

| Charge Type | Trigger | SKU |
|-------------|---------|-----|
| Outbound Calling Plan — Uncommitted | User has no committed calling plan; billed per user per day active | `A-AUD-OCP1-U` |
| Service Number minutes — Local | Minutes exceed **250 min/month per service number** | `A-AUD-PSTN-SN` |
| Service Number minutes — Non-Local | Minutes exceed **250 min/month per non-local service number** | `A-AUD-PSTN-SN-NL` |
| Inbound Toll-Free minutes | Minutes exceed the included amount for the toll-free bundle | `A-AUD-PSTN-IBTF` |
| International calling | Any international minute; billed per minute by destination | `A-AUD-PSTN-INT` / `A-AUD-PSTN-INT-NL` |

**Key point:** `A-AUD-OCP1-U` applies specifically to **Uncommitted** users — those who appear in CDR activity without a corresponding committed Outbound Calling Plan in the Recurring Charges section of the invoice.

---

## Subscription IDs

- Each subscription receives **exactly one invoice per billing period**
- A single subscription may cover **multiple locations**
- The **Subscription ID** (e.g., `Sub12345`) appears in the header of every invoice page and on each charge block within the invoice
- Subscription IDs are visible in Cisco Commerce Workspace (CCW) under the order/subscription record
- Format example: **A-FLEX-3 Collaboration Flex Plan 3.0 / Subscription ID: Sub12345**

---

## SKU Reference Table

> ⚠️ All rates marked **EXPERIMENTAL** are derived from invoice samples and publicly available rate sheets. They are NOT contractual. Actual rates depend on subscription type, country, and negotiated pricing. Always verify against the customer's actual invoice or partner rate card.

| SKU | Description | Unit | Experimental Rate | Source |
|-----|-------------|------|-------------------|--------|
| `A-AUD-OCP1-U` | Outbound Calling Plan Uncommitted Usage Overage | Per user/day | ⚠️ ~$0.07–$0.10/user/day | Invoice sample |
| `A-AUD-U-TN` | Telephone Number (TN) — Local Uncommitted | Per TN/day | ⚠️ ~$0.033/TN/day | Invoice sample |
| `A-AUD-U-TN-NL` | Telephone Number (TN) — Non-Local Uncommitted | Per TN/day | ⚠️ ~$0.067/TN/day | Invoice sample |
| `A-AUD-U-SN` | Service Number Bundle (TN + included minutes) | Per number/day | ⚠️ ~$0.083/number/day | Invoice sample |
| `A-AUD-U-SN-NL` | Non-Local Service Number Bundle | Per number/day | ⚠️ ~$0.133/number/day | Invoice sample |
| `A-AUD-U-IBTF` | Inbound Toll-Free Number Bundle Uncommitted | Per number/day | ⚠️ ~$0.10/number/day | Invoice sample |
| `A-AUD-PSTN-SN` | Service Number Minutes Overage (Local) | Per minute | ⚠️ ~$0.02/min | Invoice sample |
| `A-AUD-PSTN-SN-NL` | Non-Local Service Number Minutes Overage | Per minute | ⚠️ ~$0.025/min | Invoice sample |
| `A-AUD-PSTN-IBTF` | Inbound Toll-Free Minutes Overage | Per minute | ⚠️ ~$0.025/min | Invoice sample |
| `A-AUD-PSTN-INT` | International Metered Calling — Local origin | Per minute | ⚠️ See destination table | Rate sheet |
| `A-AUD-PSTN-INT-NL` | International Metered Calling — Non-Local origin | Per minute | ⚠️ See destination table | Rate sheet |

**Notes:**
- `A-AUD-*` prefix indicates Australia as the billing country; other countries use a different regional prefix
- `-NL` suffix denotes Non-Local numbers (numbers provisioned outside the customer's primary location state/region)
- `U-` in SKU indicates an uncommitted (usage-based) element
- `PSTN-` in SKU indicates a per-minute usage charge

---

## International Destination Rate Tiers

> ⚠️ All rates below are **EXPERIMENTAL** — derived from Cisco's published international rate sheets (see Sources). Actual rates vary by billing country, subscription type, and may change without notice. Always verify against the customer's invoice or current Cisco rate card.

Cisco publishes country-specific international rate sheets (US rates, Europe rates, etc.). Rates are billed under `A-AUD-PSTN-INT` (local) or `A-AUD-PSTN-INT-NL` (non-local).

| Tier | Typical Destinations | Experimental Rate Range |
|------|---------------------|------------------------|
| **Tier 1** | North America (US, Canada, Mexico), Western Europe (UK, Germany, France, Netherlands, Spain, Italy, Austria, Belgium, Switzerland) | ⚠️ ~$0.01–$0.03/min |
| **Tier 2** | Eastern Europe (Poland, Czech Republic, Romania, Hungary), Latin America (Brazil, Argentina, Colombia, Chile), Asia-Pacific (Australia fixed, Japan, Singapore, Hong Kong, South Korea, India major) | ⚠️ ~$0.05–$0.15/min |
| **Tier 3** | Middle East (Saudi Arabia, UAE, Israel, Jordan), Africa (South Africa, Nigeria, Kenya, Egypt), Premium destinations (satellite, special services), Pacific Islands | ⚠️ ~$0.20–$0.50+/min |

**Practical notes:**
- On the invoice, `QTY` for international = total minutes used across all international destinations in the period
- `Rate Price` shown on the invoice is the **average** per-minute rate across all destinations dialed
- Individual destination rates are visible in the Annexure section of the invoice, broken down by country
- International calling to mobile numbers typically has higher rates than landline within the same country

---

## Billing Logic

### How QTY Is Calculated per Charge Type

| SKU Category | QTY Calculation | Example |
|--------------|-----------------|---------|
| **Outbound Calling Plan Uncommitted** (`A-AUD-OCP1-U`) | Sum of all user-days: each user without a committed plan contributes 1 to QTY for each calendar day they had calling activity | 5 uncommitted users × 30 days = QTY 150 |
| **Local TN** (`A-AUD-U-TN`) | Sum of provisioning days across all local TNs in the billing cycle. A TN provisioned for even 1 minute in a day counts as 1 full day | 2 TNs × 30 days + 1 TN × 15 days = **QTY 75** |
| **Non-Local TN** (`A-AUD-U-TN-NL`) | Same as local TN logic, applied to non-local numbers | 1 NL TN × 30 days = QTY 30 |
| **Service Number Bundle** (`A-AUD-U-SN`, `A-AUD-U-SN-NL`) | Sum of provisioning days for all service numbers (per-day regardless of call activity) | 2 SNs × 30 days = QTY 60 |
| **Inbound Toll-Free Bundle** (`A-AUD-U-IBTF`) | Sum of provisioning days for all toll-free numbers | 1 IBTF × 30 days = QTY 30 |
| **Service Number Minutes Overage** (`A-AUD-PSTN-SN`, `-NL`) | Total minutes in excess of 250 min/month **per service number**. Calculated individually per number, then summed | SN1 used 350 min → 100 overage min; SN2 used 200 min → 0 overage; Total QTY = 100 |
| **Inbound Toll-Free Minutes Overage** (`A-AUD-PSTN-IBTF`) | Total minutes in excess of the included amount for each toll-free number | Included: 500 min; Used: 750 min → QTY 250 |
| **International Metered Calling** (`A-AUD-PSTN-INT`, `-NL`) | Total international minutes used during the billing period across all international destinations | 93 minutes to UK + 12 minutes to Japan = QTY 105 |

**TN provisioning example (from real invoice):**
- 2 TNs provisioned for the full 30-day billing period = 60 day-units
- 1 TN provisioned for only 15 days of the period = 15 day-units
- **Total QTY = 75** at the daily TN rate

**Key rules:**
- A TN provisioned for **any portion of a day** counts as a full day of billing
- Service number bundles are billed daily regardless of whether any calls were made to the number
- Inbound Toll-Free has a **one-time activation fee** billed the month after provisioning (appears under Other Charges)
- International charges accumulate during the billing period but appear on the **next invoice** (~30 days in arrears)

---

## Tax Notes

### US Invoices
US invoices include a **Tax Details Annexure** with a full breakdown:

| Tax Level | Examples |
|-----------|---------|
| **Federal** | Federal Universal Service Fund (USF), federal excise tax |
| **State** | State sales tax, state USF, state telecom taxes |
| **County** | County 911/E911, county sales tax |
| **City** | City 911/E911, city sales tax, municipal telecom tax |

Tax format on invoice: `{TAX_TYPE}_{LEVEL}_(RATE)_(CITY)_(ST)_(COUNTY)`

Example: `E911 (VoIP)_County_USA_0.08_Benton_AR_Saline`

**E911 tax:** Required by state, county, and/or city where the service is deployed. Cisco applies the tax at the jurisdiction level — there is no Cisco markup on E911 charges.

**Access line taxes:** Charged monthly at a flat rate. These are **not prorated** even if the number was provisioned for only part of the month.

**Tax basis:** Taxes are assessed based on the provisioning location of each telephone number, not the billing address.

### Non-US Invoices
- VAT (Value Added Tax) appears as a line item in the main invoice body rather than in a separate annexure
- VAT rate varies by country
- Some countries have additional telecom-specific levies

### Tax Exemptions
- Tax exemption certificates and regulatory questions: **webexcalling-phd@cisco.com**
- Exemptions must be applied before the billing period to take effect on that invoice

---

## Billing Contacts

| Purpose | Contact |
|---------|---------|
| **General billing inquiries** | Contact information printed in the invoice header |
| **Tax exemption / regulatory questions** | webexcalling-phd@cisco.com |
| **Invoice access (webex.com customers)** | User Hub → Billing → Billing information → download icon |
| **Invoice access (CCW customers)** | Cisco Commerce Workspace, under the subscription ID |

**Billing entity confirmation:**
- Invoices show **CISCO SYSTEMS, INC.** as the billing party
- The legal entity providing PSTN services is **Broadsoft Adaption LLC**
- Card/payment charges appear from **BroadSoft Adaption LLC** on bank statements
- This is expected and correct — it is not a fraudulent charge
