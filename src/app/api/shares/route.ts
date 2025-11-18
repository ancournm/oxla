import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { db } from '@/lib/db'
import { v4 as uuidv4 } from 'uuid'

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    const body = await request.json()
    const { fileId, permission, expiresAt } = body
    
    if (!fileId) {
      return NextResponse.json({ error: 'File ID is required' }, { status: 400 })
    }
    
    if (!permission || !['VIEW', 'EDIT'].includes(permission)) {
      return NextResponse.json({ error: 'Invalid permission' }, { status: 400 })
    }
    
    // Check if file exists and belongs to user
    const file = await db.file.findUnique({
      where: { id: fileId },
    })
    
    if (!file || file.userId !== session.user.id) {
      return NextResponse.json({ error: 'File not found' }, { status: 404 })
    }
    
    // Generate unique share token
    const shareToken = uuidv4()
    
    // Create share record
    const share = await db.share.create({
      data: {
        userId: session.user.id,
        fileId,
        token: shareToken,
        permission: permission as 'VIEW' | 'EDIT',
        expiresAt: expiresAt ? new Date(expiresAt) : null,
      },
    })
    
    const shareUrl = `${request.nextUrl.origin}/api/shares/${shareToken}`
    
    return NextResponse.json({
      message: 'Share created successfully',
      share: {
        id: share.id,
        token: share.token,
        permission: share.permission,
        expiresAt: share.expiresAt,
        shareUrl,
        createdAt: share.createdAt,
      },
    })
    
  } catch (error) {
    console.error('Error creating share:', error)
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
    
    if (fileId) {
      // Get shares for specific file
      const shares = await db.share.findMany({
        where: { fileId },
        include: {
          file: {
            select: { id: true, name: true },
          },
        },
        orderBy: { createdAt: 'desc' },
      })
      
      // Filter shares to only show those belonging to current user
      const userShares = shares.filter(share => share.userId === session.user.id)
      
      return NextResponse.json({ shares: userShares })
    } else {
      // Get all shares for current user
      const shares = await db.share.findMany({
        where: { userId: session.user.id },
        include: {
          file: {
            select: { id: true, name: true },
          },
        },
        orderBy: { createdAt: 'desc' },
      })
      
      return NextResponse.json({ shares })
    }
    
  } catch (error) {
    console.error('Error getting shares:', error)
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
    const shareId = searchParams.get('shareId')
    
    if (!shareId) {
      return NextResponse.json({ error: 'Share ID is required' }, { status: 400 })
    }
    
    const share = await db.share.findUnique({
      where: { id: shareId },
    })
    
    if (!share || share.userId !== session.user.id) {
      return NextResponse.json({ error: 'Share not found' }, { status: 404 })
    }
    
    // Delete share
    await db.share.delete({
      where: { id: shareId },
    })
    
    return NextResponse.json({ message: 'Share deleted successfully' })
    
  } catch (error) {
    console.error('Error deleting share:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

// Handle share access via token
export async function handleShareAccess(request: NextRequest, token: string) {
  try {
    // Find share by token
    const share = await db.share.findUnique({
      where: { token },
      include: {
        file: true,
      },
    })
    
    if (!share) {
      return NextResponse.json({ error: 'Share not found' }, { status: 404 })
    }
    
    // Check if share is expired
    if (share.expiresAt && share.expiresAt < new Date()) {
      return NextResponse.json({ error: 'Share expired' }, { status: 40 })
    }
    
    // Get file content
    const { readFile } = await import('fs/promises')
    const { join } = await import('path')
    const filePath = join(process.cwd(), 'drive_storage', share.file.path)
    
    try {
      const fileBuffer = await readFile(filePath)
      
      return new NextResponse(fileBuffer, {
        headers: {
          'Content-Type': share.file.mimeType || 'application/octet-stream',
          'Content-Disposition': `attachment; filename="${share.file.name}"`,
          'Content-Length': share.file.size.toString(),
        },
      })
    } catch (error) {
      console.error('Error reading file:', error)
      return NextResponse.json({ error: 'File not found' }, { status: 404 })
    }
    
  } catch (error) {
    console.error('Error accessing share:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}