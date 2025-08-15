import { NextRequest, NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { db } from '@/lib/db'

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    const body = await request.json()
    const { name, parentId } = body
    
    if (!name) {
      return NextResponse.json({ error: 'Folder name is required' }, { status: 400 })
    }
    
    // Check if parent folder exists and belongs to user
    if (parentId) {
      const parentFolder = await db.folder.findUnique({
        where: { id: parentId },
      })
      
      if (!parentFolder || parentFolder.userId !== session.user.id) {
        return NextResponse.json({ error: 'Parent folder not found' }, { status: 404 })
      }
    }
    
    // Create folder
    const folder = await db.folder.create({
      data: {
        userId: session.user.id,
        name,
        parentId: parentId || null,
      },
    })
    
    return NextResponse.json({
      message: 'Folder created successfully',
      folder: {
        id: folder.id,
        name: folder.name,
        parentId: folder.parentId,
        createdAt: folder.createdAt,
      },
    })
    
  } catch (error) {
    console.error('Error creating folder:', error)
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
    const folderId = searchParams.get('folderId')
    
    if (folderId) {
      // Get specific folder
      const folder = await db.folder.findUnique({
        where: { id: folderId },
        include: {
          parent: {
            select: { id: true, name: true },
          },
          children: {
            select: { id: true, name: true },
          },
        },
      })
      
      if (!folder || folder.userId !== session.user.id) {
        return NextResponse.json({ error: 'Folder not found' }, { status: 404 })
      }
      
      return NextResponse.json({ folder })
    } else {
      // List folders
      const folders = await db.folder.findMany({
        where: { userId: session.user.id },
        include: {
          parent: {
            select: { id: true, name: true },
          },
          children: {
            select: { id: true, name: true },
          },
        },
        orderBy: { createdAt: 'desc' },
      })
      
      return NextResponse.json({ folders })
    }
    
  } catch (error) {
    console.error('Error getting folders:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

export async function PUT(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions)
    
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    
    const { searchParams } = new URL(request.url)
    const folderId = searchParams.get('folderId')
    
    if (!folderId) {
      return NextResponse.json({ error: 'Folder ID is required' }, { status: 400 })
    }
    
    const body = await request.json()
    const { name, parentId } = body
    
    const folder = await db.folder.findUnique({
      where: { id: folderId },
    })
    
    if (!folder || folder.userId !== session.user.id) {
      return NextResponse.json({ error: 'Folder not found' }, { status: 404 })
    }
    
    // Check if new parent folder exists and belongs to user
    if (parentId) {
      const parentFolder = await db.folder.findUnique({
        where: { id: parentId },
      })
      
      if (!parentFolder || parentFolder.userId !== session.user.id) {
        return NextResponse.json({ error: 'Parent folder not found' }, { status: 404 })
      }
      
      // Prevent circular references
      if (parentId === folderId) {
        return NextResponse.json({ error: 'Cannot move folder to itself' }, { status: 400 })
      }
    }
    
    // Update folder
    const updatedFolder = await db.folder.update({
      where: { id: folderId },
      data: {
        name: name || folder.name,
        parentId: parentId !== undefined ? parentId : folder.parentId,
      },
    })
    
    return NextResponse.json({
      message: 'Folder updated successfully',
      folder: {
        id: updatedFolder.id,
        name: updatedFolder.name,
        parentId: updatedFolder.parentId,
        createdAt: updatedFolder.createdAt,
        updatedAt: updatedFolder.updatedAt,
      },
    })
    
  } catch (error) {
    console.error('Error updating folder:', error)
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
    const folderId = searchParams.get('folderId')
    
    if (!folderId) {
      return NextResponse.json({ error: 'Folder ID is required' }, { status: 400 })
    }
    
    const folder = await db.folder.findUnique({
      where: { id: folderId },
    })
    
    if (!folder || folder.userId !== session.user.id) {
      return NextResponse.json({ error: 'Folder not found' }, { status: 404 })
    }
    
    // Check if folder has files or subfolders
    const [filesCount, subfoldersCount] = await Promise.all([
      db.file.count({ where: { folderId } }),
      db.folder.count({ where: { parentId: folderId } }),
    ])
    
    if (filesCount > 0 || subfoldersCount > 0) {
      return NextResponse.json({ 
        error: 'Cannot delete folder with contents',
        filesCount,
        subfoldersCount
      }, { status: 400 })
    }
    
    // Delete folder
    await db.folder.delete({
      where: { id: folderId },
    })
    
    return NextResponse.json({ message: 'Folder deleted successfully' })
    
  } catch (error) {
    console.error('Error deleting folder:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}