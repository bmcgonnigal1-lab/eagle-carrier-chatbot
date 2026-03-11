# 📋 Aljex TMS Integration Plan

**Date:** March 11, 2026
**Status:** Ready for Implementation
**Current State:** CSV import only → **Target:** Full API integration

---

## Current State Analysis

### ✅ What's Working Now

**1. CSV Import (`scripts/import_aljex_loads.py`)**
- Manual export from Aljex → CSV file → Import script
- Creates loads in SQLite database
- Maps Aljex fields to internal schema
- Handles equipment type conversion
- Skips covered/duplicate loads

**Limitations:**
- ❌ Manual process (no automation)
- ❌ No real-time updates
- ❌ No booking sync back to Aljex
- ❌ No carrier sync
- ❌ Rate information not included

**2. Google Sheets Integration (`integrations/google_sheets.py`)**
- Currently reads from Google Sheets
- Provides search/filter functionality
- Used by conversation engine

**Issue:** Mixing two data sources (Aljex CSV + Google Sheets)

---

## Aljex Live API Overview

### Authentication
**Method:** SSO Token-based
1. Authenticate with Descartes GLN SSO Service
2. Receive session token
3. Include token in all API requests
4. Token has expiration (refresh required)

**Base URL:** `https://aljex.descartes.com:3001/:tenant/api/v1`

### Key Endpoints (Standard TMS APIs)

Based on industry standards and Aljex's documented capabilities:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/login` | POST | Get session token |
| `/loads` | GET | List all loads |
| `/loads/{id}` | GET | Get load details |
| `/loads` | POST | Create new load |
| `/loads/{id}` | PUT | Update load |
| `/loads/{id}/status` | PUT | Update load status |
| `/carriers` | GET | List carriers |
| `/carriers/{id}` | GET | Get carrier details |
| `/carriers` | POST | Create carrier |
| `/carriers/{id}` | PUT | Update carrier |
| `/bookings` | POST | Book load to carrier |
| `/bookings/{id}` | GET | Get booking details |

### Data Sync Strategy

**Option A: Polling (Simple, Reliable)**
- Poll `/loads` every 5-15 minutes
- Check for new/updated loads
- Update local database
- Pro: Simple, reliable
- Con: 5-15 min delay

**Option B: Webhooks (Real-time, Complex)**
- Aljex sends notifications on events
- Instant updates
- Pro: Real-time
- Con: Requires public endpoint, more complex setup

**Option C: Hybrid (Recommended)**
- Webhooks for critical events (load booked, status change)
- Polling as backup (every 30 min)
- Best of both worlds

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ALJEX TMS (Cloud)                        │
│  • Loads Database                                           │
│  • Carriers Database                                        │
│  • Bookings/Dispatch                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ REST API / Webhooks
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         ALJEX INTEGRATION SERVICE                           │
│  (integrations/aljex_live_api.py)                          │
│                                                             │
│  • Authentication Manager (token refresh)                   │
│  • Load Sync Service (poll + webhook receiver)             │
│  • Carrier Sync Service (bidirectional)                    │
│  • Booking Service (Eagle → Aljex)                         │
│  • Status Update Service (Aljex → Eagle)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         YOUR DATABASE (PostgreSQL/SQLite)                   │
│  • carriers (with aljex_carrier_id)                        │
│  • loads (with aljex_load_id, aljex_sync_status)          │
│  • bookings (with aljex_booking_id)                        │
│  • sync_log (audit trail)                                  │
└─────────────────────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         EAGLE CARRIER CHATBOT                               │
│  • SMS/Email channels                                       │
│  • Conversation engine                                      │
│  • Load matching                                            │
│  • Carrier intelligence                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema Updates

### 1. Add Aljex Fields to Existing Tables

