# SupplyChain TimeCycle & Bottleneck Analyzer Backend

A comprehensive FastAPI-based supply chain analytics platform with automatic time cycle calculation, SLA monitoring, and bottleneck detection.

## 🚀 Features

### Core Analytics Engine
- **Automated Duration Calculation**: Calculates stage-wise durations (procurement, processing, dispatch, delivery)
- **SLA Breach Detection**: Configurable SLA thresholds with automatic breach detection and alerting
- **Bottleneck Identification**: Automatically identifies the slowest stage in each order lifecycle
- **Real-time Analytics**: All analytics calculated during order creation/update

### Analytics Capabilities
- Aggregate analytics summaries
- SLA breach reports and tracking
- Bottleneck distribution analysis
- Stage performance statistics
- Priority-based analytics
- Top delayed orders tracking
- Detailed per-order analytics reports

### Architecture
- **Modular Design**: Clean separation of utilities, services, and routers
- **Reusable Components**: Time calculator, SLA detector, and bottleneck analyzer utilities
- **Service Layer**: Business logic encapsulation with preprocessing pipeline
- **Scalable**: Production-ready FastAPI structure

## 📁 Project Structure

```
supply-chain-backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── database.py                  # Database configuration
│   ├── models.py                    # SQLAlchemy models with analytics fields
│   │
│   ├── routers/                     # API endpoints
│   │   ├── __init__.py
│   │   ├── orders.py               # Order CRUD operations
│   │   ├── stage_logs.py           # Stage log management
│   │   └── analytics.py            # Analytics queries and reports
│   │
│   ├── schemas/                     # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── order_schemas.py        # Order validation schemas
│   │   └── stage_log_schemas.py    # Stage log schemas
│   │
│   ├── services/                    # Business logic layer
│   │   ├── __init__.py
│   │   ├── order_service.py        # Order service with analytics
│   │   └── order_preprocessing.py  # Analytics preprocessing pipeline
│   │
│   └── utils/                       # Reusable utilities
│       ├── __init__.py
│       ├── time_calculator.py      # Duration calculation engine
│       ├── sla_detector.py         # SLA validation logic
│       └── bottleneck_detector.py  # Bottleneck analysis utilities
│
├── requirements.txt
├── example_usage.py                 # API usage examples
├── .env                            # Environment configuration
├── .gitignore
└── README.md
```

## 🛠️ Backend Setup

### Prerequisites
- Python 3.8+
- MySQL 5.7+ or 8.0+

### Installation

1. **Navigate to backend directory**
   ```bash
   cd supply-chain-backend
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   
   Create MySQL database:
   ```sql
   CREATE DATABASE supply_chain_db;
   ```
   
   Update `.env` file with your credentials:
   ```env
   DATABASE_URL=mysql+pymysql://username:password@localhost:3306/supply_chain_db
   ```

5. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📊 Analytics Processing Pipeline

### How It Works

1. **Order Creation**: When an order is created with lifecycle timestamps, it automatically flows through the preprocessing pipeline

2. **Time Calculation**: The system calculates durations for each stage:
   - Procurement Time (order placed → confirmed)
   - Processing Time (confirmed → processing completed)
   - Dispatch Time (processing completed → shipped)
   - Delivery Time (shipped → delivered)
   - Total Time (order placed → delivered)

3. **SLA Validation**: Each stage duration is compared against configurable thresholds:
   - Procurement: 24 hours (default)
   - Processing: 72 hours (default)
   - Dispatch: 12 hours (default)
   - Delivery: 48 hours (default)

4. **Bottleneck Detection**: The stage with the highest duration is identified as the bottleneck

5. **Data Storage**: All calculated analytics are stored with the order for instant querying

### SLA Thresholds

Default SLA thresholds (in hours):
- **Procurement**: 24 hours
- **Processing**: 72 hours
- **Dispatch**: 12 hours
- **Delivery**: 48 hours

These can be customized in `app/utils/sla_detector.py`

## 🔌 API Endpoints

### Order Management

#### Create Order with Analytics
```http
POST /api/orders/
Content-Type: application/json

{
  "order_number": "ORD-2026-001",
  "customer_name": "Acme Corp",
  "customer_email": "orders@acmecorp.com",
  "product_name": "Industrial Widget",
  "quantity": 100,
  "priority": "high",
  "order_placed_at": "2026-05-01T10:00:00",
  "order_confirmed_at": "2026-05-02T08:00:00",
  "processing_completed_at": "2026-05-05T10:00:00",
  "shipped_at": "2026-05-05T18:00:00",
  "delivered_at": "2026-05-07T14:00:00"
}
```

Response includes all calculated analytics fields:
```json
{
  "id": 1,
  "order_number": "ORD-2026-001",
  "procurement_time": 22.0,
  "processing_time": 74.0,
  "dispatch_time": 8.0,
  "delivery_time": 44.0,
  "total_time": 148.0,
  "sla_breach": true,
  "breached_stage": "processing",
  "bottleneck_stage": "processing"
}
```

#### List Orders with Filters
```http
GET /api/orders/?sla_breach=true
GET /api/orders/?bottleneck_stage=processing
GET /api/orders/?status=completed&limit=50
```

#### Update Order (with analytics reprocessing)
```http
PATCH /api/orders/{order_id}?reprocess_analytics=true
Content-Type: application/json

