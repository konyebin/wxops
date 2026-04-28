# Webex Control Hub Reports

## Overview

**Webex Control Hub Reports** allow organisation admins to track performance, usage, and quality metrics across meetings, calling, messaging, and devices. Reports are delivered as **CSV files**, generated either on-demand (immediate download) or on a scheduled basis (daily, weekly, monthly) with email notification on completion. Reports are available under **Control Hub → Reports**.

Only admins or users explicitly granted report-generation permissions can access reports. The Reports API and Report Templates API require **Pro Pack** licensing.

Sources used during construction of this document are listed in the Sources section below.

---

## Sources

| Title | URL |
|-------|-----|
| Reports for Your Cloud Collaboration Portfolio | https://help.webex.com/en-us/article/nmug598/Reports-for-Your-Cloud-Collaboration-Portfolio |
| Understand Detailed Call History Report for Webex Calling | https://www.cisco.com/c/en/us/support/docs/unified-communications/webex-calling/220377-understand-detailed-call-history-report.html |
| Webex Calling Detailed Call History API Reference | https://developer.webex.com/docs/api/v1/reports-detailed-call-history/get-detailed-call-history |
| Webex Detailed Call History API Blog Post | https://developer.webex.com/blog/webex-detailed-call-history-api |
| Manage User Calling Data | https://help.webex.com/en-us/article/ijda3o/Manage-User-Calling-Data |

---

## Licensing Tiers

| Feature | Standard | Pro Pack |
|---------|----------|----------|
| Max date range per download | 31 days | 92 days |
| Historical data window (most reports) | 89–400 days | 400 days |
| Calling Detailed Call History window | 89 days | 400 days |
| API access (Reports API + Templates API) | No | Yes |
| Scheduling | Yes | Yes |

---

## Data Timing

| Property | Value |
|----------|-------|
| **Timezone** | UTC (all timestamps in all reports) |
| **Data delay** | ~8 hours — prior-day data appears around 08:00 UTC |
| **Same-day reports** | May contain partial data; generate in the afternoon for better coverage |
| **Processing time** | Up to 24 hours depending on dataset size and queue depth |
| **File naming convention** | `[Template Name]_[Alphanumeric]_[Download Date].csv` |

---

## Report Priority Matrix

Which report is the primary source of truth for each billing or usage question:

| Query | Primary Report | Why | Secondary |
|-------|---------------|-----|-----------|
| CCP minute usage | Calling Detailed Call History | Has `PSTN vendor name`, `Duration`, `User type`, `Call type`, `Direction` — only report that identifies Cisco Calling Plan calls at the minute level | — |
| TN inventory / count | Telephone Number Inventory | Only source for current number count, status, and assignment | — |
| Virtual Line activity | Calling Detailed Call History | Filter `User type` = `VirtualLine` to isolate virtual line call records | — |
| International minutes | Calling Detailed Call History | Filter `Call type` = `SIP_INTERNATIONAL`; group by `International Country` | — |
| Queue performance | Call Queue Stats | Only source for queue-level handle time, abandonment, overflow, timeout metrics | Call Queue Agent Stats |
| CVI license accuracy | VIMT License Report + VIMT Usage Report | Only reports exposing CVI device licensing and activity | — |
| Hunt group performance | Hunt Group Stats | Only source for hunt group answer rates, abandonment, agent counts | Hunt Group Agent Stats |
| Auto attendant call routing | Auto Attendant Stats Summary | Shows answered vs unanswered, call volume, routing outcomes | AA Business/After-Hours Key Details |
| Inbound toll-free minutes | Calling Detailed Call History | Filter `Call type` = `SIP_TOLLFREE` + `Direction` = `TERMINATING` | — |
| Service number overage risk | Calling Detailed Call History | Filter `Called number` matching service number list; sum `Duration` per number | — |

---

## Calling Detailed Call History

The most comprehensive calling report in Control Hub. Contains one CDR row per call leg (inbound and outbound legs are separate rows). This is the **primary source for all CCP billing analysis**.

**Date range:** Standard — 89 days history, 31 days per download. Pro Pack — 400 days history, 92 days per download.