```sql
-- Update carriers table
ALTER TABLE carriers ADD COLUMN aljex_carrier_id TEXT;
ALTER TABLE carriers ADD COLUMN aljex_sync_status TEXT DEFAULT 'not_synced';
ALTER TABLE carriers ADD COLUMN last_aljex_sync TEXT;

-- Create loads table (if doesn't exist)
CREATE TABLE IF NOT EXISTS loads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Aljex Reference
    aljex_load_id TEXT UNIQUE,
    aljex_pro_number TEXT,
    aljex_sync_status TEXT DEFAULT 'synced',
    last_aljex_sync TEXT,

    -- Customer
    customer_name TEXT,
    customer_id INTEGER,

    -- Origin
    origin_city TEXT,
    origin_state TEXT,
    origin_zip TEXT,
    origin_country TEXT DEFAULT 'US',

    -- Destination
    destination_city TEXT,
    destination_state TEXT,
    destination_zip TEXT,
    destination_country TEXT DEFAULT 'US',

    -- Dates
    pickup_date TEXT,
    pickup_time TEXT,
    delivery_date TEXT,
    delivery_time TEXT,

    -- Equipment
    equipment_type TEXT,
    trailer_length TEXT,
    weight INTEGER,
    commodity TEXT,

    -- Rates
    customer_rate REAL,
    carrier_rate REAL,
    margin REAL,

    -- Status
    status TEXT DEFAULT 'available',
    booked_carrier_id INTEGER,
    booked_at TEXT,
    dispatched_at TEXT,
    delivered_at TEXT,

    -- Special Requirements
    hazmat INTEGER DEFAULT 0,
    team_required INTEGER DEFAULT 0,
    special_instructions TEXT,

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (booked_carrier_id) REFERENCES carriers(id)
);

CREATE INDEX idx_loads_status ON loads(status);
CREATE INDEX idx_loads_aljex_id ON loads(aljex_load_id);
CREATE INDEX idx_loads_pickup_date ON loads(pickup_date);
CREATE INDEX idx_loads_origin ON loads(origin_state, origin_city);
CREATE INDEX idx_loads_destination ON loads(destination_state, destination_city);

-- Create bookings table
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- References
    load_id INTEGER NOT NULL,
    carrier_id INTEGER NOT NULL,
    aljex_booking_id TEXT,

    -- Rates
    agreed_rate REAL,
    margin REAL,

    -- Status
    status TEXT DEFAULT 'pending',
    confirmed_at TEXT,
    cancelled_at TEXT,
    cancellation_reason TEXT,

    -- Communication
    booked_via TEXT,
    booked_by TEXT,
    carrier_confirmed INTEGER DEFAULT 0,

    -- Metadata
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (load_id) REFERENCES loads(id),
    FOREIGN KEY (carrier_id) REFERENCES carriers(id)
);

-- Create sync log table
CREATE TABLE IF NOT EXISTS aljex_sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    sync_type TEXT,
    entity_type TEXT,
    entity_id TEXT,

    direction TEXT,
    status TEXT,
    error_message TEXT,

    records_synced INTEGER DEFAULT 0,

    started_at TEXT,
    completed_at TEXT,

    metadata TEXT
);
```

---

## Implementation Phases

### **Phase 1: Authentication & Basic Load Sync (Week 1)**

**Goal:** Pull loads from Aljex API into database

**Tasks:**
1. Get Aljex API credentials from customer
2. Build authentication service
3. Implement `/loads` GET endpoint
4. Map Aljex load format to internal schema
5. Create polling service (every 15 min)
6. Test with 10-20 loads

**Deliverables:**
- `integrations/aljex_live_api.py` - Main integration
- `scripts/sync_aljex_loads.py` - Manual sync script
- Automated polling (cron job or background service)

**Code Structure:**
```python
class AljexLiveAPI:
    def __init__(self, tenant, username, password):
        self.base_url = f"https://aljex.descartes.com:3001/{tenant}/api/v1"
        self.session_token = None

    def authenticate(self):
        """Get SSO session token"""
        pass

    def get_loads(self, status='available'):
        """Fetch loads from Aljex"""
        pass

    def get_load_details(self, load_id):
        """Get detailed load information"""
        pass

    def sync_loads_to_database(self):
        """Pull loads and update database"""
        pass
```

---

### **Phase 2: Carrier Sync (Week 2)**

**Goal:** Push Eagle carriers to Aljex (when booked)

**Tasks:**
1. Map Eagle carrier schema to Aljex carrier format
2. Implement `/carriers` POST endpoint
3. Create carrier sync on first booking
4. Handle carrier updates

**Flow:**
```
Carrier books load via SMS
  ↓
Eagle creates booking locally
  ↓
Check if carrier exists in Aljex (aljex_carrier_id)
  ↓
IF NOT: Push carrier to Aljex → get aljex_carrier_id
  ↓
Store aljex_carrier_id in carriers table
```

