# 🌹 Atlas Rose Bot - Handmade Flower Shop

A Telegram bot for selling handmade satin rose bouquets with full admin panel and order management.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Bot Features](#bot-features)
- [Admin Panel](#admin-panel)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)

---

## ✨ Features

### For Customers:
- 🌹 Browse bouquet catalog with photos
- 🛒 Multi-step order constructor
- ⚡️ Express delivery option (+1000₽)
- 💌 Greeting card service (+100₽)
- 📅 Custom date/time selection
- 📍 Pickup or delivery options
- ⭐️ Favorites system
- 📦 Order history
- 💬 Direct contact with seller

### For Admins:
- 📊 Statistics dashboard
- 📦 Order management
- ➕ Add new bouquets
- ✏️ Edit bouquet names
- 💰 Change prices
- 🔥 Toggle popularity
- 🗑 Delete bouquets
- 🤖 Auto-popularity (10+ orders)

---

## 🛠 Tech Stack

- **Python 3.11**
- **python-telegram-bot 21.0.1** - Telegram Bot API
- **PyYAML 6.0.2** - Data storage
- **python-dotenv 1.0.1** - Environment variables
- **Railway / PythonAnywhere** - Hosting

---

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### Local Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/atlas-rose-bot.git
cd atlas-rose-bot
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create `.env` file:**
```bash
BOT_TOKEN=your_bot_token_here
```

4. **Run the bot:**
```bash
python bot.py
```

---

## ⚙️ Configuration

### Bot Configuration (`config.py`)

```python
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Your bot token
ADMIN_ID = 4324231523               # Primary admin Telegram ID
ADMIN_ID_2 = 5343425324            # Secondary admin ID
ADMIN_IDS = [5343425324]
CONTACT_USERNAME = "...."        # Contact Telegram username
```

### Bouquet Configuration (`data/bouquets.yaml`)

```yaml
bouquets:
  - id: "b1"
    name: "Blue Roses"
    base_price: 4500
    image_path: "images/1.jpg"
    is_popular: true
    order_count: 0
    quantities:
      - value: 21
        multiplier: 0.244  # 21 roses = 1100₽
      - value: 51
        multiplier: 0.511  # 51 roses = 2300₽
      - value: 71
        multiplier: 0.711  # 71 roses = 3200₽
      - value: 101
        multiplier: 1.0    # 101 roses = 4500₽
    packaging:
      - type: "standard"
        name: "Standard"
        price: 0
      - type: "premium"
        name: "Premium"
        price: 300
      - type: "black"
        name: "Black"
        price: 500
```

---

## 🚀 Deployment

### Option 1: Railway (Recommended)

1. **Push to GitHub:**
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/your-repo.git
git push -u origin main
```

2. **Deploy to Railway:**
   - Go to [Railway.app](https://railway.app)
   - Create new project
   - Connect GitHub repository
   - Add environment variable: `BOT_TOKEN`
   - Deploy automatically

3. **Files required:**
   - `Procfile` - Contains: `worker: python bot.py`
   - `runtime.txt` - Contains: `python-3.11`

### Option 2: PythonAnywhere (Free Forever)

1. **Sign up at [PythonAnywhere.com](https://www.pythonanywhere.com)**

2. **Upload files:**
```bash
# In Bash console
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

3. **Create virtual environment:**
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Create `.env` file:**
```bash
nano .env
# Add: BOT_TOKEN=your_token_here
```

5. **Create Always-On Task:**
   - Go to "Tasks" tab
   - Create new always-on task
   - Command: `/home/yourusername/your-repo/venv/bin/python /home/yourusername/your-repo/bot.py`

6. **Note:** Free plan requires renewal every 3 months (one click)

---

## 🎯 Bot Features

### Customer Flow

1. **Start Bot:** `/start` command
2. **Browse Catalog:** View all available bouquets
3. **Select Bouquet:** Choose desired bouquet
4. **Configure Order:**
   - Select quantity: 21, 51, 71, or 101 roses
   - Choose packaging: Standard, Premium, or Black
   - Optional: Express delivery (+1000₽)
   - Optional: Greeting card (+100₽)
   - Select delivery date (min 2-4 days based on quantity)
   - Choose time (12:00 - 20:00)
   - Pickup method: Self-pickup or City meeting
5. **Add to Cart:** Review and add to shopping cart
6. **Contact for Payment:** Direct message to seller

### Admin Commands

- `/admin` - Open admin panel
- `/cancel` - Cancel current operation

---

## 👑 Admin Panel

### Statistics
- Total users
- Total orders
- Total revenue
- Today's orders
- Today's revenue
- Total bouquets in catalog

### Order Management
- View last 10 orders
- Customer information
- Order details

### Bouquet Management
- ✏️ Change bouquet name
- 💰 Change price
- 🔥 Toggle popularity
- 🗑 Delete bouquet
- ➕ Add new bouquet (with photo upload)

### Auto-Popularity Feature
Bouquets automatically become "popular" (🔥) after receiving 10+ orders.

---

## 📁 Project Structure

```
atlas-rose-bot/
├── bot.py                  # Main bot entry point
├── config.py              # Configuration & settings
├── requirements.txt       # Python dependencies
├── Procfile              # Railway deployment config
├── runtime.txt           # Python version specification
├── .env                  # Environment variables (not in repo)
├── .gitignore           # Git ignore rules
├── README.md            # This file
│
├── handlers/            # Command handlers
│   ├── __init__.py
│   ├── client.py       # Customer commands & flow
│   └── admin.py        # Admin panel & management
│
├── database/           # Data management
│   ├── __init__.py
│   └── db.py          # YAML database operations
│
├── data/              # YAML storage
│   ├── bouquets.yaml  # Bouquet catalog
│   ├── admins.yaml    # Admin user IDs
│   ├── carts.yaml     # Shopping carts
│   ├── orders.yaml    # Order history
│   ├── favorites.yaml # User favorites
│   └── users.yaml     # User registry
│
└── images/            # Bouquet photos
    ├── 1.jpg
    ├── 2.jpg
    ├── 3.jpg
    ├── 4.jpg
    ├── 5.jpg
    ├── 6.jpg
    └── 7.jpg
```

---

## 🔐 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram Bot API Token | `123456:ABC-DEF...` |

### Optional Variables (Hardcoded in config.py)

| Variable | Description | Default |
|----------|-------------|---------|
| `ADMIN_ID` | Primary admin Telegram ID | `1063802362` |
| `ADMIN_ID_2` | Secondary admin ID | `1477864632` |

---

## 🎨 Customization

### Adding New Bouquet

1. **Via Admin Panel:**
   - Use `/admin` command
   - Click "➕ Add bouquet"
   - Follow the prompts

2. **Manually edit `data/bouquets.yaml`:**
   - Copy existing bouquet structure
   - Change `id`, `name`, `base_price`, `image_path`
   - Upload photo to `images/` folder

### Changing Prices

**Via Admin Panel:**
1. `/admin` → "🌹 Manage bouquets"
2. Select bouquet
3. Click "💰 Change price"
4. Enter new price

**Or edit `data/bouquets.yaml` manually**

### Adding More Admins

Edit `data/admins.yaml`:
```yaml
admins:
  - 1063802362
  - your_new_admin_id_here
```

And update `config.py`:
```python
ADMIN_IDS = [1063802362,your_new_admin_id]
```

---

## 🐛 Troubleshooting

### Bot doesn't respond to /start

**Solution:**
1. Check bot token is correct
2. Verify bot is running (check logs)
3. Ensure Telegram username is set

### "BOT_TOKEN not found" error

**Solution:**
1. Create `.env` file in project root
2. Add `BOT_TOKEN=your_token_here`
3. Restart bot

### Photos not loading

**Solution:**
1. Ensure images exist in `images/` folder
2. Check file permissions
3. Verify `image_path` in `bouquets.yaml` is correct

### Admin panel shows "Access denied"

**Solution:**
1. Verify your Telegram ID
2. Add your ID to `ADMIN_IDS` in `config.py`
3. Add your ID to `data/admins.yaml`
4. Restart bot

---

## 📝 Data Storage

All data is stored in YAML files for simplicity and portability:

- **bouquets.yaml** - Bouquet catalog with prices, images, popularity
- **carts.yaml** - User shopping carts (temporary)
- **orders.yaml** - Order history with timestamps
- **favorites.yaml** - User favorite bouquets
- **users.yaml** - Registered users
- **admins.yaml** - Admin user IDs

---

## 🔄 Updates & Maintenance

### Updating the Bot

1. **Pull latest changes:**
```bash
git pull origin main
```

2. **Update dependencies:**
```bash
pip install -r requirements.txt --upgrade
```

3. **Restart bot:**
   - Railway: Auto-deploys on push
   - PythonAnywhere: Stop and restart always-on task

### Backing Up Data

Regularly backup the `data/` folder:
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz data/
```

---

## 📊 Analytics

Track bot performance through:
- Admin statistics panel (`/admin` → "📊 Statistics")
- Order count per bouquet (auto-popularity feature)
- Daily revenue tracking
- User registration count

---

## 🛡️ Security

- ✅ Admin access restricted by Telegram ID
- ✅ Environment variables for sensitive data
- ✅ `.gitignore` prevents committing secrets
- ✅ User data stored locally (YAML)
- ✅ No external database required

---

## 📄 License

This project is licensed under the MIT License.

---

## 👥 Authors

- **Developer:** [@thesun4ck](https://t.me/thesun4ck)

---

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [Railway](https://railway.app) - Deployment platform
- [PythonAnywhere](https://www.pythonanywhere.com) - Free Python hosting

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/yourusername/atlas-rose-bot.git

# Install
cd atlas-rose-bot
pip install -r requirements.txt

# Configure
echo "BOT_TOKEN=your_token_here" > .env

# Run
python bot.py
```

**Bot is ready!** Start chatting with your bot in Telegram 🌹

---

