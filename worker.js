const { PrismaClient } = require('@prisma/client')
const { createClient } = require('redis')

// Initialize Prisma client
const prisma = new PrismaClient()

// Initialize Redis client
const redis = createClient({
  url: process.env.REDIS_URL || 'redis://localhost:6379',
})

redis.on('error', (err) => console.log('Redis Client Error', err))
redis.on('connect', () => console.log('Redis Client Connected'))

// Email service class
class EmailService {
  async sendEmail(emailJob) {
    try {
      console.log(`Processing email job: ${emailJob.id}`)
      console.log(`Sending email to: ${emailJob.recipient}`)
      
      // Update job status to processing
      await prisma.emailJob.update({
        where: { id: emailJob.id },
        data: { status: 'PROCESSING' },
      })
      
      // Simulate email sending (replace with actual email service)
      const success = await this.simulateEmailSend(emailJob)
      
      if (success) {
        await prisma.emailJob.update({
          where: { id: emailJob.id },
          data: {
            status: 'COMPLETED',
            completedAt: new Date(),
          },
        })
        console.log(`Email sent successfully: ${emailJob.id}`)
        return true
      } else {
        throw new Error('Email sending failed')
      }
    } catch (error) {
      console.error(`Error processing email job ${emailJob.id}:`, error)
      
      // Check if we should retry
      if (emailJob.retryCount < emailJob.maxRetries) {
        await prisma.emailJob.update({
          where: { id: emailJob.id },
          data: {
            status: 'RETRYING',
            retryCount: emailJob.retryCount + 1,
          },
        })
        
        // Re-add to queue for retry
        await redis.lpush('email_queue', JSON.stringify({
          jobId: emailJob.id,
          userId: emailJob.userId,
          type: emailJob.type,
          recipient: emailJob.recipient,
          subject: emailJob.subject,
          content: emailJob.content,
        }))
        
        console.log(`Email job queued for retry: ${emailJob.id}`)
      } else {
        await prisma.emailJob.update({
          where: { id: emailJob.id },
          data: {
            status: 'FAILED',
            failedAt: new Date(),
            error: error.message,
          },
        })
        console.log(`Email job failed permanently: ${emailJob.id}`)
      }
      
      return false
    }
  }
  
  async simulateEmailSend(emailJob) {
    // Simulate email sending delay
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 3000))
    
    // Simulate success/failure (90% success rate)
    return Math.random() > 0.1
  }
}

// Worker class
class EmailWorker {
  constructor() {
    this.emailService = new EmailService()
    this.isRunning = false
    this.processingInterval = null
  }
  
  async start() {
    if (this.isRunning) {
      console.log('Email worker is already running')
      return
    }
    
    console.log('Starting email worker...')
    this.isRunning = true
    
    // Connect to Redis
    await redis.connect()
    
    // Process queue immediately
    await this.processQueue()
    
    // Set up periodic processing
    this.processingInterval = setInterval(async () => {
      await this.processQueue()
    }, 5000) // Process every 5 seconds
  }
  
  async stop() {
    if (!this.isRunning) {
      console.log('Email worker is not running')
      return
    }
    
    console.log('Stopping email worker...')
    this.isRunning = false
    
    if (this.processingInterval) {
      clearInterval(this.processingInterval)
      this.processingInterval = null
    }
    
    await redis.disconnect()
  }
  
  async processQueue() {
    try {
      // Process up to 10 jobs at a time
      for (let i = 0; i < 10; i++) {
        const jobData = await redis.rpop('email_queue')
        
        if (!jobData) {
          break // No more jobs in queue
        }
        
        try {
          const job = JSON.parse(jobData)
          
          // Get the full email job from database
          const emailJob = await prisma.emailJob.findUnique({
            where: { id: job.jobId },
          })
          
          if (!emailJob) {
            console.error(`Email job not found: ${job.jobId}`)
            continue
          }
          
          // Process the email job
          await this.emailService.sendEmail(emailJob)
          
        } catch (error) {
          console.error('Error processing email job:', error)
        }
      }
    } catch (error) {
      console.error('Error in email queue processing:', error)
    }
  }
  
  async getQueueStats() {
    try {
      const pending = await redis.llen('email_queue')
      const processing = await prisma.emailJob.count({
        where: { status: 'PROCESSING' },
      })
      const failed = await prisma.emailJob.count({
        where: { status: 'FAILED' },
      })
      
      return { pending, processing, failed }
    } catch (error) {
      console.error('Error getting queue stats:', error)
      return { pending: 0, processing: 0, failed: 0 }
    }
  }
}

// Main function
async function main() {
  const worker = new EmailWorker()
  
  // Handle graceful shutdown
  process.on('SIGTERM', async () => {
    console.log('Received SIGTERM, shutting down gracefully...')
    await worker.stop()
    await prisma.$disconnect()
    process.exit(0)
  })
  
  process.on('SIGINT', async () => {
    console.log('Received SIGINT, shutting down gracefully...')
    await worker.stop()
    await prisma.$disconnect()
    process.exit(0)
  })
  
  // Start the worker
  await worker.start()
  console.log('Email worker started successfully')
}

// Run the worker
main().catch(async (error) => {
  console.error('Fatal error in email worker:', error)
  process.exit(1)
})