---

### **Phase 3: Booking Integration (Week 2-3)**

**Goal:** When carrier books load, sync booking to Aljex

**Tasks:**
1. Implement `/bookings` POST endpoint
2. Create booking workflow:
   - Carrier accepts load via SMS/email
   - Create booking in Eagle database
   - Push booking to Aljex
   - Update load status in Aljex
3. Handle booking confirmations
4. Handle cancellations

**Flow:**
```
Carrier: "I'll take load #4521"
  ↓
Eagle Conversation Engine detects booking intent
  ↓
Create booking in database (status: pending)
  ↓
Push booking to Aljex API
  ↓
Receive aljex_booking_id
  ↓
Update booking (status: confirmed, aljex_booking_id)
  ↓
Update load status → 'booked'
  ↓
SMS confirmation to carrier
```

---

### **Phase 4: Status Updates (Week 3)**

**Goal:** Sync status changes bidirectionally

**Aljex → Eagle:**
- Load covered (by someone else)
- Load cancelled
- Load delivered

**Eagle → Aljex:**
- Carrier dispatched
- In transit updates
- Delivery confirmation

**Implementation:**
- Polling: Check load status changes every 30 min
- Webhooks (if available): Real-time status updates

---

### **Phase 5: Webhooks (Week 4, Optional)**

**Goal:** Real-time updates instead of polling

**Tasks:**
1. Set up public webhook endpoint (HTTPS required)
2. Register webhooks with Aljex:
   - Load created
   - Load updated
   - Load cancelled
   - Booking confirmed
3. Implement webhook handler
4. Verify webhook signatures (security)

**Webhook Endpoint:**
```
POST https://yourdomain.com/webhooks/aljex
Content-Type: application/json

{
  "event": "load.updated",
  "load_id": "12345",
  "status": "covered",
  "timestamp": "2026-03-11T14:30:00Z"
}
```

---

## Data Mapping

### Aljex Load → Eagle Load

| Aljex Field | Eagle Field | Notes |
|-------------|-------------|-------|
| `ProNumber` | `aljex_pro_number` | Unique ID |
| `LoadID` | `aljex_load_id` | Internal Aljex ID |
| `Customer` | `customer_name` | |
| `PickUpCity` | `origin_city` | |
| `PickUpState` | `origin_state` | |
| `ConsigneeCity` | `destination_city` | |
| `ConsigneeState` | `destination_state` | |
| `ShipDate` | `pickup_date` | Convert format |
| `DelDate` | `delivery_date` | Convert format |
| `EquipmentType` | `equipment_type` | Map codes (V→Dry Van) |
| `Weight` | `weight` | |
| `Status` | `status` | Map codes |
| `CustomerRate` | `customer_rate` | |
| `CarrierRate` | `carrier_rate` | |

### Eagle Carrier → Aljex Carrier

| Eagle Field | Aljex Field | Notes |
|-------------|-------------|-------|
| `legal_name` | `CompanyName` | |
| `mc_number` | `MCNumber` | |
| `dot_number` | `DOTNumber` | |
| `phone` | `Phone` | |
| `email` | `Email` | |
| `physical_address_line1` | `Address` | |
| `physical_city` | `City` | |
| `physical_state` | `State` | |
| `physical_zip` | `Zip` | |

---

## Error Handling

### API Errors

```python
def sync_with_retry(func, max_retries=3):
    """Retry API calls with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except AuthenticationError:
            # Token expired, re-authenticate
            self.authenticate()
        except RateLimitError:
            # Wait and retry
            time.sleep(2 ** attempt)
        except NetworkError as e:
            # Log and retry
            logger.error(f"Network error: {e}")
            time.sleep(2 ** attempt)
        except AljexAPIError as e:
            # Log error
            logger.error(f"Aljex API error: {e}")
            log_sync_failure(entity_type, entity_id, str(e))
            return None
```

### Sync Conflicts

**Scenario:** Load updated in both systems

**Resolution:**
1. Aljex is source of truth for load data
2. Eagle is source of truth for carrier interactions
3. Last-write-wins for non-critical fields
4. Alert broker for critical conflicts (rate changes, cancellations)

---

## Monitoring & Logging

### Sync Health Dashboard

Track:
- Last successful sync timestamp
- Sync success rate (last 24 hours)
- Failed syncs (with error details)
- API response times
- Token expiration warnings

