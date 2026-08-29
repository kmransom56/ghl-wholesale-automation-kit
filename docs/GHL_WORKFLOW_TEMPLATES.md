# GHL Workflow Templates

GHL-native automation workflows replacing Zapier. Point each webhook action at your deployed server base URL.

## Webhook Base URL

Replace `https://your-server.com` with your production host (e.g. `https://ghl-automation.netintegrate.net`).

| Endpoint | Path |
|----------|------|
| Quality score | `/api/webhooks/calculate-score` |
| 70% rule | `/api/webhooks/seventy-percent-rule` |
| Investor matching | `/api/webhooks/find-matches` |
| Post-close stats | `/api/webhooks/update-investor-stats` |
| DealDriven sync (manual) | `/api/manual/sync-dealdriven` |
| Process deal (manual) | `/api/manual/process-deal` |

---

## Workflow 1: Investor Quality Qualification

**Trigger:** Contact Created (tag: `investor` optional)

1. **Webhook — Calculate Score**
   - URL: `https://your-server.com/api/webhooks/calculate-score`
   - Method: POST
   - Body:
   ```json
   {
     "contactId": "{{contact.id}}",
     "cash_available": "{{contact.cash_available}}",
     "deals_per_year": "{{contact.deals_per_year}}",
     "min_property_price": "{{contact.min_property_price}}",
     "max_property_price": "{{contact.max_property_price}}"
   }
   ```
2. **Update Custom Field:** `Investor_Quality_Score` = response `qualityScore`
3. **Update Custom Field:** `Investor_Tier` = response `tier`
4. **If** `qualityScore` ≥ 75 → add tag `qualified`, else tag `review-needed`

---

## Workflow 2: Wholesale Deal Matching

**Trigger:** Custom field changed (`deal_arv` or `New_Property`)

1. **Webhook — 70% Rule**
   - URL: `https://your-server.com/api/webhooks/seventy-percent-rule`
   - Body: `after_repair_value`, `repair_costs`, `current_asking_price`, `contactId`
2. **Webhook — Find Matches**
   - URL: `https://your-server.com/api/webhooks/find-matches`
   - Body: `propertyPrice`, `repair_costs`, `minScore` (75), `location`, `property_type`
3. **For each** matched investor → send SMS/email with ARV, repairs, max offer, profit
4. **Create opportunity** in Wholesale Deals pipeline

---

## Workflow 3: Post-Close Enrollment

**Trigger:** Opportunity status = Closed Won

1. **Webhook — Update Investor Stats**
   - URL: `https://your-server.com/api/webhooks/update-investor-stats`
   - Body: `contactId`, `dealAmount`
2. **Update** `Investor_Tier` from response
3. **Enroll** in Post-Close Nurture sequence (Day 1 / 7 / 14 messages)

---

## Custom Fields (run once)

```bash
python ghl_custom_fields.py
```

Creates: `Investor_Quality_Score`, `Investor_Tier`, `Property_Match_Score`

---

## Testing Checklist

- [ ] `/health` returns `{"status":"healthy"}`
- [ ] New investor contact receives quality score and tier
- [ ] Property added triggers 70% rule + match list
- [ ] Closed deal updates investor tier
- [ ] DealDriven sync: `POST /api/manual/sync-dealdriven` with credentials
