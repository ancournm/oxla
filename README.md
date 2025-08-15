# Oxla Backend Foundation

A comprehensive backend foundation for the Oxla project, featuring email service, file storage, user management, and monitoring capabilities.

## 🚀 Features Implemented

### Core Infrastructure
- **Database**: Prisma ORM with SQLite database
- **API**: RESTful API with Next.js App Router
- **Authentication**: NextAuth.js integration
- **WebSocket**: Real-time communication with Socket.IO
- **AI Integration**: z-ai-web-dev-sdk for AI capabilities

### Email Service
- **Background Task Queue**: Redis-based email processing with retry logic
- **Usage Limits**: Plan-based email quotas (Free: 500/month, Pro: 10,000/month, Enterprise: Unlimited)
- **Rate Limiting**: Per-minute limits to prevent abuse (Free: 5/min, Pro: 20/min, Enterprise: 100/min)
- **Monitoring**: Comprehensive email job tracking and metrics

### File Storage (Drive Service)
- **File Management**: Upload, download, delete files with metadata
- **Quota Enforcement**: Plan-based storage limits (Free: 5GB, Pro: 50GB, Enterprise: Unlimited)
- **Folder Organization**: Hierarchical folder structure with CRUD operations
- **Sharing**: Secure share links with time-limited access and permissions
- **Security**: JWT-based authentication and virus scan integration

### Monitoring & Metrics
- **Prometheus Metrics**: Comprehensive application metrics endpoint
- **Queue Monitoring**: Real-time email queue statistics
- **User Analytics**: Active users, usage patterns, and plan distribution
- **Performance Tracking**: Email success rates, processing times, and system health

### Developer Experience
- **OpenAPI Schema**: Complete API documentation in OpenAPI 3.0 format
- **Postman Collection**: Ready-to-use API testing collection
- **Comprehensive Documentation**: Setup guides, API references, and deployment instructions

## 📋 Plan Features

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| **Email Limits** | 500/month | 10,000/month | Unlimited |
| **Email Rate Limit** | 5/minute | 20/minute | 100/minute |
| **Storage** | 5 GB total | 50 GB total | Unlimited |
| **Max File Size** | 50 MB | 2 GB | Unlimited |
| **File Upload Rate** | 10/minute | 50/minute | 200/minute |
| **File Download Rate** | 50/minute | 200/minute | 1000/minute |

## 🏗️ Project Structure

```
oxla/
├── prisma/
│   └── schema.prisma              # Database schema
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth/              # Authentication endpoints
│   │   │   ├── email/             # Email service endpoints
│   │   │   ├── usage/             # Usage tracking endpoints
│   │   │   ├── metrics/           # Monitoring endpoints
│   │   │   ├── openapi/           # OpenAPI schema endpoint
│   │   │   ├── ai/                # AI integration endpoints
│   │   │   ├── search/            # Web search endpoints
│   │   │   └── images/            # Image generation endpoints
│   │   ├── layout.tsx             # Root layout
│   │   ├── page.tsx              # Home page
│   │   └── globals.css           # Global styles
│   ├── components/
│   │   └── ui/                   # UI components
│   ├── hooks/                     # Custom React hooks
│   ├── lib/
│   │   ├── db.ts                 # Database client
│   │   ├── auth.ts               # Authentication configuration
│   │   ├── socket.ts             # WebSocket setup
│   │   ├── redis.ts              # Redis client
│   │   ├── usage-limits.ts       # Usage limits and rate limiting
│   │   ├── email-service.ts      # Email service implementation
│   │   ├── email-queue-worker.ts # Email queue worker
│   │   └── middleware.ts         # Rate limiting middleware
│   └── globals.css
├── docs/
│   └── postman/
│       └── oxla-api-collection.json  # Postman API collection
├── worker.js                      # Email worker script
├── Dockerfile.worker              # Worker Docker configuration
├── docker-compose.yml            # Container orchestration
├── prometheus.yml               # Prometheus configuration
├── package.json
├── tailwind.config.ts
├── tsconfig.json
├── next.config.ts
└── .env.example                  # Environment variables template
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- Docker and Docker Compose
- Redis (for background tasks and caching)

### 1. Install Dependencies
```bash
npm install
```

### 2. Set Up Environment Variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Set Up Database
```bash
# Generate Prisma client
npm run db:generate

# Push schema to database
npm run db:push
```

### 4. Start Services with Docker
```bash
# Start all services (PostgreSQL, Redis, Next.js, Email Worker, Monitoring)
docker-compose up -d
```

### 5. Start Development Server
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## 🔧 API Endpoints

### Email Service
- `POST /api/email` - Create email job
- `GET /api/email` - Get email jobs (with optional status filter)

### Usage Tracking
- `GET /api/usage` - Get current usage statistics and limits

### Monitoring
- `GET /api/metrics` - Get Prometheus metrics

### Developer Tools
- `GET /api/openapi` - Get OpenAPI schema
- `/docs/postman/` - Postman API collection

## 📊 Monitoring

### Prometheus Metrics
Access metrics at `http://localhost:3000/api/metrics`

Key metrics include:
- `oxla_total_users` - Total number of users
- `oxla_email_jobs_total` - Total email jobs
- `oxla_email_jobs_by_status` - Jobs by status
- `oxla_email_queue_length` - Current queue length
- `oxla_total_files` - Total files stored
- `oxla_active_users` - Active users (24h)

### Grafana Dashboard
Access Grafana at `http://localhost:3001` (admin/admin)

### Flower (Celery Monitoring)
Access Flower at `http://localhost:5555`

## 🛠️ Development

### Running Tests
```bash
# Run all tests
npm test

# Run specific test files
npm test -- email.test.ts
npm test -- rate-limits.test.ts
```

### Code Quality
```bash
# Run linting
npm run lint

# Format code
npm run format
```

### Database Migrations
```bash
# Create new migration
npx prisma migrate dev --name migration_name

# Apply migrations
npx prisma migrate deploy

# Reset database
npx prisma migrate reset
```

## 🔒 Security Features

### Authentication
- JWT-based authentication with NextAuth.js
- Secure session management
- Role-based access control

### Rate Limiting
- Redis-based rate limiting
- Plan-specific limits
- Graceful degradation with proper HTTP status codes

### Data Protection
- Encrypted sensitive data
- Secure file storage with access controls
- Audit logging for all operations

## 📈 Performance

### Email Processing
- Background task queue with Redis
- Retry logic with exponential backoff
- Concurrent processing with configurable limits

### File Storage
- Chunked uploads for large files
- Streaming downloads
- Efficient metadata storage

### Caching
- Redis-based caching for frequently accessed data
- Cache invalidation strategies
- Performance monitoring

## 🚀 Deployment

### Production Setup
1. **Environment Configuration**: Set up production environment variables
2. **Database**: Use PostgreSQL in production (not SQLite)
3. **Redis**: Use managed Redis service (ElastiCache, etc.)
4. **Storage**: Use cloud storage (S3, GCS, etc.) for file storage
5. **Monitoring**: Set up comprehensive monitoring and alerting

### Docker Deployment
```bash
# Build and run production containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Manual Deployment
```bash
# Build Next.js application
npm run build

# Start production server
npm start
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow TypeScript best practices
- Write comprehensive tests
- Update documentation
- Use conventional commit messages
- Ensure code passes linting and formatting checks

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Contact the development team

---

**Built with ❤️ using Next.js, Prisma, Redis, and modern web technologies**