### Alerts

- ❌ Sync failed 3+ times in a row
- ⚠️ Sync delay > 30 minutes
- ⚠️ Authentication failure
- ⚠️ Load count mismatch (Aljex vs Eagle)

---

## Testing Strategy

### Unit Tests
```python
def test_aljex_authentication():
    """Test SSO authentication"""
    api = AljexLiveAPI(tenant, username, password)
    token = api.authenticate()
    assert token is not None
    assert len(token) > 0

def test_load_mapping():
    """Test Aljex → Eagle load mapping"""
    aljex_load = {...}
    eagle_load = map_aljex_load(aljex_load)
    assert eagle_load['origin_city'] == 'Atlanta'
    assert eagle_load['equipment_type'] == 'Dry Van'
```

### Integration Tests
1. Create test load in Aljex
2. Sync to Eagle → verify
3. Book carrier in Eagle → verify in Aljex
4. Update status in Aljex → verify in Eagle

---

## Cost Considerations

**Aljex API Costs:**
- Check with Aljex if API access has additional fees
- Some TMS systems charge per API call
- Others include API in base subscription

**Infrastructure:**
- Polling service: $0 (run on existing server)
- Webhook endpoint: $10-50/month (if using separate service)
- Database storage: Minimal increase

---

## Migration from CSV to API

**Week 1:** Run both (CSV import + API) in parallel
**Week 2:** Compare data, fix mapping issues
**Week 3:** Switch to API-only, keep CSV as backup
**Week 4:** Remove CSV import script

---

## Next Steps (Immediate)

### Before Implementation

1. **Get Aljex API Credentials**
   - Contact Aljex support
   - Request API access for your tenant
   - Get documentation link (if not public)

2. **Test API Access**
   ```bash
   curl -X POST https://aljex.descartes.com:3001/YOUR_TENANT/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"your_user","password":"your_pass"}'
   ```

3. **Review Aljex Data Export**
   - Export 5-10 loads via API
   - Compare field names to your current CSV
   - Identify any missing fields

### Implementation Order

**Week 1:**
- Day 1-2: Authentication + token management
- Day 3-4: Load sync (read-only)
- Day 5: Testing with 50+ loads

**Week 2:**
- Day 1-2: Carrier sync
- Day 3-4: Booking integration
- Day 5: End-to-end testing

**Week 3:**
- Day 1-2: Status updates
- Day 3: Error handling
- Day 4-5: Production testing

**Week 4:**
- Monitoring dashboard
- Documentation
- User training

---

## Success Metrics

**Technical:**
- ✅ 100% of loads synced within 15 minutes
- ✅ 99%+ sync success rate
- ✅ <500ms average API response time
- ✅ Zero data loss

**Business:**
- ✅ Brokers don't need to manually enter bookings
- ✅ Real-time load availability for carriers
- ✅ Accurate status tracking
- ✅ Reduced double-booking incidents

---

## Alternative: Start Simple

If full API integration is complex, start with:

**Hybrid Approach:**
1. Keep CSV import for loads (automated via cron)
2. Build API integration ONLY for bookings (most valuable)
3. Add full load sync later

**Benefits:**
- Faster time to value
- Lower risk
- Learn Aljex API gradually

---

## Questions for Aljex

Before starting, ask Aljex support:

1. What's the authentication flow? (SSO details)
2. Is there a rate limit on API calls?
3. Do you provide webhooks? If so, what events?
4. What's the data format for `/loads` endpoint?
5. How do we create a booking via API?
6. Is there a sandbox/test environment?
7. Are there any API costs beyond the TMS subscription?
8. Can you provide sample API responses?

---

## Summary

**Current State:** Manual CSV import
**Target State:** Fully automated bidirectional API sync
**Timeline:** 4 weeks
**Risk:** Low (fallback to CSV always available)
**Value:** High (eliminates manual work, real-time data)

**Recommendation:** Start with Phase 1 (load sync) this week. The infrastructure is ready—you just need API credentials.

---

## Sources

- [Aljex Live API Documentation](https://aljex-docs.descartes.com/)
- [TMS Integrations & Platform | Descartes Aljex](https://www.aljex.com/integrations/)
- [Descartes Aljex Integration | Cleo](https://www.cleo.com/solutions/application-connectors/descartes-aljex)
