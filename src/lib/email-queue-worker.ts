import { connectRedis } from '@/lib/redis'
import { emailService } from '@/lib/email-service'
import { db } from '@/lib/db'

export class EmailQueueWorker {
  private isRunning = false
  private processingInterval: NodeJS.Timeout | null = null
  
  constructor(private intervalMs: number = 5000) {}
  
  async start(): Promise<void> {
    if (this.isRunning) {
      console.log('Email queue worker is already running')
      return
    }
    
    console.log('Starting email queue worker...')
    this.isRunning = true
    
    // Process queue immediately
    await this.processQueue()
    
    // Set up periodic processing
    this.processingInterval = setInterval(async () => {
      await this.processQueue()
    }, this.intervalMs)
  }
  
  async stop(): Promise<void> {
    if (!this.isRunning) {
      console.log('Email queue worker is not running')
      return
    }
    
    console.log('Stopping email queue worker...')
    this.isRunning = false
    
    if (this.processingInterval) {
      clearInterval(this.processingInterval)
      this.processingInterval = null
    }
  }
  
  private async processQueue(): Promise<void> {
    try {
      const redis = await connectRedis()
      
      // Process up to 10 jobs at a time
      for (let i = 0; i < 10; i++) {
        const jobData = await redis.rpop('email_queue')
        
        if (!jobData) {
          break // No more jobs in queue
        }
        
        try {
          const job = JSON.parse(jobData)
          console.log(`Processing email job: ${job.jobId}`)
          
          const result = await emailService.processEmailJob(job.jobId)
          
          if (result.success) {
            console.log(`Email job completed successfully: ${job.jobId}`)
          } else {
            console.error(`Email job failed: ${job.jobId}`, result.error)
          }
        } catch (error) {
          console.error('Error processing email job:', error)
        }
      }
    } catch (error) {
      console.error('Error in email queue worker:', error)
    }
  }
  
  async getQueueStats(): Promise<{ pending: number; processing: number; failed: number }> {
    try {
      const redis = await connectRedis()
      const pending = await redis.llen('email_queue')
      
      const processing = await db.emailJob.count({
        where: { status: 'PROCESSING' },
      })
      
      const failed = await db.emailJob.count({
        where: { status: 'FAILED' },
      })
      
      return { pending, processing, failed }
    } catch (error) {
      console.error('Error getting queue stats:', error)
      return { pending: 0, processing: 0, failed: 0 }
    }
  }
}

// Create a singleton instance
export const emailQueueWorker = new EmailQueueWorker()

// Auto-start the worker when this module is imported
if (process.env.NODE_ENV !== 'test') {
  emailQueueWorker.start().catch(console.error)
}