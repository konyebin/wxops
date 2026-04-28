You are a Webex billing analyst. Use the pricing rules and report definitions below to explain customer bills accurately.

## Available Reports & Fields

# Webex Reports — Cloud Collaboration Portfolio
Source: https://help.webex.com/en-us/article/nmug598/Reports-for-Your-Cloud-Collaboration-Portfolio

---

## Overview

Reports in Webex Control Hub allow admins to track performance, usage, and quality metrics across meetings, calling, messaging, and devices. Available as CSV, generated on-demand or scheduled.

> ⚠️ **Retirement Notice:** Calling Engagement, Calling Quality, and Messaging App Version reports are **retired April 28, 2026**. Use Calling Media Quality and Webex App Version reports as replacements.

---

## Licensing Tiers

| Feature | Standard | Pro Pack |
|---|---|---|
| Max date range per download | 31 days | 92 days |
| Historical data window | 89–400 days | 400 days |
| API access | No | Yes |
| Calling Detailed Call History | 89 days | 400 days |

---

## Data Timing

- Timezone: **UTC**
- Delay: ~**8 hours** before prior-day data appears (~08:00 UTC)
- Same-day reports may contain partial data — generate in the afternoon
- Processing time: up to **24 hours** depending on size/queue
- File naming: `[Template Name]_[Alphanumeric]_[Download Date].csv`

---

## Meetings Reports

### 1. Meetings Usage Summary
- Total meetings, minutes, participants, video/VoIP/audio minutes
- Access: Standard + Pro Pack | History: 13 months

### 2. Meetings Details
- Per-meeting records: host, start/end, duration, attendees, recording status
- Tracks: E2EE, simultaneous interpretation, breakout sessions
- Telephony: local/intl toll, toll-free, callback, VoIP minutes
- Integrations: Teams, Outlook, Slack, Google Calendar scheduling tracked

### 3. Meetings Attendees
- Per-participant: join/leave times, device OS, browser, IP addresses, connection type
- Media quality: audio/video packet loss, jitter, latency (send + receive), CPU usage
- Hardware: camera, mic, speaker brand/model
- Geographic: country, state, city
- Quality fields: `VIDEO_QUALITY`, `VOIP_QUALITY` (Good/Bad/Unknown)
- Note: Media quality data only available for meetings > 2 minutes

### 4. Meetings In-Meeting Feature Usage
- Features tracked: recording, screen/app/doc share, chat, Q&A, captions, whiteboard, file transfer, annotation, virtual backgrounds, simultaneous translation, reactions, raised hand, Webex Assistant, real-time translation
- Requires: WBS 42.7+ client

### 5. Meetings Embedded Apps
- App name, usage frequency, participant engagement

### 6. Meetings High CPU
- Users averaging ≥90% CPU for ≥25% of video minutes
- Fields: user email, total video minutes, high CPU minutes, percentage
- Note: Webex auto-downgrades video at 95% CPU for 5 consecutive seconds

### 7. Meetings Active Hosts
- Count of meetings scheduled and started per host
- Fields: user ID/email, meeting count, host name

### 8. Meetings Inactive Users
- Users who haven't hosted or attended in the selected period
- Fields: name, email, user ID, license type, admin status, days since last activity
- Note: PSTN call-in users don't count as active

### 9. Meetings Audio Usage
- Audio type breakdown: CCA in/out, PSTN in/out, VoIP, Edge Audio, Fallback
- Fields: user names, phone numbers, audio minutes, meeting details

### 10. Meetings Telephony Report
- Session types: PSTN (5–9999), CCA (10000–20000), Edge Audio (>20000)
- Call types: callback domestic/intl, toll, toll-free, VoIP, premium toll
- Fields: dialed/callback numbers, ANI, duration, tracking codes

### 11. Meetings Future Schedules
- Upcoming meetings for the next 90 days + previous 30 days
- Use case: plan site migrations/upgrades
- Excludes: Personal Room invitation URLs
- Fields: meeting number, service type, host details, invitee count, recurrence info

### 12. Meetings License Consumption
- Availability: utility-based billing subscriptions only
- Fields: date period, subscription ID, product name, provisioned vs. allocated licenses
- Billing cycle: 30-day periods

### 13. Meetings Active User Rolling Average
- Availability: true forward eligible subscriptions only
- Metrics: unique active hosts/day, 30-day cumulative, 90-day rolling average, consumption qty

### 14. Enterprise Agreement Report
- Aggregate subscription and license tracking
- Access: Standard + Pro Pack

---

## Webinar Reports

### Webinar Report
- Fields: meeting/host ID, topic, type (Webinar/Webcast), host details, dates, duration, registrant count, attendee count
- Not available in Webex for Government

---

## Messaging Reports

### 1. Messaging User Activity (Daily)
- Per-user daily: messages sent, calls made, files shared, spaces count, spaces created/joined/exited
- Note: days with no activity are omitted

