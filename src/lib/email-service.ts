import { db } from '@/lib/db'
import { connectRedis } from '@/lib/redis'
import { checkEmailQuota, checkEmailRateLimit, incrementUsage } from '@/lib/usage-limits'

export interface EmailJobData {
  userId: string
  type: 'SEND' | 'RECEIVE'
  recipient: string
  subject?: string
  content?: string
  scheduledAt?: Date
}

export class EmailService {
  async createEmailJob(data: EmailJobData): Promise<{ success: boolean; jobId?: string; error?: string }> {
    try {
      // Check user's plan and quotas
      const user = await db.user.findUnique({
        where: { id: data.userId },
      })
      
      if (!user) {
        return { success: false, error: 'User not found' }
      }
      
      // Check monthly quota
      const quotaCheck = await checkEmailQuota(data.userId, user.plan)
      if (!quotaCheck.allowed) {
        return { success: false, error: 'Monthly email quota exceeded' }
      }
      
      // Check rate limit
      const rateLimitCheck = await checkEmailRateLimit(data.userId, user.plan)
      if (!rateLimitCheck.allowed) {
        return { success: false, error: 'Rate limit exceeded' }
      }
      
      // Create email job in database
      const emailJob = await db.emailJob.create({
        data: {
          userId: data.userId,
          type: data.type,
          recipient: data.recipient,
          subject: data.subject,
          content: data.content,
          scheduledAt: data.scheduledAt,
          status: 'PENDING',
        },
      })
      
      // Add job to Redis queue
      const redis = await connectRedis()
      await redis.lpush('email_queue', JSON.stringify({
        jobId: emailJob.id,
        ...data,
      }))
      
      // Update usage tracking
      if (data.type === 'SEND') {
        await incrementUsage(data.userId, 'emails_sent')
      } else {
        await incrementUsage(data.userId, 'emails_received')
      }
      
      return { success: true, jobId: emailJob.id }
    } catch (error) {
      console.error('Error creating email job:', error)
      return { success: false, error: 'Internal server error' }
    }
  }
  
  async processEmailJob(jobId: string): Promise<{ success: boolean; error?: string }> {
    try {
      const emailJob = await db.emailJob.findUnique({
        where: { id: jobId },
      })
      
      if (!emailJob) {
        return { success: false, error: 'Job not found' }
      }
      
      // Update job status to processing
      await db.emailJob.update({
        where: { id: jobId },
        data: { status: 'PROCESSING' },
      })
      
      // Simulate email sending (replace with actual email service)
      const emailSent = await this.sendEmail(emailJob)
      
      if (emailSent) {
        await db.emailJob.update({
          where: { id: jobId },
          data: { 
            status: 'COMPLETED',
            completedAt: new Date(),
          },
        })
        return { success: true }
      } else {
        throw new Error('Email sending failed')
      }
    } catch (error) {
      console.error('Error processing email job:', error)
      
      // Update job status to failed or retry
      const emailJob = await db.emailJob.findUnique({
        where: { id: jobId },
      })
      
      if (emailJob && emailJob.retryCount < emailJob.maxRetries) {
        await db.emailJob.update({
          where: { id: jobId },
          data: {
            status: 'RETRYING',
            retryCount: emailJob.retryCount + 1,
          },
        })
        
        // Re-add to queue for retry
        const redis = await connectRedis()
        await redis.lpush('email_queue', JSON.stringify({
          jobId: emailJob.id,
          userId: emailJob.userId,
          type: emailJob.type,
          recipient: emailJob.recipient,
          subject: emailJob.subject,
          content: emailJob.content,
        }))
      } else {
        await db.emailJob.update({
          where: { id: jobId },
          data: {
            status: 'FAILED',
            failedAt: new Date(),
            error: error instanceof Error ? error.message : 'Unknown error',
          },
        })
      }
      
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' }
    }
  }
  
  private async sendEmail(emailJob: any): Promise<boolean> {
    // Simulate email sending
    // In a real implementation, you would use an email service like SendGrid, Mailgun, etc.
    console.log(`Sending email to ${emailJob.recipient}`)
    console.log(`Subject: ${emailJob.subject}`)
    console.log(`Content: ${emailJob.content}`)
    
    // Simulate success/failure (90% success rate)
    return Math.random() > 0.1
  }
  
  async getEmailJobs(userId: string, status?: string): Promise<any[]> {
    const whereClause: any = { userId }
    if (status) {
      whereClause.status = status
    }
    
    return await db.emailJob.findMany({
      where: whereClause,
      orderBy: { createdAt: 'desc' },
    })
  }
  
  async getEmailUsage(userId: string): Promise<{ sent: number; received: number; month: number; year: number }> {
    const now = new Date()
    const month = now.getMonth() + 1
    const year = now.getFullYear()
    
    let usage = await db.emailUsage.findUnique({
      where: { userId_month_year: { userId, month, year } },
    })
    
    if (!usage) {
      usage = await db.emailUsage.create({
        data: {
          userId,
          month,
          year,
          emailsSent: 0,
          emailsReceived: 0,
        },
      })
    }
    
    return {
      sent: usage.emailsSent,
      received: usage.emailsReceived,
      month: usage.month,
      year: usage.year,
    }
  }
}

export const emailService = new EmailService()