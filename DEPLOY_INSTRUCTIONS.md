# 🚀 Deployment Instructions

Your clean repository is ready to deploy!

## Files Ready

All essential files are in place:
- ✅ `app.py` - Main application (imports updated)
- ✅ `auth.py` - Authentication (imports updated)
- ✅ `database.py` - Database manager
- ✅ `chatbot.py` - AI features (optional)
- ✅ `requirements.txt` - Dependencies
- ✅ `Procfile` - Deployment config (`gunicorn app:app`)
- ✅ `runtime.txt` - Python version
- ✅ `.gitignore` - Git ignore rules
- ✅ `README.md` - Documentation
- ✅ `templates/` - All HTML templates renamed
- ✅ `static/` - CSS and JS files

## Quick Deploy Steps

### 1. Initialize Git

```bash
cd /Users/ryanbuckner/insurance-portal-clean
git init
git add .
git commit -m "Initial clean repository"
```

### 2. Create GitHub Repo

1. Go to github.com → New Repository
2. Name: `insurance-investor-portal` (or your choice)
3. **Private** (recommended)
4. **Don't** initialize with README
5. Create repository

### 3. Push to GitHub

```bash
git remote add origin https://github.com/YOUR-USERNAME/insurance-investor-portal.git
git branch -M main
git push -u origin main
```

### 4. Deploy to Render

1. Go to **render.com** → New Web Service
2. Connect GitHub → Select your repo
3. **Settings:**
   - Name: `investor-portal`
   - Build Command: `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app` ⚠️ **IMPORTANT!**
   - Plan: Free

4. **Add Persistent Disk** (CRITICAL):
   - Go to Settings → Disks
   - Add Disk:
     - Name: `investor-data`
     - Mount: `/data`
     - Size: `1GB`
   - Click Create

5. **Environment Variables:**
   - `SECRET_KEY` = (generate: `python3 -c "import secrets; print(secrets.token_hex(32))"`)
   - `FLASK_ENV` = `production`
   - `OPENAI_API_KEY` = (optional, your OpenAI key)

6. **Create Web Service**

7. Wait 2-3 minutes for deployment

### 5. Verify

1. Visit your URL: `https://your-app.onrender.com`
2. Login as admin: `admin` / `admin123`
3. Check that auto-setup ran (check Render logs)
4. Upload test data via Admin Dashboard

## What Happens on First Run

✅ Auto-creates investors (Eric, Phillip)  
✅ Auto-creates user accounts  
✅ Auto-creates database tables  
✅ Ready to upload data!

## Test Locally First (Optional)

```bash
cd /Users/ryanbuckner/insurance-portal-clean
pip install -r requirements.txt
python app.py
```

Visit: http://localhost:5002

---

## All Set! 🎉

Your clean repository is ready to push and deploy. Everything has been updated with correct imports and file names.

