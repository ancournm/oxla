import { NextRequest, NextResponse } from 'next/server'
import { emailService } from '@/lib/email-service'
import { emailRateLimitMiddleware } from '@/lib/middleware'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'

export async function POST(request: NextRequest) {
  try {
    // Apply rate limiting middleware
    const rateLimitResponse = await emailRateLimitMiddleware(request)
    if (rateLimitResponse) {
      return rateLimitResponse
    }
    
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    const body = await request.json()
    const { recipient, subject, content, scheduledAt } = body
    
    if (!recipient) {
      return NextResponse.json({ error: 'Recipient is required' }, { status: 400 })
    }
    
    const result = await emailService.createEmailJob({
      userId: session.user.id,
      type: 'SEND',
      recipient,
      subject,
      content,
      scheduledAt: scheduledAt ? new Date(scheduledAt) : undefined,
    })
    
    if (result.success) {
      return NextResponse.json({ 
        message: 'Email job created successfully',
        jobId: result.jobId,
      })
    } else {
      return NextResponse.json({ error: result.error }, { status: 400 })
    }
  } catch (error) {
    console.error('Error in email API:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    
    const jobs = await emailService.getEmailJobs(session.user.id, status || undefined)
    
    return NextResponse.json({ jobs })
  } catch (error) {
    console.error('Error getting email jobs:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}