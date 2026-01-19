# Prompt สำหรับ Claude Max: LINE Chatbot - AI Plant Disease Detection System

## Project Overview
สร้าง LINE Chatbot ระบบวินิจฉัยโรคพืชด้วย AI Vision โดยเน้นข้าวเป็นหลัก ใช้ Gemini 2.0 Flash สำหรับวิเคราะห์ภาพ

## System Requirements

### Core Features
1. รับภาพพืชจากผู้ใช้ผ่าน LINE
2. ส่ง Flex Message ขอข้อมูลเพิ่มเติม (ชนิดพืช, จุดที่เกิด)
3. วิเคราะห์โรคด้วย Gemini 2.0 Flash Vision API
4. ส่งผลวิเคราะห์กลับเป็น Flex Message

### Output Structure
```json
{
  "disease_name_th": "ชื่อโรคภาษาไทย",
  "disease_name_en": "Disease Name in English",
  "pathogen_type": "เชื้อรา|ไวรัส|แบคทีเรีย|ศัตรูพืช|ปัญหาสารอาหาร",
  "confidence_level": 85,
  "symptoms_observed": ["อาการที่พบ 1", "อาการที่พบ 2"],
  "disease_characteristics": {
    "appearance": "ลักษณะการปรากฏ",
    "occurrence": "สาเหตุและสภาวะที่เกิด",
    "spread_pattern": "รูปแบบการแพร่กระจาย",
    "severity": "เล็กน้อย|ปานกลาง|รุนแรง"
  },
  "recommendations": ["คำแนะนำ 1", "คำแนะนำ 2"],
  "prevention_methods": ["วิธีป้องกัน 1", "วิธีป้องกัน 2"],
  "treatment": {
    "immediate_action": ["การดำเนินการเร่งด่วน"],
    "chemical_control": [
      {
        "product_name": "ชื่อสาร",
        "active_ingredient": "สารออกฤทธิ์",
        "dosage": "อัตราการใช้",
        "application_method": "วิธีใช้",
        "precautions": "ข้อควรระวัง"
      }
    ],
    "organic_control": ["วิธีอินทรีย์"],
    "cultural_practices": ["วิธีการจัดการแปลงนา"]
  },
  "additional_notes": "ข้อมูลเพิ่มเติม",
  "followup_needed": true,
  "expert_consultation": "แนะนำปรึกษาผู้เชี่ยวชาญ"
}
```

## Tech Stack Selection

### เหตุผลในการเลือก

#### 1. Backend Framework: **FastAPI (Python 3.11+)** ⭐
**เหตุผล:**
- Async/Await native → ประมวลผลหลาย request พร้อมกัน
- เร็วกว่า Flask 3-4 เท่า (ASGI vs WSGI)
- Auto-documentation (Swagger/OpenAPI)
- Type hints → น้อย bug, debug ง่าย
- รองรับ WebSocket สำหรับ real-time

**ทางเลือกอื่น (ไม่แนะนำ):**
- Flask: ช้ากว่า, ไม่มี async native
- Express.js: ต้องจัดการ async แบบ callback hell
- Django: หนักเกินไป, overkill สำหรับ chatbot

#### 2. AI Vision API: **Gemini 2.0 Flash** ⭐
**เหตุผล:**
- **เร็วที่สุด**: latency ~1-2s (Claude ~3-5s)
- **ถูกที่สุด**: $0.075/1M tokens input (Claude $3/1M tokens)
- **Free tier**: 15 RPM, 1500 RPD
- **Context window**: 1M tokens
- **Multimodal native**: ออกแบบมาสำหรับ vision

**เปรียบเทียบ:**
| Feature | Gemini 2.0 Flash | Claude Sonnet 4.5 | GPT-4o |
|---------|------------------|-------------------|--------|
| Speed | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Cost | $0.075/1M | $3/1M | $2.5/1M |
| Accuracy | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Free Tier | ✅ 15 RPM | ❌ | ❌ |

#### 3. Message Queue: **Redis + Celery** ⭐
**เหตุผล:**
- Redis: In-memory → super fast caching
- Celery: Async task processing
- รองรับ retry mechanism
- Monitoring ง่าย (Flower)

#### 4. Database: **PostgreSQL**
**เหตุผล:**
- JSONB support → เก็บ diagnosis result
- Full-text search → ค้นหาประวัติ
- Reliable, production-ready

