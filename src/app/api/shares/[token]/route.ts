import { NextRequest } from 'next/server'
import { db } from '@/lib/db'
import { readFile } from 'fs/promises'
import { join } from 'path'

export async function GET(request: NextRequest, { params }: { params: { token: string } }) {
  try {
    const token = params.token
    
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
      return NextResponse.json({ error: 'Share expired' }, { status: 410 })
    }
    
    // Get file content
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