### Complete Column Headers (CSV Source of Truth)

```
Start time, Answer time, Duration, Calling number, Called number, User, Calling line ID,
Called line ID, Correlation ID, Location, Inbound trunk, Outbound trunk, Route group,
Direction, Call type, Client type, Client version, Sub client type, OS type, Device Mac,
Model, Answered, International Country, Original reason, Related reason, Redirect reason,
Site main number, Site timezone, User type, Call ID, Local SessionID, Remote SessionID,
User UUID, Org UUID, Report ID, Department ID, Site UUID, Releasing party,
Redirecting number, Transfer related call ID, Dialed digits, Authorization code,
Call transfer time, User number, Local call ID, Remote call ID, Network call ID,
Related call ID, Call outcome, Call outcome reason, Final local sessionID,
Final remote sessionID, Answer Indicator, Ring duration, Release time, Report time,
PSTN legal entity, PSTN vendor Org ID, PSTN vendor name, PSTN provider ID,
Caller ID number, External caller ID number, Device owner UUID,
Call Recording Platform Name, Call Recording Result, Call Recording Trigger,
Redirecting party UUID, Public Calling IP Address, Public Called IP Address,
Original called party UUID, Recall Type, Hold Duration, Auto Attendant Key Pressed,
Queue Type, Answered Elsewhere, Route list calls overage, Caller Reputation Score,
Caller Reputation Service Result, Caller Reputation Score Reason, Interaction ID,
WxCC consult merge status, ELIN, Emergency number source
```

### Column Categories

**Billing-Critical** — used for charge calculations:

| Column | Description |
|--------|-------------|
| `Start time` | UTC timestamp when the call was initiated |
| `Duration` | Call duration in seconds; divide by 60 for minutes |
| `User` | Display name of the Webex Calling user or service |
| `Direction` | `ORIGINATING` (outbound) or `TERMINATING` (inbound) |
| `Call type` | Type of call — see Call Type Values table below |
| `User type` | Category of calling entity — see User Type Values below |
| `PSTN vendor name` | Name of PSTN provider; `"Cisco Calling Plans"` identifies CCP-billable calls |
| `PSTN legal entity` | Regulated entity providing PSTN service; `"Broadsoft Adaption LLC"` for Cisco CCP |
| `International Country` | Destination country for international calls; populated when `Call type` = `SIP_INTERNATIONAL` |
| `User UUID` | Stable UUID for the user — use this (not `User` display name) for unique user counts |

**Routing & Identity:**

| Column | Description |
|--------|-------------|
| `Calling number` | E.164 number of the calling party |
| `Called number` | E.164 number of the called party |
| `Location` | Webex Calling location name |
| `Inbound trunk` | Name of inbound PSTN trunk (if applicable) |
| `Outbound trunk` | Name of outbound PSTN trunk (if applicable) |
| `Route group` | Route group used for the call |
| `Org UUID` | Organisation UUID |
| `Site UUID` | Site/location UUID |
| `Department ID` | Department identifier |

**Outcome:**

| Column | Description |
|--------|-------------|
| `Answered` | `TRUE` or `FALSE` |
| `Call outcome` | `Success`, `Failure`, `Refusal` |
| `Call outcome reason` | Detailed reason code (e.g., `Normal`, `UserBusy`, `NoAnswer`) |
| `Answer Indicator` | How the call was answered (direct, forwarded, etc.) |
| `Ring duration` | Seconds the call rang before answer or abandonment |
| `Releasing party` | Which party ended the call |

**Session IDs** (for call correlation and transfer tracking):

| Column | Description |
|--------|-------------|
| `Call ID` | Unique identifier for this call leg |
| `Correlation ID` | Links all legs belonging to the same call flow |
| `Local SessionID` | UUID for the local media session |
| `Remote SessionID` | UUID for the remote media session |
| `Interaction ID` | Groups all interactions in a multi-leg scenario |
| `Local call ID` | Local SIP call ID |
| `Remote call ID` | Remote SIP call ID |

**Features:**

