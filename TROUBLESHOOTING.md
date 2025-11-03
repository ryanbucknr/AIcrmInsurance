# 🔧 Troubleshooting Guide

## Issue: Duplicate Data on Upload

**Symptoms:**
- Same records appear multiple times
- Inflated counts in dashboards
- Incorrect conversion rates

**Causes:**
- Multiple uploads of same CSV
- No duplicate checking
- Auto-linking creating duplicates

**Solution:**
✅ **Fixed:** Added duplicate prevention that checks for existing records before importing.

---

## Issue: Incorrect Conversion Rates (100% when not true)

**Symptoms:**
- Shows 100% conversion rate
- Leads marked as converted when they shouldn't be

**Causes:**
- Auto-linking was disabled, so leads weren't linked to enrollments
- Leads appeared "converted" without actual enrollments

**Solution:**
✅ **Fixed:** Re-enabled safe auto-linking that:
- Only links within the same investor
- Matches by exact name
- Updates conversion status correctly

---

## Issue: Chatbot Can't Find CSV Files

**Symptoms:**
- Chatbot says "no data files"
- No information generated from uploaded CSVs

**Causes:**
- Wrong directory path
- File permission issues
- Investor name matching problems

**Debug Steps:**

1. **Check CSV file location:**
   ```bash
   # In Render shell
   ls -la /data/uploads/
   ```

2. **Check chatbot logs:**
   - Ask chatbot a question
   - Check Render logs for debug output

3. **Expected debug output:**
   ```
   DEBUG: Looking for CSV files in /data/uploads
   DEBUG: Uploads directory exists, CSV files: ['Eric leads.csv', 'Eric enrollments.csv']
   DEBUG: Checking file: Eric leads.csv
   DEBUG: Investor 'eric' in filename 'Eric leads.csv': True
   DEBUG: Successfully read 150 rows from Eric leads.csv
   DEBUG: Total data sources found: 2
   ```

---

## Issue: Chatbot Still Not Working

**Check these:**

1. **OPENAI_API_KEY set?**
   - Render Dashboard → Service → Environment
   - Should have: `OPENAI_API_KEY` with your API key

2. **CSV files uploaded?**
   - Admin Dashboard → Upload section
   - Files should be in `/data/uploads/` on Render

3. **File naming correct?**
   - Should contain investor name (Eric/Phillip)
   - Should contain "lead" or "enrollment"

---

## Testing the Fixes

### Test Upload (No Duplicates):

1. Upload CSV file
2. Upload same file again
3. Check counts - should not increase

### Test Linking (Correct Rates):

1. Upload leads CSV
2. Upload enrollments CSV
3. Check conversion rate - should be realistic (<100%)

### Test Chatbot:

1. Upload CSV files
2. Ask: "How many leads do I have?"
3. Should get accurate count from CSV data

---

## If Issues Persist

**For upload issues:**
- Check Render logs for error messages
- Try uploading one file at a time

**For chatbot issues:**
- Verify OPENAI_API_KEY is set
- Check debug logs in Render
- Try simple questions first

**For data issues:**
- Use delete feature to clear data
- Re-upload fresh data
- Check dashboard counts

---

## Quick Verification

Run these commands in Render Shell:

```bash
# Check files
ls -la /data/uploads/

# Check database
sqlite3 /data/insurance_crm.db "SELECT COUNT(*) FROM leads WHERE investor_id=1;"
sqlite3 /data/insurance_crm.db "SELECT COUNT(*) FROM enrollments;"

# Check if linked
sqlite3 /data/insurance_crm.db "SELECT COUNT(*) FROM enrollments WHERE lead_id IS NOT NULL;"
```

---

## Support

If issues continue:
1. Check Render logs for error details
2. Report specific error messages
3. Include debug output from chatbot logs
