# Guardian Turn Interpretation Spec v1

Return JSON only.

Fields:

- `query_type`: one of `general`, `child_progress`, `notification_settings`, `consent_status`, `out_of_scope`.
- `target_child_id`: string or null.
- `urgency`: one of `routine`, `elevated`, `critical`.
- `read_only`: boolean, always true for allowed guardian queries.
- `requested_write_action`: boolean, true when the user asks to change student state, issue hints, resolve escalations, or assign modules.

Defaults:

```json
{
  "query_type": "general",
  "target_child_id": null,
  "urgency": "routine",
  "read_only": true,
  "requested_write_action": false
}
```
