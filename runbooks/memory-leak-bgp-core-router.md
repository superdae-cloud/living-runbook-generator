# Memory-LEAK + BGP + CORE-Router

*Auto-generated from 1 incident(s), 2024-09-28 → 2024-09-28. Do not hand-edit above the manual notes section — it will be overwritten next time this pipeline runs.*

## Symptom signature
- memory
- leak
- memory leak
- bgp
- leak bgp
- bgp core
- Seen on: CORE2-NYC

## Frequency
- 1 incident(s) matched this signature
- First seen: 2024-09-28
- Last seen: 2024-09-28

## Diagnostic steps seen across these incidents
- `show processes memory sorted` showed the BGP process's memory usage climbing steadily for weeks before the crash
- Vendor bug database matched a known memory-leak defect in the running IOS-XR version under heavy route-churn conditions
- No configuration error found — this was a software defect

## Likely root cause(s)
- Known vendor software defect causing a slow memory leak in the BGP process under sustained high route churn, eventually exhausting memory and forcing a process restart.

## Resolution steps that worked
- Opened a case with the vendor and applied the recommended patched image during the next maintenance window
- Added a monitoring alert for BGP process memory trending upward over multiple weeks

## Source incidents
- `INC-1052` (2024-09-28, CORE2-NYC) — `2024-09-28-inc-1052.md`

## Manual notes
*Anything you write between the two markers below survives the next auto-regeneration.*

<!-- MANUAL NOTES START -->
(add engineer notes here)
<!-- MANUAL NOTES END -->
