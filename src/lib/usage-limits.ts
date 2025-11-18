import { redisClient } from './redis'

// Plan limits configuration
export const PLAN_LIMITS = {
  FREE: {
    emailsPerMonth: 500,
    emailsPerMinute: 5,
    storageGB: 5,
    maxFileSizeMB: 50,
  },
  PRO: {
    emailsPerMonth: 10000,
    emailsPerMinute: 20,
    storageGB: 50,
    maxFileSizeMB: 2048,
  },
  ENTERPRISE: {
    emailsPerMonth: Infinity,
    emailsPerMinute: 100,
    storageGB: Infinity,
    maxFileSizeMB: Infinity,
  },
}

// Rate limiting keys
export const RATE_LIMIT_KEYS = {
  EMAIL_SEND: 'email_send_limit',
  EMAIL_RECEIVE: 'email_receive_limit',
  FILE_UPLOAD: 'file_upload_limit',
  FILE_DOWNLOAD: 'file_download_limit',
}

// Usage tracking keys
export const USAGE_KEYS = {
  EMAILS_SENT: 'emails_sent',
  EMAILS_RECEIVED: 'emails_received',
  STORAGE_USED: 'storage_used',
}

export async function incrementUsage(userId: string, key: string, amount: number = 1): Promise<number> {
  const redisKey = `usage:${userId}:${key}`
  return await redisClient.incrBy(redisKey, amount)
}

export async function getUsage(userId: string, key: string): Promise<number> {
  const redisKey = `usage:${userId}:${key}`
  const value = await redisClient.get(redisKey)
  return value ? parseInt(value) : 0
}

export async function resetUsage(userId: string, key: string): Promise<void> {
  const redisKey = `usage:${userId}:${key}`
  await redisClient.del(redisKey)
}

export async function checkRateLimit(userId: string, type: string, limit: number, windowMs: number = 60000): Promise<{ allowed: boolean; current: number; remaining: number }> {
  const redisKey = `rate_limit:${userId}:${type}`
  const now = Date.now()
  const windowStart = Math.floor(now / windowMs) * windowMs
  
  // Check if we need to reset the counter
  const currentWindow = await redisClient.get(`${redisKey}:window`)
  if (currentWindow !== windowStart.toString()) {
    await redisClient.set(`${redisKey}:window`, windowStart.toString())
    await redisClient.set(`${redisKey}:count`, '0')
  }
  
  // Get current count
  const count = await redisClient.incr(`${redisKey}:count`)
  const remaining = Math.max(0, limit - count)
  const allowed = count <= limit
  
  // Set expiration for the rate limit window
  await redisClient.expire(`${redisKey}:window`, Math.ceil(windowMs / 1000))
  await redisClient.expire(`${redisKey}:count`, Math.ceil(windowMs / 1000))
  
  return { allowed, current: count, remaining }
}

export async function getPlanLimits(plan: string) {
  return PLAN_LIMITS[plan as keyof typeof PLAN_LIMITS] || PLAN_LIMITS.FREE
}

export async function checkEmailQuota(userId: string, plan: string): Promise<{ allowed: boolean; current: number; remaining: number }> {
  const limits = await getPlanLimits(plan)
  const currentUsage = await getUsage(userId, USAGE_KEYS.EMAILS_SENT)
  const remaining = Math.max(0, limits.emailsPerMonth - currentUsage)
  const allowed = currentUsage < limits.emailsPerMonth
  
  return { allowed, current: currentUsage, remaining }
}

export async function checkEmailRateLimit(userId: string, plan: string): Promise<{ allowed: boolean; current: number; remaining: number }> {
  const limits = await getPlanLimits(plan)
  return await checkRateLimit(userId, RATE_LIMIT_KEYS.EMAIL_SEND, limits.emailsPerMinute)
}

export async function resetMonthlyUsage(): Promise<void> {
  // This should be called by a cron job at the beginning of each month
  const keys = await redisClient.keys('usage:*')
  for (const key of keys) {
    await redisClient.del(key)
  }
}