| Column | Description |
|--------|-------------|
| `Auto Attendant Key Pressed` | DTMF key pressed when routed through an auto attendant |
| `Queue Type` | Type of call queue involved |
| `Call Recording Platform Name` | Recording platform name if call was recorded |
| `Call Recording Result` | Outcome of recording attempt |
| `Call Recording Trigger` | What triggered the recording |
| `Redirecting number` | Number that redirected the call |
| `Redirect reason` | Reason for the redirect |
| `Redirecting party UUID` | UUID of the redirecting party |
| `Transfer related call ID` | Links transfer legs together |
| `Hold Duration` | Total hold time in seconds |
| `Dialed digits` | Digits dialed by the user |
| `Authorization code` | Outgoing calling permission authorization code |

### Virtual Line Identification

- Filter `User type` == `VirtualLine` to isolate virtual line calls from user calls
- Virtual lines appear with their display name in the `User` column (e.g., `"VL Bally Lakh"`)
- `User UUID` for virtual lines is stable and unique — use for counting distinct active virtual lines

**Known `User type` values (from real CDR data):**

| Value | Meaning |
|-------|---------|
| `User` | Standard Webex Calling user |
| `VirtualLine` | Virtual line (multi-line, shared appearance) |

> ⚠️ **NOTE:** The above list is NOT exhaustive. Additional `User type` values are expected in real data (e.g., `HuntGroup`, `AutomatedAttendantVideo`, `Place`, `VoiceMail`). This list will be updated as more CDR exports are collected. Flag any unrecognised `User type` values for review.

### Call Type Values

| Value | Description |
|-------|-------------|
| `SIP_NATIONAL` | Domestic PSTN outbound call |
| `SIP_INBOUND` | Inbound PSTN call |
| `SIP_INTERNATIONAL` | International outbound PSTN call |
| `SIP_TOLLFREE` | Toll-free number call |
| `SIP_MEETING` | Call into/from a Webex meeting |
| `SIP_SHORTCODE` | Short code call (e.g., directory services) |
| `SIP_EMERGENCY` | Emergency (911) call |
| `SIP_PREMIUM` | Premium rate number call |
| `SIP_ENTERPRISE` | Internal enterprise call |
| `SIP_MOBILE` | Mobile number call |
| `SIP_URI` | SIP URI call |
| `SIP_OPERATOR` | Operator-assisted call |
| `SIP_CLICKTOCALL` | Click-to-call initiated call |

### Key Field Values for Billing Filters

| Field | Value | Meaning |
|-------|-------|---------|
| `PSTN vendor name` | `"Cisco Calling Plans"` | Call is billable under CCP |
| `PSTN legal entity` | `"Broadsoft Adaption LLC"` | Confirms Cisco billing entity (varies by region) |
| `Direction` | `ORIGINATING` | Outbound call leg |
| `Direction` | `TERMINATING` | Inbound call leg |

---

## Telephone Number Inventory

Point-in-time snapshot of all telephone numbers and extensions in the organisation. **No date range selector** — always reflects the current state.

**Update frequency:** Changes are reflected within 24 hours of provisioning or deactivation.

**Use for:** Counting assigned TNs for billing calculations; validating number type (local vs non-local); identifying unassigned numbers.

### Columns

| Column | Description |
|--------|-------------|
| `Location` | Webex Calling location name |
| `Country` | Country code for the number |
| `Phone number` | E.164 format telephone number |
| `Extension` | Internal extension (if assigned) |
| `Active` | Whether the number is active |
| `User type` | Type of entity the number is assigned to |
| `Number type` | Primary or secondary number |
| `Email` | Email of the assigned user (if a user) |
| `User UUID` | UUID of the assigned user |
| `Last known` | Last known activity or assignment date |

> **Gotcha:** This is a point-in-time report. It cannot be used to determine how many TNs were provisioned on a specific past date. For historical TN counts, cross-reference with invoice QTY values or provision/de-provision audit logs.

---

## Call Queue Stats

Group-level performance metrics for call queues. Covers the selected date range.

### Columns

