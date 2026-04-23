# SupplyChain_TimeCycle-BottleneckAnalyzer_backend

## Project Structure

```
supply-chain-backend/
│
├── app/
│   └── main.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Backend Setup

### Prerequisites
- Python 3.8+

### Installation

```bash
cd supply-chain-backend
pip install -r requirements.txt
```

### Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check endpoint