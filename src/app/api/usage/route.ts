import { NextRequest, NextResponse } from 'next/server'
import { emailService } from '@/lib/email-service'
import { getPlanLimits, getUsage } from '@/lib/usage-limits'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'

export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    // Get user's plan
    const user = await db.user.findUnique({
      where: { id: session.user.id },
    })
    
    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }
    
    const limits = await getPlanLimits(user.plan)
    
    // Get current usage
    const emailsSent = await getUsage(session.user.id, 'emails_sent')
    const emailsReceived = await getUsage(session.user.id, 'emails_received')
    
    // Get detailed email usage from database
    const emailUsage = await emailService.getEmailUsage(session.user.id)
    
    return NextResponse.json({
      plan: user.plan,
      limits: {
        emailsPerMonth: limits.emailsPerMonth,
        emailsPerMinute: limits.emailsPerMinute,
        storageGB: limits.storageGB,
        maxFileSizeMB: limits.maxFileSizeMB,
      },
      usage: {
        emailsSent: emailsSent,
        emailsReceived: emailsReceived,
        emailsSentThisMonth: emailUsage.sent,
        emailsReceivedThisMonth: emailUsage.received,
      },
      remaining: {
        emailsPerMonth: Math.max(0, limits.emailsPerMonth - emailsSent),
        emailsPerMinute: Math.max(0, limits.emailsPerMinute - emailsSent),
      },
    })
  } catch (error) {
    console.error('Error getting usage:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}