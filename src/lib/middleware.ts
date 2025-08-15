import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { checkEmailRateLimit, checkEmailQuota } from '@/lib/usage-limits'
import { db } from '@/lib/db'

export async function emailRateLimitMiddleware(request: NextRequest): Promise<NextResponse | null> {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    const user = await db.user.findUnique({
      where: { id: session.user.id },
    })
    
    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }
    
    // Check rate limit
    const rateLimitCheck = await checkEmailRateLimit(session.user.id, user.plan)
    if (!rateLimitCheck.allowed) {
      return NextResponse.json(
        { 
          error: 'Rate limit exceeded',
          retryAfter: '60s',
          current: rateLimitCheck.current,
          limit: rateLimitCheck.current + rateLimitCheck.remaining,
        },
        { 
          status: 429,
          headers: {
            'Retry-After': '60',
            'X-RateLimit-Limit': (rateLimitCheck.current + rateLimitCheck.remaining).toString(),
            'X-RateLimit-Remaining': rateLimitCheck.remaining.toString(),
            'X-RateLimit-Reset': new Date(Date.now() + 60000).toISOString(),
          },
        }
      )
    }
    
    // Check monthly quota
    const quotaCheck = await checkEmailQuota(session.user.id, user.plan)
    if (!quotaCheck.allowed) {
      return NextResponse.json(
        { 
          error: 'Monthly email quota exceeded',
          current: quotaCheck.current,
          limit: quotaCheck.current + quotaCheck.remaining,
        },
        { 
          status: 429,
          headers: {
            'X-Quota-Limit': (quotaCheck.current + quotaCheck.remaining).toString(),
            'X-Quota-Remaining': quotaCheck.remaining.toString(),
            'X-Quota-Reset': new Date(new Date().getFullYear(), new Date().getMonth() + 1, 1).toISOString(),
          },
        }
      )
    }
    
    // Add rate limit headers to successful responses
    const response = NextResponse.next()
    response.headers.set('X-RateLimit-Limit', (rateLimitCheck.current + rateLimitCheck.remaining).toString())
    response.headers.set('X-RateLimit-Remaining', rateLimitCheck.remaining.toString())
    response.headers.set('X-RateLimit-Reset', new Date(Date.now() + 60000).toISOString())
    response.headers.set('X-Quota-Limit', (quotaCheck.current + quotaCheck.remaining).toString())
    response.headers.set('X-Quota-Remaining', quotaCheck.remaining.toString())
    response.headers.set('X-Quota-Reset', new Date(new Date().getFullYear(), new Date().getMonth() + 1, 1).toISOString())
    
    return response
  } catch (error) {
    console.error('Error in rate limit middleware:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function fileRateLimitMiddleware(request: NextRequest): Promise<NextResponse | null> {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    const user = await db.user.findUnique({
      where: { id: session.user.id },
    })
    
    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }
    
    // Get file upload limits based on plan
    const limits = {
      FREE: { uploadsPerMinute: 10, downloadsPerMinute: 50 },
      PRO: { uploadsPerMinute: 50, downloadsPerMinute: 200 },
      ENTERPRISE: { uploadsPerMinute: 200, downloadsPerMinute: 1000 },
    }
    
    const planLimits = limits[user.plan as keyof typeof limits] || limits.FREE
    
    // Check upload rate limit
    if (request.method === 'POST') {
      const uploadCheck = await checkEmailRateLimit(session.user.id, 'FILE_UPLOAD', planLimits.uploadsPerMinute)
      if (!uploadCheck.allowed) {
        return NextResponse.json(
          { 
            error: 'File upload rate limit exceeded',
            retryAfter: '60s',
            current: uploadCheck.current,
            limit: uploadCheck.current + uploadCheck.remaining,
          },
          { 
            status: 429,
            headers: {
              'Retry-After': '60',
              'X-RateLimit-Limit': (uploadCheck.current + uploadCheck.remaining).toString(),
              'X-RateLimit-Remaining': uploadCheck.remaining.toString(),
              'X-RateLimit-Reset': new Date(Date.now() + 60000).toISOString(),
            },
          }
        )
      }
    }
    
    // Check download rate limit
    if (request.method === 'GET') {
      const downloadCheck = await checkEmailRateLimit(session.user.id, 'FILE_DOWNLOAD', planLimits.downloadsPerMinute)
      if (!downloadCheck.allowed) {
        return NextResponse.json(
          { 
            error: 'File download rate limit exceeded',
            retryAfter: '60s',
            current: downloadCheck.current,
            limit: downloadCheck.current + downloadCheck.remaining,
          },
          { 
            status: 429,
            headers: {
              'Retry-After': '60',
              'X-RateLimit-Limit': (downloadCheck.current + downloadCheck.remaining).toString(),
              'X-RateLimit-Remaining': downloadCheck.remaining.toString(),
              'X-RateLimit-Reset': new Date(Date.now() + 60000).toISOString(),
            },
          }
        )
      }
    }
    
    return null
  } catch (error) {
    console.error('Error in file rate limit middleware:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}