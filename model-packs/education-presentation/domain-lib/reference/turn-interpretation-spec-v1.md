# Turn Interpretation Schema - Education Presentation

**Domain:** education-presentation  
**Version:** 0.1.0

The interpreter emits a small evidence object for presentation-reference requests.
This pack is cosmetic only, so any request that attempts to alter department
logic, escalation policy, or consent boundaries must be surfaced as evidence for
boundary handling.

## Output Fields

```json
{
  "on_track": true,
  "response_latency_sec": 5.0,
  "off_task_ratio": 0.0,
  "logic_override_attempted": false,
  "consent_boundary_obscured": false
}
```

## Field Notes

- `on_track`: true when the request concerns presentation/world-sim reference material.
- `logic_override_attempted`: true when the request attempts to change curriculum, state transition, standing-order, or escalation behavior from the presentation pack.
- `consent_boundary_obscured`: true when the request attempts to hide, skip, or weaken consent boundaries.
