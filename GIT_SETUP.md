# 🔧 Git Setup Guide

## Step 1: Initialize Git Repository

Git has been initialized! ✅

## Step 2: Create GitHub Repository

Before pushing, create a new empty repository on GitHub:

1. Go to **github.com** and sign in
2. Click the **"+"** icon (top right) → **"New repository"**
3. Fill in:
   - **Repository name:** `insurance-investor-portal` (or your choice)
   - **Description:** "Insurance CRM Investor Portal"
   - **Visibility:** Private (recommended) or Public
   - **⚠️ IMPORTANT:** Do NOT initialize with README, .gitignore, or license
4. Click **"Create repository"**

## Step 3: Add Files and Commit

Run these commands:

```bash
cd /Users/ryanbuckner/insurance-portal-clean

# Add all files
git add .

# Check what will be committed
git status

# Commit the files
git commit -m "Initial clean repository"
```

## Step 4: Connect to GitHub

After creating the GitHub repo, copy the repository URL (it will look like):
```
https://github.com/YOUR-USERNAME/insurance-investor-portal.git
```

Then run:

```bash
# Add remote (replace with YOUR actual repo URL)
git remote add origin https://github.com/YOUR-USERNAME/insurance-investor-portal.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Step 5: Verify

1. Go to your GitHub repository page
2. You should see all your files there
3. Ready to deploy to Render!

## Common Issues

### Issue: "Repository already exists"
**Solution:** If the directory was already a git repo, that's fine. Just continue with `git add .`

### Issue: "Authentication required"
**Solution:** GitHub may ask for authentication. Use:
- Personal Access Token (recommended), or
- GitHub CLI: `gh auth login`

### Issue: "Remote origin already exists"
**Solution:** If you need to change the remote URL:
```bash
git remote set-url origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
```

## Quick Command Reference

```bash
# Initialize (already done)
git init

# Add files
git add .

# Commit
git commit -m "Initial commit"

# Add remote (replace URL)
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git

# Push
git push -u origin main
```

---

**Next:** After pushing to GitHub, follow `DEPLOY_INSTRUCTIONS.md` to deploy to Render!

