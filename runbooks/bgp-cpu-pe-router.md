# BGP + CPU + PE-Router

*Auto-generated from 3 incident(s), 2024-01-15 → 2024-11-06. Do not hand-edit above the manual notes section — it will be overwritten next time this pipeline runs.*

## Symptom signature
- bgp
- cpu
- cpu pe
- bgp cpu
- pe router
- router bgp
- Seen on: PE1-DEN, PE2-CHI, PE3-ATL

## Frequency
- 3 incident(s) matched this signature
- First seen: 2024-01-15
- Last seen: 2024-11-06

## Diagnostic steps seen across these incidents
- Checked `show bgp neighbors` — state repeatedly went from Established to Idle
- `show logging` revealed "BGP-3-NOTIFICATION: sent to neighbor ... Hold Timer Expired"
- CPU spike correlated with a route-map recompute after a large prefix withdrawal from upstream
- `show bgp neighbors` state repeatedly went from Established to Idle
- Found an inbound route-map with a similarly malformed match clause as a prior incident
- `show bgp neighbors` state flapping between Established and Idle
- `show logging` showed hold timer expiry notifications
- Same malformed route-map pattern found again, this time on PE4-ATL

## Root cause
- A malformed route-map on PE2-DEN was causing repeated recomputation of ~40k prefixes on every BGP update, spiking CPU and causing hold-timer expiry.
- Same class of issue as before: a route-map missing a `continue` clause caused full re-evaluation of the prefix table on every update, spiking CPU and tripping the BGP hold timer.
- Third occurrence of the same route-map defect (missing `continue` clause) — this template appears to have been pushed to multiple PE routers.

## Resolution steps that worked
- Fixed the route-map syntax error (missing `continue` clause causing an infinite matching loop)
- Verified CPU dropped to baseline and BGP session stabilized after 15 minutes
- Added a config audit ticket to check other PE routers for the same route-map pattern
- Fixed the route-map on PE4-ATL
- Escalated to Routing team to audit ALL PE routers for this template, per standing note in the runbook

## Source incidents
- `INC-1001` (2024-01-15, PE1-DEN) — `2024-01-15-inc-1001.md`
- `INC-1014` (2024-03-02, PE2-CHI) — `2024-03-02-inc-1014.md`
- `INC-1067` (2024-11-06, PE3-ATL) — `2024-11-06-inc-1067.md`

## Manual notes
*Anything you write between the two markers below survives the next auto-regeneration.*

<!-- MANUAL NOTES START -->
Escalate to the Routing team immediately if this hits a 3rd PE router — may indicate the bad route-map template got pushed org-wide.
<!-- MANUAL NOTES END -->