#### 5. Image Processing: **Pillow + OpenCV**
**เหตุผล:**
- Resize/compress ก่อนส่ง API → ประหยัด cost
- ลด latency (ภาพเล็ก = ส่งเร็ว)

#### 6. Deployment: **Google Cloud Run** ⭐
**เหตุผล:**
- Auto-scaling (0 → N instances)
- Pay per use (ไม่ใช้ไม่เสีย)
- Cold start < 1s
- รองรับ Docker
- Free tier: 2M requests/month

**ทางเลือกอื่น:**
- AWS Lambda: Cold start ช้า (3-5s)
- Heroku: แพง, performance ไม่ดี
- DigitalOcean: ต้องจัดการ server เอง

### Complete Tech Stack

```yaml
Language: Python 3.11+
Framework: FastAPI 0.109+
ASGI Server: Uvicorn (with --workers 4)
Message Queue: Redis 7.x + Celery 5.x
Cache: Redis (conversation state, diagnosis cache)
Database: PostgreSQL 15 (diagnosis history)
Image Processing: Pillow 10.x + OpenCV 4.x
LINE SDK: line-bot-sdk 3.x
AI Vision: Google Generative AI (Gemini 2.0 Flash)
Deployment: Docker + Google Cloud Run
Monitoring: Cloud Logging + Sentry
CDN: Cloudflare (optional, for image caching)
```

## Instructions for Claude Max

