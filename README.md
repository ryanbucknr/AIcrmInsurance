# Insurance Investor Portal

Secure portal for investors to view their investment data and performance metrics.

## Features

- 🔐 Secure authentication for multiple investors
- 📊 Individual investor dashboards
- 📈 Performance metrics and ROI tracking
- 🤖 AI-powered chatbot for data queries (optional)
- 📤 Admin data upload and management

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run Locally

```bash
python app.py
```

Visit: http://localhost:5002

## Login Credentials

Default credentials (change in production):

| User | Username | Password |
|------|----------|----------|
| Eric | `eric` | `eric123` |
| Phillip | `phillip` | `phillip123` |
| Admin | `admin` | `admin123` |

## Deployment

### Deploy to Render.com

1. **Create Web Service** - Connect GitHub repo
2. **Start Command:** `gunicorn app:app`
3. **Add Persistent Disk:**
   - Name: `investor-data`
   - Mount: `/data`
   - Size: `1GB`
4. **Environment Variables:**
   - `SECRET_KEY` - Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"`
   - `FLASK_ENV` - Set to `production`
   - `OPENAI_API_KEY` - (Optional, for chatbot features)

5. **Deploy!** Data will auto-setup on first run.

## File Structure

```
├── app.py              # Main Flask application
├── auth.py             # Authentication manager
├── database.py         # Database operations
├── chatbot.py          # AI chatbot (optional)
├── requirements.txt    # Python dependencies
├── Procfile           # Render deployment config
├── runtime.txt        # Python version
└── templates/         # HTML templates
    ├── login.html
    ├── dashboard.html
    └── admin.html
```

## Usage

1. **Investors** log in to see their own data
2. **Admin** can upload new CSV/Excel files via dashboard
3. **Auto-setup** creates investors and accounts on first run
4. **Data persists** on persistent disk (`/data`)

## Security

⚠️ **Before production:**
- Change all default passwords
- Set strong `SECRET_KEY`
- Enable HTTPS
- Use persistent disk for data storage

## Support

For issues, check Render logs or contact support.

