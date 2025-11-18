import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { db } from '@/lib/db'
import { getPlanLimits, checkRateLimit } from '@/lib/usage-limits'
import { fileRateLimitMiddleware } from '@/lib/middleware'
import { virusScanService } from '@/lib/virus-scan'
import { writeFile, mkdir, unlink, readFile } from 'fs/promises'
import { join } from 'path'
import { v4 as uuidv4 } from 'uuid'

export async function POST(request: NextRequest) {
  try {
    // Apply rate limiting middleware
    const rateLimitResponse = await fileRateLimitMiddleware(request)
    if (rateLimitResponse) {
      return rateLimitResponse
    }
    
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
    
    // Get plan limits
    const limits = await getPlanLimits(user.plan)
    
    // Parse form data
    const formData = await request.formData()
    const file = formData.get('file') as File
    const folderId = formData.get('folderId') as string
    
    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 })
    }
    
    // Check file size limit
    const fileSizeInMB = file.size / (1024 * 1024)
    if (fileSizeInMB > limits.maxFileSizeMB) {
      return NextResponse.json({ 
        error: 'File size exceeds limit',
        maxSizeMB: limits.maxFileSizeMB,
        currentSizeMB: fileSizeInMB
      }, { status: 413 })
    }
    
    // Check storage quota
    const currentFiles = await db.file.aggregate({
      where: { userId: session.user.id },
      _sum: { size: true },
    })
    
    const currentStorageGB = (currentFiles._sum.size || 0) / (1024 * 1024 * 1024)
    const newStorageGB = currentStorageGB + (file.size / (1024 * 1024 * 1024))
    
    if (newStorageGB > limits.storageGB) {
      return NextResponse.json({ 
        error: 'Storage quota exceeded',
        maxStorageGB: limits.storageGB,
        currentStorageGB: currentStorageGB,
        requestedStorageGB: newStorageGB
      }, { status: 413 })
    }
    
    // Get file buffer for virus scanning
    const fileBuffer = Buffer.from(await file.arrayBuffer())
    
    // Perform virus scan
    const scanResult = await virusScanService.scanFileContent(fileBuffer, file.name)
    
    if (scanResult.isInfected) {
      return NextResponse.json({
        error: 'Virus detected',
        threats: scanResult.threats,
        scanTime: scanResult.scanTime,
      }, { status: 403 })
    }
    
    // Generate unique filename
    const fileExtension = file.name.split('.').pop()
    const uniqueFileName = `${uuidv4()}.${fileExtension}`
    const filePath = join(process.cwd(), 'drive_storage', uniqueFileName)
    
    // Ensure storage directory exists
    await mkdir(join(process.cwd(), 'drive_storage'), { recursive: true })
    
    // Save file
    await writeFile(filePath, fileBuffer)
    
    // Create file record in database
    const fileRecord = await db.file.create({
      data: {
        userId: session.user.id,
        name: file.name,
        path: uniqueFileName,
        size: file.size,
        mimeType: file.type,
        folderId: folderId || null,
      },
    })
    
    // Update usage tracking
    const { incrementUsage } = await import('@/lib/usage-limits')
    await incrementUsage(session.user.id, 'storage_used', file.size)
    
    return NextResponse.json({
      message: 'File uploaded successfully',
      file: {
        id: fileRecord.id,
        name: fileRecord.name,
        size: fileRecord.size,
        mimeType: fileRecord.mimeType,
        createdAt: fileRecord.createdAt,
        virusScanResult: scanResult,
      },
    })
    
  } catch (error) {
    console.error('Error uploading file:', error)
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
    const fileId = searchParams.get('fileId')
    const folderId = searchParams.get('folderId')
    
    if (fileId) {
      // Download specific file
      const fileRecord = await db.file.findUnique({
        where: { id: fileId },
      })
      
      if (!fileRecord || fileRecord.userId !== session.user.id) {
        return NextResponse.json({ error: 'File not found' }, { status: 404 })
      }
      
      // Apply rate limiting for download
      const rateLimitResponse = await fileRateLimitMiddleware(request)
      if (rateLimitResponse) {
        return rateLimitResponse
      }
      
      const filePath = join(process.cwd(), 'drive_storage', fileRecord.path)
      const fileBuffer = await readFile(filePath)
      
      return new NextResponse(fileBuffer, {
        headers: {
          'Content-Type': fileRecord.mimeType || 'application/octet-stream',
          'Content-Disposition': `attachment; filename="${fileRecord.name}"`,
          'Content-Length': fileRecord.size.toString(),
        },
      })
    } else {
      // List files
      const whereClause: any = { userId: session.user.id }
      if (folderId) {
        whereClause.folderId = folderId
      }
      
      const files = await db.file.findMany({
        where: whereClause,
        include: {
          folder: {
            select: { id: true, name: true },
          },
        },
        orderBy: { createdAt: 'desc' },
      })
      
      return NextResponse.json({ files })
    }
    
  } catch (error) {
    console.error('Error in files API:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    const { searchParams } = new URL(request.url)
    const fileId = searchParams.get('fileId')
    
    if (!fileId) {
      return NextResponse.json({ error: 'File ID is required' }, { status: 400 })
    }
    
    const fileRecord = await db.file.findUnique({
      where: { id: fileId },
    })
    
    if (!fileRecord || fileRecord.userId !== session.user.id) {
      return NextResponse.json({ error: 'File not found' }, { status: 404 })
    }
    
    // Delete physical file
    const filePath = join(process.cwd(), 'drive_storage', fileRecord.path)
    await unlink(filePath)
    
    // Delete database record
    await db.file.delete({
      where: { id: fileId },
    })
    
    return NextResponse.json({ message: 'File deleted successfully' })
    
  } catch (error) {
    console.error('Error deleting file:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}