{
  "shipped_at": "2026-05-06T12:00:00"
}
```

### Analytics Endpoints

#### Get Analytics Summary
```http
GET /api/analytics/summary
```

Returns aggregate metrics:
- Total orders
- SLA breach count and rate
- Average durations per stage
- Bottleneck distribution

#### Get SLA Breach Report
```http
GET /api/analytics/sla-breaches?limit=100
```

Returns all orders that breached SLA thresholds.

#### Get Orders by Bottleneck Stage
```http
GET /api/analytics/bottlenecks/processing?limit=50
```

Returns orders filtered by specific bottleneck stage.

#### Get Bottleneck Distribution
```http
GET /api/analytics/bottleneck-distribution
```

Returns distribution of bottleneck stages across all orders.

#### Get Stage Performance Statistics
```http
GET /api/analytics/stage-performance
```

Returns average, min, max durations for each stage.

#### Get Detailed Order Analysis
```http
GET /api/analytics/order/{order_id}/detailed-analysis
```

Returns comprehensive analytics report for a specific order including:
- All stage durations
- Detailed SLA status per stage
- Bottleneck analysis with percentages
- Timeline information

#### Get Orders by Priority
```http
GET /api/analytics/orders-by-priority
```

Returns analytics grouped by order priority level.

#### Get Top Delayed Orders
```http
GET /api/analytics/top-delayed-orders?limit=10
```

Returns orders with longest total cycle time.

#### Get SLA Thresholds
```http
GET /api/analytics/sla-thresholds
```

Returns current SLA threshold configuration.

### Stage Log Management

#### Create Stage Log
```http
POST /api/stage-logs/
```

#### List Stage Logs
```http
GET /api/stage-logs/?order_id={order_id}
```

#### Update Stage Log
```http
PATCH /api/stage-logs/{stage_log_id}
```

### Health Check

```http
GET /health
GET /
```

## 🧪 Testing & Examples

### Using the Example Script

Run the provided example script to test all functionality:

```bash
# Ensure the server is running first
python example_usage.py
```

This script demonstrates:
- Creating orders with lifecycle timestamps
- Automatic analytics calculation
- Querying analytics summaries
- SLA breach detection
- Bottleneck analysis
- Detailed order reports

### Manual Testing with cURL

Create an order:
```bash
curl -X POST "http://localhost:8000/api/orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "ORD-TEST-001",
    "customer_name": "Test Customer",
    "product_name": "Test Product",
    "quantity": 10,
    "priority": "normal",
    "order_placed_at": "2026-05-01T10:00:00",
    "order_confirmed_at": "2026-05-01T20:00:00",
    "processing_completed_at": "2026-05-03T10:00:00",
    "shipped_at": "2026-05-03T15:00:00",
    "delivered_at": "2026-05-05T12:00:00"
  }'
```

Get analytics summary:
```bash
curl http://localhost:8000/api/analytics/summary
```

## 🔧 Configuration

### Database Configuration

Edit `.env` file:
```env
DATABASE_URL=mysql+pymysql://username:password@host:port/database_name
```

### SLA Threshold Configuration

Edit `app/utils/sla_detector.py`:
```python
SLA_THRESHOLDS = {
    "procurement": 24.0,    # hours
    "processing": 72.0,     # hours
    "dispatch": 12.0,       # hours
    "delivery": 48.0,       # hours
}
```

## 📈 Database Schema

### Order Table Fields

**Core Fields:**
- `id`, `order_number`, `customer_name`, `customer_email`
- `product_name`, `quantity`, `priority`, `status`
- `created_at`, `updated_at`, `completed_at`

**Lifecycle Timestamps:**
- `order_placed_at`
- `order_confirmed_at`
- `processing_completed_at`
- `shipped_at`
- `delivered_at`

**Analytics Fields (Auto-calculated):**
- `procurement_time` (hours)
- `processing_time` (hours)
- `dispatch_time` (hours)
- `delivery_time` (hours)
- `total_time` (hours)
- `sla_breach` (boolean)
- `breached_stage` (string)
- `bottleneck_stage` (string)

## 🚀 Production Deployment

### Recommendations

1. **Environment Variables**: Use proper environment management
2. **Database Pooling**: Configure connection pool size based on load
3. **Logging**: Enable structured logging for production
4. **Monitoring**: Set up health checks and performance monitoring
5. **Security**: Enable CORS, rate limiting, and authentication

### Running with Gunicorn

```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🔄 Workflow

1. **Order Created** → Lifecycle timestamps provided
2. **Preprocessing Pipeline** → Calculates all analytics
3. **Data Stored** → Order saved with analytics fields
4. **Query Analytics** → Fast retrieval via indexed fields
5. **Reports & Dashboards** → Ready for visualization tools

## 📝 Key Features Summary

✅ **Automatic Analytics**: No manual calculation needed  
✅ **Real-time Processing**: Analytics calculated on order creation/update  
✅ **Configurable SLAs**: Easily adjust thresholds per business needs  
✅ **Comprehensive Reports**: Multiple analytics endpoints for insights  
✅ **Scalable Architecture**: Modular design for easy maintenance  
✅ **Production Ready**: Clean separation of concerns, error handling  
✅ **API Documentation**: Auto-generated Swagger/ReDoc docs  
✅ **Test Ready**: Example scripts and comprehensive testing support  

## 🎯 Use Cases

- **Supply Chain Monitoring**: Track order lifecycle performance
- **SLA Compliance**: Monitor and report on SLA breaches
- **Bottleneck Analysis**: Identify operational inefficiencies
- **Performance Optimization**: Data-driven process improvements
- **Executive Dashboards**: Aggregate analytics for leadership
- **Tableau Integration**: Export data for advanced visualization

## 📞 Support

For issues or questions, please check:
1. API documentation at `/docs`
2. Example usage scripts
3. Error logs in the application

---

**Version**: 2.0.0  
**Last Updated**: May 2026  
**License**: MIT