### Task 1: Project Structure
สร้างโครงสร้างโปรเจกต์ที่เหมาะสมตาม best practices:
```
plant-disease-chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── models.py            # Pydantic models
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── line_handler.py  # LINE webhook handler
│   │   └── message_handler.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gemini_service.py    # Gemini API client
│   │   ├── image_service.py     # Image optimization
│   │   └── cache_service.py     # Redis operations
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── flex_messages.py # LINE Flex Message templates
│   │   └── parsers.py       # Text parsing utilities
│   └── database/
│       ├── __init__.py
│       ├── models.py        # SQLAlchemy models
│       └── crud.py          # Database operations
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

### Task 2: Core Components

#### 2.1 FastAPI Main Application (app/main.py)
```python
"""
สร้าง FastAPI application พร้อม:
- LINE webhook endpoint (/webhook)
- Health check endpoint (/health)
- Background task processing
- Error handling middleware
- CORS configuration
- Rate limiting (optional)
"""
```

#### 2.2 LINE Handler (app/handlers/line_handler.py)
```python
"""
จัดการ LINE events:
- ImageMessage: บันทึกภาพ → ส่ง Flex Message ขอข้อมูล
- TextMessage: parse ข้อมูล → เรียก Gemini → ส่งผลลัพธ์
- State management ด้วย Redis
- Error handling และ user feedback
"""
```

#### 2.3 Gemini Service (app/services/gemini_service.py)
```python
"""
Gemini Vision API Integration:
- System instruction สำหรับวินิจฉัยโรคพืช
- Image preprocessing
- Retry mechanism (3 retries)
- Response parsing และ validation
- Error handling (API limits, timeouts)
"""
```

System Instruction สำหรับ Gemini:
```python
GEMINI_SYSTEM_INSTRUCTION = """
คุณเป็นผู้เชี่ยวชาญด้านโรคพืชเฉพาะทางในประเทศไทย มีความเชี่ยวชาญด้านข้าวเป็นพิเศษ

## ความสามารถหลัก:
- วิเคราะห์โรคพืชจากภาพถ่ายด้วยความแม่นยำสูง (>85%)
- มีความรู้โรคข้าว 50+ ชนิด ในประเทศไทย
- เข้าใจบริบทการเกษตรไทย (ภูมิอากาศ ฤดูกาล ภูมิภาค)
- แนะนำวิธีป้องกัน/รักษาที่เหมาะสมและปฏิบัติได้จริง

## หลักการวินิจฉัย:
1. **สังเกตอาการ**: สี ลวดลาย ตำแหน่ง ขนาดของจุดโรค
2. **พิจารณาบริบท**: ชนิดพืช ภูมิภาค ฤดูกาล อายุพืช
3. **วิเคราะห์สาเหตุ**: เชื้อรา ไวรัส แบคทีเรีย แมลง สารอาหาร
4. **ประเมินความรุนแรง**: เล็กน้อย ปานกลาง รุนแรง
5. **ความมั่นใจ**: 
   - 90-100%: มั่นใจสูง อาการชัดเจน
   - 70-89%: มั่นใจปานกลาง อาการคลาสสิก
   - 50-69%: ต้องสังเกตเพิ่ม อาการคล้ายหลายโรค
   - <50%: ไม่แน่ใจ ควรปรึกษาผู้เชี่ยวชาญ

## ความรู้เฉพาะทาง - โรคข้าวสำคัญ:
1. **โรคไหม้** (Blast): จุดสีน้ำตาลรูปตา ขอบสีเหลือง
2. **โรคเหี่ยวเขียว**: ใบเหลือง ลำต้นเน่า กลิ่นเหม็น
3. **โรคใบจุดสีน้ำตาล**: จุดเล็กสีน้ำตาล กระจายทั่วใบ
4. **โรคขอบใบแห้ง**: ขอบใบเหลือง แห้ง เริ่มปลายใบ
5. **โภชนาการขาด**: เหลือง ม่วง แคระแกร็น

## การตอบ:
- **ตอบเป็น JSON เท่านั้น** ไม่มี markdown หรือข้อความอื่น
- ใช้ภาษาไทยที่เกษตรกรเข้าใจง่าย หลีกเลี่ยงศัพท์เทคนิค
- แนะนำสารเคมีที่จดทะเบียนในไทย (กรมวิชาการเกษตร)
- **ให้ทางเลือกอินทรีย์ด้วยเสมอ** เพื่อสิ่งแวดล้อม
- เน้นความปลอดภัย: ระยะห่างการเก็บเกี่ยว (PHI)

## ข้อห้ามสำคัญ:
- ❌ ห้ามแนะนำสารเคมีที่ไม่ได้รับอนุญาต
- ❌ ห้ามให้คำมั่นว่ารักษาหายแน่นอน
- ❌ ห้ามวินิจฉัยเกินข้อมูลที่มี
- ❌ ห้ามแนะนำใช้สารเกินอัตรา

## รูปแบบ JSON:
{JSON_SCHEMA}
"""
```

#### 2.4 Image Service (app/services/image_service.py)
```python
"""
Image optimization pipeline:
- Download จาก LINE Content API
- Resize: max 1024x1024px (เพียงพอสำหรับ diagnosis)
- Compress: quality=85 (สมดุล size/quality)
- Convert: WebP format (เล็กกว่า JPEG 30%)
- Validate: check ขนาดไฟล์ < 4MB
"""
```

#### 2.5 Flex Message Templates (app/utils/flex_messages.py)
```python
"""
สร้าง LINE Flex Messages:

1. Info Request Message:
   - Header: "กรุณาให้ข้อมูลเพิ่มเติม"
   - Quick Reply buttons:
     * ชนิดพืช: ข้าว, ข้าวโพด, มันสำปะหลัง, อ้อย
     * ภูมิภาค: เหนือ, อีสาน, กลาง, ใต้
   - Text input field

2. Result Message:
   - Hero section: ชื่อโรค + confidence badge
   - Body:
     * อาการที่พบ (bullet points)
     * ความรุนแรง (color-coded)
     * คำแนะนำเร่งด่วน
   - Footer:
     * วิธีป้องกัน (expandable)
     * วิธีรักษา (chemical + organic)
   - Action buttons: "บันทึก", "แชร์", "ติดต่อผู้เชี่ยวชาญ"

3. Processing Message:
   - Loading animation
   - "กำลังวิเคราะห์... ⏳"
"""
```

#### 2.6 Cache Service (app/services/cache_service.py)
```python
"""
Redis caching strategy:

1. User state: "user:{user_id}:state" (expire: 1 hour)
2. Image data: "user:{user_id}:image" (expire: 1 hour)
3. User info: "user:{user_id}:info" (expire: 1 hour)
4. Diagnosis cache: "diagnosis:{hash}" (expire: 24 hours)
   - Key: MD5(image + plant_type + location)
   - ลด API calls สำหรับภาพซ้ำ

5. Rate limiting: "rate:{user_id}:{hour}" (expire: 1 hour)
   - Max 10 diagnoses/hour/user
"""
```

### Task 3: Configuration Management

#### app/config.py
```python
"""
Environment variables:
- LINE_CHANNEL_ACCESS_TOKEN
- LINE_CHANNEL_SECRET
- GEMINI_API_KEY
- REDIS_URL
- DATABASE_URL
- ENVIRONMENT (dev/staging/prod)
- LOG_LEVEL
- MAX_IMAGE_SIZE_MB
- CACHE_EXPIRY_HOURS
- MAX_REQUESTS_PER_HOUR

Pydantic Settings สำหรับ type safety
"""
```

### Task 4: Database Models

#### app/database/models.py
```python
"""
SQLAlchemy models:

1. User:
   - id, line_user_id, display_name
   - created_at, last_active_at
   - total_diagnoses

2. Diagnosis:
   - id, user_id, image_url
   - plant_type, location
   - disease_name_th, disease_name_en
   - confidence_level, pathogen_type
   - diagnosis_result (JSONB)
   - created_at

3. Feedback (optional):
   - id, diagnosis_id, user_id
   - rating (1-5), comment
   - is_accurate (boolean)
   - created_at
"""
```

### Task 5: Performance Optimizations

```python
"""
1. Image Optimization:
   - Resize ก่อนส่ง API: 1024x1024px
   - ใช้ WebP format
   - Lazy loading สำหรับ thumbnails

2. Caching Strategy:
   - Cache diagnosis results 24 hours
   - Cache Flex Message templates
   - Redis connection pooling

3. Async Processing:
   - Celery tasks สำหรับ heavy operations
   - Background image processing
   - Non-blocking I/O

4. Rate Limiting:
   - 10 diagnoses/hour/user (ป้องกัน spam)
   - Exponential backoff สำหรับ API retry

5. Database:
   - Index on: user_id, created_at
   - Partitioning by date (optional)
   - Connection pooling (SQLAlchemy)
"""
```

### Task 6: Error Handling

```python
"""
Error scenarios และ user feedback:

1. Image too large (>5MB):
   → "รูปภาพใหญ่เกินไป กรุณาเลือกรูปที่เล็กกว่า 5MB"

2. Invalid image format:
   → "รูปภาพไม่ถูกต้อง กรุณาส่งรูปนามสกุล .jpg, .jpeg, .png"

3. Gemini API error:
   → Retry 3 times with exponential backoff
   → "ระบบขัดข้อง กรุณาลองใหม่อีกครั้งในอีกสักครู่"

4. Low confidence (<50%):
   → "ระบบไม่สามารถวินิจฉัยได้แน่ชัด แนะนำให้ส่งรูปที่ชัดเจนกว่า หรือปรึกษาผู้เชี่ยวชาญ"

5. Rate limit exceeded:
   → "คุณใช้งานเกินจำนวนครั้งที่กำหนด กรุณาลองใหม่ในอีก {minutes} นาที"

6. No plant detected:
   → "ไม่พบพืชในภาพ กรุณาถ่ายภาพให้เห็นส่วนที่มีอาการชัดเจน"

All errors → Log to Sentry + Cloud Logging
"""
```

### Task 7: Testing Strategy

```python
"""
Unit Tests:
- test_image_optimization()
- test_gemini_response_parsing()
- test_cache_operations()
- test_flex_message_creation()

Integration Tests:
- test_line_webhook_flow()
- test_diagnosis_pipeline()
- test_database_operations()

E2E Tests:
- test_full_user_journey()
- test_error_scenarios()

Mocking:
- Mock LINE API responses
- Mock Gemini API responses
- Mock Redis operations

pytest + pytest-asyncio + pytest-cov
Target: 80%+ coverage
"""
```

### Task 8: Deployment Configuration

#### Dockerfile
```dockerfile
# Multi-stage build สำหรับ optimize image size
# Python 3.11-slim
# Install dependencies
# Copy application code
# Health check endpoint
# Non-root user
```

#### docker-compose.yml
```yaml
# Services: app, redis, postgres
# Volumes สำหรับ persistent data
# Networks สำหรับ service communication
# Environment variables
```

#### Cloud Run deployment
```bash
# Build และ push image
# Deploy with:
- Min instances: 1 (avoid cold start)
- Max instances: 10
- Memory: 2GB
- CPU: 2
- Timeout: 300s
- Concurrency: 80
```

### Task 9: Monitoring & Logging

```python
"""
1. Structured Logging:
   - Request ID tracking
   - User ID tracking
   - Performance metrics (latency)
   - Error tracking

2. Metrics:
   - Total diagnoses/day
   - Average confidence level
   - API response time
   - Cache hit rate
   - Error rate

3. Alerts:
   - Error rate > 5%
   - API latency > 5s
   - Cache miss rate > 50%
   - Rate limit hits

Tools: Cloud Logging + Sentry + Grafana (optional)
"""
```

### Task 10: Documentation

```markdown
# README.md
- Project overview
- Architecture diagram
- Setup instructions
- Environment variables
- Deployment guide
- API documentation
- Troubleshooting