### 2. Messaging User Activity Summary (Period)
- Period-level rollup: totals for messages, calls, files, spaces
- Fields: user ID, name, email, start/end dates

### 3. Messaging Bots Activity (Daily)
- Org bots only (external bots excluded)
- Per-bot daily: active spaces, messages sent, files shared, spaces joined/exited, mention count

### 4. Messaging Bots Activity Summary (Period)
- Period-level: avg active spaces, total messages/files, spaces activity, mention averages
- Fields: bot owner identification

### 5. Messaging External Domain
- Tracks external collaboration in both directions:
  - External domains in your org's spaces
  - Your users in external spaces
- Fields: domain name, external user count, spaces with external users, last activity dates (read/sent/shared/joined)

---

## Webex Calling Reports

### 1. Calling Media Quality Report
- Scope: call legs with established media sessions
- Supported devices: Polycom, Yealink, AudioCodes (no analog phones / no IPv6)
- Quality threshold — "Good": jitter < 150ms, latency < 400ms, packet loss < 5%
- Metrics: audio/video jitter, packet loss, latency, codec, path optimization, video duration
- Fields: user, endpoint, device, call duration, caller indicator, UA version

### 2. Calling Engagement Report ⚠️ RETIRING Apr 28 2026
- Call leg data for Webex and Call on Webex usage
- Fields: name, email, start time, duration, video duration, endpoint, call ID, caller status

### 3. Calling Quality Report ⚠️ RETIRING Apr 28 2026
- Excludes cloud-registered devices
- Fields: audio/video packet loss, latency, jitter, duration, endpoint, UA version

### 4. Calling Detailed Call History
- Most comprehensive calling report — all Webex Calling activity
- Date range: Standard 89 days | Pro Pack 400 days | Max 31 days per query
- Field categories:
  - **Identifiers**: Start/answer times, duration, calling/called numbers, call type, call ID
  - **Routing**: Inbound/outbound trunks, route groups, direction (originating/terminating)
  - **User**: User type, client type, device model, OS
  - **Outcome**: Success/failure/refusal with reason codes
  - **Features**: Transfer, redirection reasons, authorization codes
  - **Network**: IP addresses, session IDs
- Call types: `SIP_MEETING`, `SIP_NATIONAL`, `SIP_INTERNATIONAL`, `SIP_SHORTCODE`, `SIP_INBOUND`, `SIP_EMERGENCY`, `SIP_PREMIUM`, `SIP_ENTERPRISE`, `SIP_TOLLFREE`, `SIP_MOBILE`, `SIP_URI`, `SIP_OPERATOR`, `SIP_CLICKTOCALL`
- Call outcomes: Success (Normal/UserBusy/NoAnswer), Failure, Refusal

### 5. Call Queue Stats
- Fields: queue name, location, phone number, hold/talk/handle/wait time (total + avg), answer rate, abandonment rate, overflow/timeout/transfer counts, agent assignments

### 6. Call Queue Agent Stats
- Per-agent: answered/presented/bounced calls, talk/hold/handle time
- Scope: agents, workspaces, virtual lines

### 7. Auto Attendant Reports (3 variants)
- **Stats Summary**: Total calls, answered, unanswered, busy, other, duration
- **Business Hours Key Details**: Key pressed, routing destination, answer rates by key
- **After-Hours Key Details**: Same metrics for after-hours

### 8. Hunt Group Stats
- Group-level: talk/handle/wait time, abandonment, answer rates, agent assignments

### 9. Hunt Group Agent Stats
- Agent-level: answered/presented calls, talk/handle time

### 10. Telephone Number Report
- Point-in-time snapshot of all numbers/extensions (no date range)
- Changes reflected within 24 hours
- Fields: location, country, phone number, extension, active status, user type, number type (primary/secondary), assigned user email, user UUID

---

## Webex App Reports

### Webex App Version Report ⚠️ RETIRING Apr 28 2026
- Last 90 days; per platform per user
- Fields: email, app type, platform (note: Apple machines may show as different model), latest version, last known date, installation ID

---

## Device Reports

### 1. Rooms and Desks Detail Report
- Device utilization and usage metrics
- Not available in Webex for Government

### 2. VIMT License Report
- Video Interoperability for third-party devices — license allocation and usage

### 3. VIMT Usage Report
- Device usage patterns and activity

### 4. Devices Power Consumption Report
- Energy consumption per device across the org
- Not available in Government orgs

---

## Onboarding Reports

### Onboarding User Activation and License Details
- User activation status and license allocation
- Access: Standard + Pro Pack | History: 13 months | Download: 31 days (Standard) / 92 days (Pro Pack)

---

## Report Management

- **Scheduling**: Immediate download or automated (daily/weekly/monthly) with email notification
- **Access Control**: Admin or authorized report generation users only
- **API**: Pro Pack required — Reports API + Report Templates API available
- **Tracking Codes**: Supported; shows default tracking code names only
