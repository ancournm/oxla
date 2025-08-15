import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { connectRedis } from '@/lib/redis'
import { emailQueueWorker } from '@/lib/email-queue-worker'

export async function GET(request: NextRequest) {
  try {
    const redis = await connectRedis()
    
    // Get current timestamp
    const now = new Date()
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000)
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000)
    
    // Get email job statistics
    const totalJobs = await db.emailJob.count()
    const completedJobs = await db.emailJob.count({ where: { status: 'COMPLETED' } })
    const failedJobs = await db.emailJob.count({ where: { status: 'FAILED' } })
    const pendingJobs = await db.emailJob.count({ where: { status: 'PENDING' } })
    const processingJobs = await db.emailJob.count({ where: { status: 'PROCESSING' } })
    const retryingJobs = await db.emailJob.count({ where: { status: 'RETRYING' } })
    
    // Get jobs from last hour and last day
    const jobsLastHour = await db.emailJob.count({
      where: { createdAt: { gte: oneHourAgo } },
    })
    const jobsLastDay = await db.emailJob.count({
      where: { createdAt: { gte: oneDayAgo } },
    })
    
    // Get completed jobs by time period
    const completedLastHour = await db.emailJob.count({
      where: { 
        status: 'COMPLETED',
        completedAt: { gte: oneHourAgo },
      },
    })
    const completedLastDay = await db.emailJob.count({
      where: { 
        status: 'COMPLETED',
        completedAt: { gte: oneDayAgo },
      },
    })
    
    // Get failed jobs by time period
    const failedLastHour = await db.emailJob.count({
      where: { 
        status: 'FAILED',
        failedAt: { gte: oneHourAgo },
      },
    })
    const failedLastDay = await db.emailJob.count({
      where: { 
        status: 'FAILED',
        failedAt: { gte: oneDayAgo },
      },
    })
    
    // Get user statistics
    const totalUsers = await db.user.count()
    const freeUsers = await db.user.count({ where: { plan: 'FREE' } })
    const proUsers = await db.user.count({ where: { plan: 'PRO' } })
    const enterpriseUsers = await db.user.count({ where: { plan: 'ENTERPRISE' } })
    
    // Get active users (users with activity in the last 24 hours)
    const activeUsers = await db.user.count({
      where: {
        OR: [
          { emailUsage: { some: { updatedAt: { gte: oneDayAgo } } } },
          { rateLimits: { some: { updatedAt: { gte: oneDayAgo } } } },
          { emailJob: { some: { createdAt: { gte: oneDayAgo } } } },
          { files: { some: { createdAt: { gte: oneDayAgo } } } },
        ],
      },
    })
    
    // Get file statistics
    const totalFiles = await db.file.count()
    const totalFileSize = await db.file.aggregate({
      _sum: { size: true },
    })
    const filesLastHour = await db.file.count({
      where: { createdAt: { gte: oneHourAgo } },
    })
    const filesLastDay = await db.file.count({
      where: { createdAt: { gte: oneDayAgo } },
    })
    
    // Get folder statistics
    const totalFolders = await db.folder.count()
    
    // Get share statistics
    const totalShares = await db.share.count()
    const activeShares = await db.share.count({
      where: {
        OR: [
          { expiresAt: { gte: now } },
          { expiresAt: null },
        ],
      },
    })
    
    // Get queue statistics
    const queueStats = await emailQueueWorker.getQueueStats()
    const queueLength = queueStats.pending
    
    // Get email usage statistics
    const emailUsage = await db.emailUsage.findMany({
      where: {
        OR: [
          { month: now.getMonth() + 1, year: now.getFullYear() },
          { month: now.getMonth(), year: now.getFullYear() },
        ],
      },
    })
    
    const currentMonthEmails = emailUsage.find(
      usage => usage.month === now.getMonth() + 1 && usage.year === now.getFullYear()
    ) || { emailsSent: 0, emailsReceived: 0 }
    
    const lastMonthEmails = emailUsage.find(
      usage => usage.month === now.getMonth() && usage.year === now.getFullYear()
    ) || { emailsSent: 0, emailsReceived: 0 }
    
    // Calculate success rates
    const totalCompletedAndFailed = completedJobs + failedJobs
    const successRate = totalCompletedAndFailed > 0 ? (completedJobs / totalCompletedAndFailed) * 100 : 0
    const successRateLastHour = jobsLastHour > 0 ? (completedLastHour / jobsLastHour) * 100 : 0
    const successRateLastDay = jobsLastDay > 0 ? (completedLastDay / jobsLastDay) * 100 : 0
    
    // Calculate average processing time (mock data for now)
    const avgProcessingTime = 2.5 // seconds
    
    // Generate Prometheus metrics
    const metrics = [
      '# HELP oxla_total_users Total number of users',
      '# TYPE oxla_total_users gauge',
      `oxla_total_users ${totalUsers}`,
      '',
      '# HELP oxla_users_by_plan Number of users by plan',
      '# TYPE oxla_users_by_plan gauge',
      `oxla_users_by_plan{plan="FREE"} ${freeUsers}`,
      `oxla_users_by_plan{plan="PRO"} ${proUsers}`,
      `oxla_users_by_plan{plan="ENTERPRISE"} ${enterpriseUsers}`,
      '',
      '# HELP oxla_active_users Number of active users (last 24h)',
      '# TYPE oxla_active_users gauge',
      `oxla_active_users ${activeUsers}`,
      '',
      '# HELP oxla_email_jobs_total Total number of email jobs',
      '# TYPE oxla_email_jobs_total counter',
      `oxla_email_jobs_total ${totalJobs}`,
      '',
      '# HELP oxla_email_jobs_by_status Number of email jobs by status',
      '# TYPE oxla_email_jobs_by_status gauge',
      `oxla_email_jobs_by_status{status="COMPLETED"} ${completedJobs}`,
      `oxla_email_jobs_by_status{status="FAILED"} ${failedJobs}`,
      `oxla_email_jobs_by_status{status="PENDING"} ${pendingJobs}`,
      `oxla_email_jobs_by_status{status="PROCESSING"} ${processingJobs}`,
      `oxla_email_jobs_by_status{status="RETRYING"} ${retryingJobs}`,
      '',
      '# HELP oxla_email_jobs_rate Email jobs creation rate',
      '# TYPE oxla_email_jobs_rate gauge',
      `oxla_email_jobs_rate{period="1h"} ${jobsLastHour}`,
      `oxla_email_jobs_rate{period="1d"} ${jobsLastDay}`,
      '',
      '# HELP oxla_email_completion_rate Email job completion rate',
      '# TYPE oxla_email_completion_rate gauge',
      `oxla_email_completion_rate{period="1h"} ${successRateLastHour}`,
      `oxla_email_completion_rate{period="1d"} ${successRateLastDay}`,
      `oxla_email_completion_rate{period="total"} ${successRate}`,
      '',
      '# HELP oxla_email_queue_length Current email queue length',
      '# TYPE oxla_email_queue_length gauge',
      `oxla_email_queue_length ${queueLength}`,
      '',
      '# HELP oxla_email_queue_by_status Email queue statistics by status',
      '# TYPE oxla_email_queue_by_status gauge',
      `oxla_email_queue_by_status{status="pending"} ${queueStats.pending}`,
      `oxla_email_queue_by_status{status="processing"} ${queueStats.processing}`,
      `oxla_email_queue_by_status{status="failed"} ${queueStats.failed}`,
      '',
      '# HELP oxla_total_files Total number of files',
      '# TYPE oxla_total_files counter',
      `oxla_total_files ${totalFiles}`,
      '',
      '# HELP oxla_files_rate File creation rate',
      '# TYPE oxla_files_rate gauge',
      `oxla_files_rate{period="1h"} ${filesLastHour}`,
      `oxla_files_rate{period="1d"} ${filesLastDay}`,
      '',
      '# HELP oxla_total_file_size_bytes Total size of all files in bytes',
      '# TYPE oxla_total_file_size_bytes gauge',
      `oxla_total_file_size_bytes ${totalFileSize._sum.size || 0}`,
      '',
      '# HELP oxla_total_folders Total number of folders',
      '# TYPE oxla_total_folders gauge',
      `oxla_total_folders ${totalFolders}`,
      '',
      '# HELP oxla_total_shares Total number of shares',
      '# TYPE oxla_total_shares gauge',
      `oxla_total_shares ${totalShares}`,
      '',
      '# HELP oxla_active_shares Number of active shares',
      '# TYPE oxla_active_shares gauge',
      `oxla_active_shares ${activeShares}`,
      '',
      '# HELP oxla_email_usage_monthly Monthly email usage',
      '# TYPE oxla_email_usage_monthly gauge',
      `oxla_email_usage_monthly{type="sent",month="${now.getMonth() + 1}",year="${now.getFullYear()}"} ${currentMonthEmails.emailsSent}`,
      `oxla_email_usage_monthly{type="received",month="${now.getMonth() + 1}",year="${now.getFullYear()}"} ${currentMonthEmails.emailsReceived}`,
      `oxla_email_usage_monthly{type="sent",month="${now.getMonth()}",year="${now.getFullYear()}"} ${lastMonthEmails.emailsSent}`,
      `oxla_email_usage_monthly{type="received",month="${now.getMonth()}",year="${now.getFullYear()}"} ${lastMonthEmails.emailsReceived}`,
      '',
      '# HELP oxla_avg_processing_time_seconds Average email processing time in seconds',
      '# TYPE oxla_avg_processing_time_seconds gauge',
      `oxla_avg_processing_time_seconds ${avgProcessingTime}`,
      '',
      '# HELP oxla_uptime_seconds Application uptime in seconds',
      '# TYPE oxla_uptime_seconds counter',
      `oxla_uptime_seconds ${Math.floor(Date.now() / 1000)}`,
    ].join('\n')
    
    return new NextResponse(metrics, {
      headers: {
        'Content-Type': 'text/plain',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
      },
    })
  } catch (error) {
    console.error('Error generating metrics:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}