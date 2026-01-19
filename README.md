# Plant Disease Detection Chatbot

LINE Chatbot ระบบวินิจฉัยโรคพืชด้วย AI Vision โดยใช้ Gemini 2.0 Flash สำหรับวิเคราะห์ภาพ

## Features

- รับภาพพืชจากผู้ใช้ผ่าน LINE
- ส่ง Flex Message ขอข้อมูลเพิ่มเติม (ชนิดพืช, ภูมิภาค)
- วิเคราะห์โรคด้วย Gemini 2.0 Flash Vision API
- ส่งผลวิเคราะห์กลับเป็น Flex Message พร้อมคำแนะนำการรักษา
- รองรับพืชหลายชนิด: ข้าว, ข้าวโพด, มันสำปะหลัง, อ้อย และอื่นๆ

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **AI Vision**: Google Gemini 2.0 Flash
- **Cache**: Redis
- **Database**: PostgreSQL
- **Image Processing**: Pillow + OpenCV
- **LINE SDK**: line-bot-sdk 3.x
- **Deployment**: Docker + Google Cloud Run

## Project Structure

```
plant-disease-chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── models.py            # Pydantic models
│   ├── handlers/
│   │   ├── line_handler.py  # LINE webhook handler
│   │   └── message_handler.py
│   ├── services/
│   │   ├── gemini_service.py    # Gemini API client
│   │   ├── image_service.py     # Image optimization
│   │   └── cache_service.py     # Redis operations
│   ├── utils/
│   │   ├── flex_messages.py # LINE Flex Message templates
│   │   └── parsers.py       # Text parsing utilities
│   └── database/
│       ├── models.py        # SQLAlchemy models
│       └── crud.py          # Database operations
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-username/plant-disease-chatbot.git
cd plant-disease-chatbot
```

### 2. Setup Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
- `LINE_CHANNEL_ACCESS_TOKEN` - LINE Messaging API token
- `LINE_CHANNEL_SECRET` - LINE Channel secret
- `GEMINI_API_KEY` - Google Gemini API key

### 3. Run with Docker Compose

```bash
# Production
docker-compose up -d

# Development (with hot reload)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 4. Run Locally (Development)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run application
uvicorn app.main:app --reload
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API token | Required |
| `LINE_CHANNEL_SECRET` | LINE Channel secret | Required |
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://...` |
| `ENVIRONMENT` | Environment (dev/staging/prod) | `dev` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_IMAGE_SIZE_MB` | Max image size in MB | `5` |
| `MAX_REQUESTS_PER_HOUR` | Rate limit per user | `10` |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check |
| `/webhook` | POST | LINE webhook |
| `/stats` | GET | Statistics (dev only) |

## LINE Bot Setup

1. สร้าง LINE Official Account ที่ [LINE Developers](https://developers.line.biz/)
2. เปิดใช้งาน Messaging API
3. ตั้งค่า Webhook URL: `https://your-domain.com/webhook`
4. คัดลอก Channel Access Token และ Channel Secret

## Gemini API Setup

1. สร้าง API key ที่ [Google AI Studio](https://aistudio.google.com/app/apikey)
2. คัดลอก API key ไปใส่ใน `.env`

## Usage Flow

1. ผู้ใช้ส่งรูปภาพพืชที่สงสัยว่าเป็นโรค
2. Bot ถามข้อมูลเพิ่มเติม (ชนิดพืช, ภูมิภาค)
3. ผู้ใช้เลือกข้อมูลจาก Flex Message
4. Bot วิเคราะห์ภาพด้วย Gemini AI
5. Bot ส่งผลวินิจฉัยพร้อมคำแนะนำการรักษา

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_models.py -v
```

## Deployment

### Google Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/plant-disease-chatbot

# Deploy
gcloud run deploy plant-disease-chatbot \
  --image gcr.io/PROJECT_ID/plant-disease-chatbot \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars="ENVIRONMENT=prod"
```

### Docker

```bash
# Build
docker build -t plant-disease-chatbot .

# Run
docker run -p 8000:8000 --env-file .env plant-disease-chatbot
```

## Performance Targets

- Response time: < 5s (95th percentile)
- Throughput: 100 requests/minute
- Cache hit rate: > 30%
- Uptime: 99.5%

## Cost Estimation (1,000 users/day)

- Gemini API: ~$7/month
- Cloud Run: ~$10/month
- Redis: ~$5/month
- PostgreSQL: ~$10/month
- **Total**: ~$30/month

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

- Google Gemini AI for vision capabilities
- LINE Messaging API for chat platform
- FastAPI for high-performance backend
