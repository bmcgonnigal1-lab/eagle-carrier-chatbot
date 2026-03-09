# Eagle Carrier Chatbot - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     EAGLE CARRIER CHATBOT                    │
└─────────────────────────────────────────────────────────────┘

         CARRIER                        EAGLE TEAM
            │                                │
            │ SMS                            │
            ▼                                ▼
    ┌──────────────┐              ┌──────────────────┐
    │   TWILIO     │              │  DISPATCH ALERTS │
    │  (SMS API)   │              │  (Booking Reqs)  │
    └──────┬───────┘              └────────▲─────────┘
           │                               │
           │ Webhook                       │
           ▼                               │
    ┌─────────────────────────────────────┴─────────┐
    │          CARRIER CHATBOT (Python)             │
    │                                                │
    │  ┌───────────────┐  ┌────────────────────┐   │
    │  │  AI ENGINE    │  │   GOOGLE SHEETS    │   │
    │  │  (OpenAI or   │  │   (Load Data)      │   │
    │  │   Regex)      │  └────────────────────┘   │
    │  └───────────────┘                            │
    │                                                │
    │  ┌──────────────────────────────────────┐    │
    │  │      SQLITE DATABASE                 │    │
    │  │  - Carrier Profiles                  │    │
    │  │  - Query Logs                        │    │
    │  │  - Intelligence Data                 │    │
    │  └──────────────────────────────────────┘    │
    └────────────────────────────────────────────┘
```

## Data Flow

### 1. Carrier Sends SMS
```
Carrier: "Atlanta to Dallas dry van"
   ↓
Twilio receives SMS
   ↓
Webhook → Chatbot
```

### 2. Chatbot Processes
```
Extract phone: +14045551234
   ↓
Check database: Is carrier known?
   ↓
AI parses message:
  - Intent: search_loads
  - Origin: ATL
  - Destination: DAL
  - Equipment: Dry Van
```

### 3. Search Loads
```
Query Google Sheets:
  - Filter: origin=ATL AND dest=DAL AND equipment=Dry Van
   ↓
Found: 2 matching loads
```

### 4. Generate Response
```
AI formats response:
  - SMS format (short & scannable)
  - Include load IDs, rates, special instructions
   ↓
Send via Twilio
```

### 5. Log Intelligence
```
Save to database:
  - Carrier searched ATL→DAL dry van
  - Showed 2 loads
  - Response time: 1.2 seconds
   ↓
Update carrier profile:
  - Add "ATL→DAL" to preferred lanes
  - Increment query count
  - Update last active date
```

## File Structure

```
eagle-carrier-chatbot/
│
├── app/
│   ├── main.py              # Main orchestrator
│   ├── database.py          # SQLite database functions
│   └── ai_engine.py         # AI conversation handler
│
├── channels/
│   └── sms.py               # Twilio SMS integration
│
├── integrations/
│   └── google_sheets.py     # Google Sheets loader
│
├── scripts/
│   ├── test_chatbot.py      # Interactive testing
│   └── import_aljex_carriers.py  # Import carriers
│
├── config.example.py        # Configuration template
├── requirements.txt         # Python dependencies
│
├── QUICK_START.md          # 2-minute test guide
├── SETUP.md                # Full setup guide
└── README.md               # Overview
```

## Key Components

### Database (SQLite)
- **carriers** - Carrier profiles, engagement metrics
- **carrier_queries** - Every interaction logged
- **booking_requests** - Booking attempts tracked

### AI Engine
- **Parse Mode 1:** OpenAI (smart, costs $20/mo)
- **Parse Mode 2:** Regex (free, works great for common queries)
- **Generate:** Creates conversational responses

### Google Sheets
- **Real-time:** Reads current load data
- **No sync lag:** Instant updates when you change loads
- **Simple:** Just a spreadsheet, easy to manage

### SMS Channel (Twilio)
- **Receive:** Webhook endpoint for incoming SMS
- **Send:** Twilio API for outbound responses
- **Security:** US/Canada only, rate limiting

## Intelligence System

### What We Track
1. **Carrier Queries** - Every search logged
2. **Lane Patterns** - Which lanes each carrier prefers
3. **Equipment Types** - What equipment they search for
4. **Timing Patterns** - When they're typically available
5. **Response Speed** - How fast they reply
6. **Booking History** - What they book vs. what they search

### What We Learn
- Carrier A always searches ATL→DAL on Mondays
- Carrier B prefers dry van, 53', over $2,000
- Carrier C responds in <5 min (reliable)
- Carrier D searches often but never books (tire kicker?)

### How We Use It
- **Smart Matching:** Offer loads to carriers who want them
- **Proactive Alerts:** Text carriers when their preferred loads arrive
- **Efficiency:** Don't waste time offering wrong loads
- **Growth:** Identify which carriers to cultivate

## Phase 1 vs. Future Phases

### ✅ Phase 1 (What You Have Now)
- SMS communication
- Load search and filtering
- Carrier tracking
- Natural language understanding
- Google Sheets integration
- Aljex carrier import
- Intelligence logging

### 🔜 Phase 2 (Next Week)
- Email channel (Microsoft Graph)
- Web server deployment
- Dashboard for viewing intelligence
- Automated carrier matching
- Pattern detection alerts

### 🔮 Phase 3 (Week 3+)
- Proactive carrier engagement
- Automated load offers
- Advanced analytics
- API for TMS integration
- Mobile app (optional)

## Costs

### Phase 1 (Minimal)
- Twilio: ~$25/month (phone + SMS)
- OpenAI: ~$20/month (optional)
- Google Sheets: Free
- **Total: $25-45/month**

### vs. Alternatives
- Parade: $2,000-4,000/month
- Uber Freight: $1,500-3,000/month
- Custom build from scratch: $10,000-50,000

**Your savings: $23,000-47,000/year** 💰

## Security

- ✅ US/Canada phone numbers only
- ✅ Rate limiting (20 messages/hour)
- ✅ Database for audit trail
- ✅ No carrier can see other carriers' data
- ✅ Fraud pattern detection (future)

---

**Built for Eagle Transportation Services, Inc.**
Let's soar! 🦅
