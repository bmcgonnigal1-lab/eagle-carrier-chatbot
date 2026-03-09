# Eagle Carrier Chatbot - Quick Start

## Test It RIGHT NOW (2 minutes)

No API keys needed! Test with sample data.

### Mac/Linux:
```bash
# 1. Open Terminal

# 2. Navigate to the folder
cd ~/Downloads/eagle-carrier-chatbot

# 3. Run the test script
./run_test.sh
```

### Windows:
```bash
# 1. Open Command Prompt

# 2. Navigate to the folder
cd Downloads\eagle-carrier-chatbot

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run test
python scripts\test_chatbot.py
```

## What You'll See

```
🦅 EAGLE CARRIER CHATBOT - INTERACTIVE TEST

✓ Database initialized
✓ Using mock SMS (no Twilio connection)
✓ Using mock data (no Google Sheets connection)
✅ Eagle Carrier Chatbot initialized!

Test the chatbot! Type carrier messages below.

Examples:
  - Atlanta loads
  - Atlanta to Dallas dry van
  - Book L12345
  - Miami reefer

📱 Carrier message: _
```

## Try These Commands

| Type This | What Happens |
|-----------|-------------|
| `Atlanta loads` | Shows all loads from Atlanta |
| `Atlanta to Dallas` | Shows ATL→DAL loads |
| `dry van loads` | Shows only dry van equipment |
| `Atlanta to Dallas dry van` | Combines all filters |
| `Book L12345` | Creates booking request |

## What's Working?

✅ **SMS conversation engine** - Understands natural language
✅ **Load searching** - Filters by origin, destination, equipment
✅ **Carrier tracking** - Logs every query in database
✅ **Booking requests** - Alerts dispatch
✅ **Eagle branding** - Company name, dispatch phone

## What's Next?

Once you test and it works:

1. **Add Twilio** (real SMS) - See SETUP.md Step 2
2. **Add Google Sheets** (your loads) - See SETUP.md Step 3
3. **Import Aljex carriers** - See SETUP.md Step 5
4. **Deploy for production** - Coming in Phase 2

## Need Help?

- **Full setup guide:** See SETUP.md
- **Code questions:** All files are commented
- **Stuck?** Check the code - it's designed to be readable!

---

**Let's get Eagle flying! 🦅**