```
Call Queue, Location, Phone NO., Extension, Total Hold Time, Avg Hold Time,
Total Talk Time, Avg Talk Time, Total Handle Time, Avg Handle Time,
Total Wait Time, Avg Wait Time, Answered Calls, % Answered Calls,
Abandoned Calls, % Abandoned Calls, Avg Abandoned Time, Total Abandoned Time,
Total Calls, Calls Overflowed, Calls Timed Out, Calls Transferred,
Avg No. of Agents Assigned, Avg No. of Agents Handling Calls
```

**Use for:** Queue-level SLA reporting, overflow analysis, staffing analysis.

---

## Auto Attendant Stats Summary

Call volume and outcome metrics for auto attendants.

### Columns

```
Auto Attendant, Ph.No./Extn., Location, Total Calls, Answered, Unanswered,
Busy, Others, % Answered, Total Duration, Total AA Talktime
```

Related variants (separate reports):
- **Auto Attendant Business Hours Key Details** — key-press statistics during business hours
- **Auto Attendant After-Hours Key Details** — key-press statistics after hours

---

## Hunt Group Stats

Group-level performance metrics for hunt groups.

### Columns

```
Hunt Group, Location, Phone No, Extension, Total Talk Mins, Avg Talk Mins,
Total Handle Mins, Avg Handle Mins, Total Wait Mins, Avg Wait Mins,
Total Abandoned Mins, Avg Abandoned Mins, Calls Answered, % Calls Answered,
Calls Abandoned, % Calls Abandoned, Avg No. of Agents Handling Calls
```

Related report: **Hunt Group Agent Stats** — per-agent breakdown within each hunt group.

---

## VIMT License Report (CVI)

**Purpose:** License allocation and usage tracking for Video Integration for Microsoft Teams (VIMT), also known as Cloud Video Interop (CVI).

- **Type:** Point-in-time snapshot
- **Use for:** Verifying that the number of CVI licenses allocated matches the number of provisioned devices; identifying over- or under-licensed states

**Fields include:** Device name, license type, allocation status, assigned organisation

**Audit logic:** Pull this report to get the total licensed CVI device count. Compare against VIMT Usage Report to identify zero-usage licences.

---

## VIMT Usage Report (CVI)

**Purpose:** Device-level usage patterns and activity for VIMT/CVI devices.

- **Type:** Rolling window (up to 90 days)
- **Use for:** 90-day rolling CVI usage tracking to verify licence accuracy

**Fields include:** Device usage metrics, activity timestamps, device identifiers

**90-Day Licence Accuracy Logic:**
1. Pull **VIMT License Report** → get total licensed CVI device count (N)
2. Pull **VIMT Usage Report** → filter to last 90 days → get active device count (M)
3. Compare N vs M:
   - Devices with a licence but **zero usage in 90 days** → potential reclaim candidates
   - Devices with usage but **no licence** → compliance risk (should not occur but flag if found)
4. Output: `Device | Licence Status | Last Active | 90-Day Usage | Action`

> **Gotcha:** A device that has a licence but hasn't been used in 90 days is not automatically a waste — confirm with the customer that the device is intentionally reserved before reclaiming.

---

## Other Reports

| Report | Category | Key Use |
|--------|----------|---------|
| **Meetings Usage Summary** | Meetings | Total meetings, minutes, participants by period |
| **Meetings Details** | Meetings | Per-meeting host, duration, attendees, recording status, telephony minutes |
| **Meetings Inactive Users** | Meetings | Users who haven't hosted or attended in the period — licence reclamation candidates |
| **Messaging User Activity** | Messaging | Per-user daily messages, calls, files, spaces (days with no activity omitted) |
| **Calling Media Quality** | Calling | Call leg media metrics (jitter, latency, packet loss) from supported devices |
| **Call Queue Agent Stats** | Calling | Per-agent answered/presented/bounced calls, talk/hold/handle time |

---

## Retirement Notices

> ⚠️ The following reports are **retiring April 28, 2026**. Any scheduled runs will be automatically removed. Migrate to the replacement reports before this date.

| Retiring Report | Replacement |
|----------------|-------------|
| Calling Engagement Report | Calling Media Quality Report |
| Calling Quality Report | Calling Media Quality Report |
| Messaging App Version Report | Webex App Version Report |
