# LogiAI — AI-Powered Logistics Support System

An intelligent customer support system for logistics and e-commerce, powered by **Natural Language Processing (NLP)**. The system classifies user queries, resolves order-related requests automatically, and escalates complex issues to human agents.

---

## Live Demo

| Service  | URL |
|----------|-----|
| Frontend |https://ai-logistics-system.vercel.app/ |
| Backend  |https://ai-logistics-system.onrender.com/|

---

## Features

- **NLP Intent Classification** — Custom-trained spaCy text classification model (3 categories: `ORDER_STATUS`, `ORDER_CANCELLATION`, `UNKNOWN`)
- **Smart Policy Engine** — Automatically resolves tracking, cancellation, refund, and damage reports based on order status and business rules
- **Escalation Logic** — Only truly unresolvable queries reach the admin; routine queries are auto-resolved or kept in-progress
- **Admin Dashboard** — Real-time metrics, ticket management with approve/reject, order policy verification
- **Light / Dark Theme** — Toggle between Professional Blue light mode and dark mode
- **JWT Authentication** — Secure login for both customers and admin
- **Order-Aware Responses** — Emoji-rich, status-specific responses for each order state

---

## Tech Stack

| Layer     | Technology |
|-----------|------------|
| Frontend  | React 18, Lucide Icons, Recharts |
| Backend   | FastAPI, Uvicorn |
| Database  | SQLAlchemy 2.0 ORM, SQLite (PostgreSQL-ready) |
| NLP Model | spaCy 3.8 (custom-trained text classifier) |
| Auth      | JWT (python-jose), bcrypt |
| Deploy    | Vercel (frontend), Render (backend) |

---

## Project Structure

```
ai-logistics-system/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, routes, chat endpoint
│   │   ├── auth.py              # JWT authentication & password hashing
│   │   ├── config.py            # Central configuration
│   │   ├── database.py          # SQLAlchemy session, CRUD operations
│   │   ├── models.py            # ORM models (User, Order, Ticket)
│   │   ├── intent_service.py    # spaCy NLP classification + keyword fallback
│   │   ├── policy_engine.py     # Business rules engine (track/cancel/refund/damage)
│   │   ├── order_service.py     # Order lookup & cancellation
│   │   ├── refund_service.py    # Refund eligibility checks
│   │   ├── response_generator.py# Professional response formatting
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   └── seed_data.py         # Demo data (users + 15 orders)
│   ├── models/
│   │   └── trained_logistics_model_v3/  # Trained spaCy NLP model
│   ├── training/                # Training scripts & datasets
│   ├── requirements.txt
│   ├── Procfile                 # Render deployment
│   ├── runtime.txt              # Python version
│   └── .env.example             # Environment variable template
├── frontend/
│   ├── src/
│   │   ├── App.js               # Router, theme toggle
│   │   ├── App.css              # Full theme system (light + dark)
│   │   ├── Userpage.js          # Chat interface, auth modal
│   │   ├── Admin.js             # Admin dashboard
│   │   └── pages/Login.js       # Admin login page
│   ├── vercel.json              # Vercel deployment config
│   ├── package.json
│   └── .env.production          # Production API URL
└── README.md
```

---

## How to Run Locally

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Madhujith45/ai-logistics-system.git
cd ai-logistics-system
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Set your secret key
# Copy .env.example to .env and update JWT_SECRET_KEY
cp .env.example .env

# Start the backend server
uvicorn app.main:app --port 8000
```

The backend will be available at `http://localhost:8000`

> **Note:** The database and demo data are automatically created on first startup.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at `http://localhost:3000`

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret key for JWT token signing | `supersecretkey` |
| `DATABASE_URL` | Database connection string | `sqlite:///./logistics.db` |

> **⚠️ Note:** For production, set `JWT_SECRET_KEY` to a strong random string via your hosting platform's environment variables (e.g., Render Dashboard → Environment).

### Frontend (`frontend/.env.production`)

| Variable | Description |
|----------|-------------|
| `REACT_APP_API_URL` | Backend API URL for production |

---

## Demo Credentials

| Role | Email / Username | Password |
|------|-----------------|----------|
| Admin | `admin` | `admin123` |
| Customer | `rahul@logiai.com` | `rahul123` |
| Customer | `priya@logiai.com` | `priya123` |
| Customer | `amit@logiai.com` | `amit123` |

---

## Sample Test Queries

| Query | Expected Behavior |
|-------|-------------------|
| `hey` / `hello` | Greeting — auto-resolved with welcome menu |
| `Track my order` | Asks for Order ID, then shows status with emoji |
| `Cancel my order` + Order ID | Cancels if Placed/Processing, denies if Shipped/Delivered |
| `I want a refund` + Order ID | Checks delivery & return window eligibility |
| `I received a damaged product` + Order ID | Initiates replacement, escalates to admin |
| `What is your return policy?` | Escalated to admin (unknown intent) |

---

## Output Screenshots

> _Add screenshots of the application here_

 
<img width="1919" height="919" alt="image" src="https://github.com/user-attachments/assets/0c36b482-ea2b-4b7b-930c-f36e244853bb" />
<img width="1919" height="906" alt="image" src="https://github.com/user-attachments/assets/7689b917-a9b2-4aff-86e5-ef63ce608146" />
<img width="925" height="789" alt="image" src="https://github.com/user-attachments/assets/07d915d0-f6a8-48c5-80bf-29161f1da4bb" />



-->

---

## NLP Model Details

- **Framework:** spaCy 3.8
- **Architecture:** Text Classification (`textcat`)
- **Categories:** `ORDER_STATUS`, `ORDER_CANCELLATION`, `UNKNOWN`
- **Training Data:** Custom-curated logistics dataset (merged from multiple sources)
- **Accuracy:** 100% on core intent queries with keyword fallback system
- **Extended Intents:** `TRACK_ORDER`, `CANCEL_ORDER`, `REFUND_REQUEST`, `DAMAGED_PRODUCT`, `MISMATCH_PRODUCT` (mapped via intent service)

---

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/chat` | Main chat endpoint — classifies intent & responds | Optional |
| `POST` | `/login` | User/Admin login (returns JWT) | No |
| `POST` | `/user/register` | Customer registration | No |
| `POST` | `/user/login` | Customer login | No |
| `GET`  | `/user/profile` | Get logged-in user profile | JWT |
| `GET`  | `/user/orders` | Get user's orders | JWT |
| `GET`  | `/tickets` | Get all tickets (admin) | Admin JWT |
| `GET`  | `/escalations` | Get pending tickets (admin) | Admin JWT |
| `POST` | `/admin/approve/{id}` | Approve a ticket | Admin JWT |
| `POST` | `/admin/reject/{id}` | Reject a ticket | Admin JWT |
| `GET`  | `/admin/metrics` | Dashboard metrics | Admin JWT |
| `GET`  | `/health` | Health check | No |

---

## Deployment

### Backend (Render)

1. Connect your GitHub repo to [Render](https://render.com)
2. Set **Build Command:** `pip install -r requirements.txt`
3. Set **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port 10000`
4. Set **Root Directory:** `backend`
5. Add environment variable: `JWT_SECRET_KEY` = your secret key

### Frontend (Vercel)

1. Connect your GitHub repo to [Vercel](https://vercel.com)
2. Set **Root Directory:** `frontend`
3. Set **Build Command:** `npm run build`
4. Add environment variable: `REACT_APP_API_URL` = your Render backend URL

---

## License

This project is built for academic purposes as a final-year project.