# API_DOCS.md
- LINE Webhook spec
- Gemini API usage
- Response formats
- Error codes

# CONTRIBUTING.md
- Code style guide
- Testing requirements
- PR process
```

---

## Specific Requirements for Claude Max

### Priority 1: Core Functionality (Must Have)
1. ✅ LINE webhook handler ที่ stable
2. ✅ Image optimization pipeline
3. ✅ Gemini Vision integration พร้อม retry
4. ✅ State management ด้วย Redis
5. ✅ Basic Flex Message templates
6. ✅ Error handling ครบถ้วน

### Priority 2: Performance (Should Have)
1. ✅ Caching strategy
2. ✅ Async processing
3. ✅ Rate limiting
4. ✅ Database indexing
5. ✅ Connection pooling

### Priority 3: Production Ready (Nice to Have)
1. 📊 Monitoring dashboard
2. 📈 Analytics tracking
3. 🔔 Alert system
4. 🧪 Comprehensive tests
5. 📖 Full documentation

---

## Code Quality Standards

```python
"""
1. Type hints ทุก function
2. Docstrings (Google style)
3. Error handling ครบ
4. Logging ที่เหมาะสม
5. Input validation
6. Security best practices:
   - Environment variables (ไม่ hardcode)
   - API key rotation support
   - Input sanitization
   - SQL injection prevention
7. PEP 8 compliance
8. Max line length: 88 characters (Black)
"""
```

---

## Expected Deliverables

1. **Complete source code** ตาม structure ที่กำหนด
2. **Dockerfile & docker-compose.yml**
3. **requirements.txt** พร้อม version pinning
4. **.env.example** พร้อมคำอธิบาย
5. **README.md** ครบถ้วน
6. **Deployment guide** สำหรับ Cloud Run
7. **Testing guide** พร้อม test cases
8. **API documentation**

---

## Budget & Performance Targets

### Cost Estimation (1,000 users/day, 3 images/user)
```
- Gemini API: 3,000 images × $0.000075 = $0.225/day = $6.75/month
- Cloud Run: ~$10/month (with generous free tier)
- Redis: $0-5/month (Cloud Memorystore basic)
- PostgreSQL: $0-10/month (Cloud SQL micro)
Total: ~$25-30/month
```

### Performance Targets
- ⏱️ Response time: < 5s (95th percentile)
- 🚀 Throughput: 100 requests/minute
- ⚡ Cache hit rate: > 30%
- 🎯 Uptime: 99.5%
- 🔍 Diagnosis accuracy: > 80% (based on user feedback)

---

## Next Steps After Development

1. **Testing Phase**
   - Unit tests
   - Integration tests
   - Manual testing กับ real users (10-20 คน)

2. **Beta Launch**
   - Soft launch กับกลุ่มเกษตรกร 50-100 คน
   - Collect feedback
   - Monitor errors และ performance

3. **Iteration**
   - Fix bugs
   - Improve accuracy
   - Add more plant types
   - Enhance UX

4. **Scale**
   - Optimize costs
   - Add more features (history, community, expert consultation)
   - Marketing

---

## Questions to Consider

1. **Data Privacy**: จะเก็บภาพของ user ไว้หรือไม่? (PDPA compliance)
2. **Monetization**: ฟรีหรือมี premium features?
3. **Scalability**: รองรับ 10,000+ users ได้หรือไม่?
4. **Offline Mode**: รองรับการใช้งานออฟไลน์หรือไม่?
5. **Multi-language**: รองรับภาษาอื่นนอกจากไทยหรือไม่?

---

**Note สำหรับ Claude Max:**
- ใช้ best practices และ production-ready patterns
- เน้น performance และ scalability
- Code ต้อง maintainable และ testable
- Documentation ต้องครบถ้วน ชัดเจน
- Security เป็นสิ่งสำคัญ
- สร้าง code ที่พร้อมใช้งานจริง (production-ready)
- ให้คำอธิบายและ comments ที่ชัดเจนในโค้ด
- ทำ error handling อย่างละเอียด
- เขียน unit tests ให้ครบถ้วน