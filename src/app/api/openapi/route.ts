import { NextRequest, NextResponse } from 'next/server'

const openApiSpec = {
  openapi: '3.0.0',
  info: {
    title: 'Oxla API',
    version: '1.0.0',
    description: 'Complete backend foundation API for Oxla project including email service, file storage, and user management',
    contact: {
      name: 'Oxla Team',
      email: 'support@oxla.com',
    },
  },
  servers: [
    {
      url: 'http://localhost:3000',
      description: 'Development server',
    },
    {
      url: 'https://api.oxla.com',
      description: 'Production server',
    },
  ],
  components: {
    securitySchemes: {
      bearerAuth: {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
      },
    },
    schemas: {
      User: {
        type: 'object',
        properties: {
          id: {
            type: 'string',
            format: 'cuid',
          },
          email: {
            type: 'string',
            format: 'email',
          },
          name: {
            type: 'string',
          },
          plan: {
            type: 'string',
            enum: ['FREE', 'PRO', 'ENTERPRISE'],
          },
          createdAt: {
            type: 'string',
            format: 'date-time',
          },
          updatedAt: {
            type: 'string',
            format: 'date-time',
          },
        },
      },
      EmailJob: {
        type: 'object',
        properties: {
          id: {
            type: 'string',
            format: 'cuid',
          },
          userId: {
            type: 'string',
            format: 'cuid',
          },
          type: {
            type: 'string',
            enum: ['SEND', 'RECEIVE'],
          },
          status: {
            type: 'string',
            enum: ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'RETRYING'],
          },
          recipient: {
            type: 'string',
            format: 'email',
          },
          subject: {
            type: 'string',
          },
          content: {
            type: 'string',
          },
          retryCount: {
            type: 'integer',
          },
          maxRetries: {
            type: 'integer',
          },
          scheduledAt: {
            type: 'string',
            format: 'date-time',
          },
          completedAt: {
            type: 'string',
            format: 'date-time',
          },
          failedAt: {
            type: 'string',
            format: 'date-time',
          },
          error: {
            type: 'string',
          },
          createdAt: {
            type: 'string',
            format: 'date-time',
          },
          updatedAt: {
            type: 'string',
            format: 'date-time',
          },
        },
      },
      EmailJobRequest: {
        type: 'object',
        required: ['recipient'],
        properties: {
          recipient: {
            type: 'string',
            format: 'email',
            description: 'Email recipient address',
          },
          subject: {
            type: 'string',
            description: 'Email subject line',
          },
          content: {
            type: 'string',
            description: 'Email content',
          },
          scheduledAt: {
            type: 'string',
            format: 'date-time',
            description: 'When to send the email (optional)',
          },
        },
      },
      UsageResponse: {
        type: 'object',
        properties: {
          plan: {
            type: 'string',
            enum: ['FREE', 'PRO', 'ENTERPRISE'],
          },
          limits: {
            type: 'object',
            properties: {
              emailsPerMonth: {
                type: 'integer',
              },
              emailsPerMinute: {
                type: 'integer',
              },
              storageGB: {
                type: 'integer',
              },
              maxFileSizeMB: {
                type: 'integer',
              },
            },
          },
          usage: {
            type: 'object',
            properties: {
              emailsSent: {
                type: 'integer',
              },
              emailsReceived: {
                type: 'integer',
              },
              emailsSentThisMonth: {
                type: 'integer',
              },
              emailsReceivedThisMonth: {
                type: 'integer',
              },
            },
          },
          remaining: {
            type: 'object',
            properties: {
              emailsPerMonth: {
                type: 'integer',
              },
              emailsPerMinute: {
                type: 'integer',
              },
            },
          },
        },
      },
      ErrorResponse: {
        type: 'object',
        properties: {
          error: {
            type: 'string',
          },
          message: {
            type: 'string',
          },
          details: {
            type: 'object',
          },
        },
      },
    },
  },
  paths: {
    '/api/email': {
      post: {
        summary: 'Create email job',
        description: 'Create a new email job for sending or receiving emails',
        tags: ['Email'],
        security: [
          {
            bearerAuth: [],
          },
        ],
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                $ref: '#/components/schemas/EmailJobRequest',
              },
            },
          },
        },
        responses: {
          '200': {
            description: 'Email job created successfully',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    message: {
                      type: 'string',
                    },
                    jobId: {
                      type: 'string',
                    },
                  },
                },
              },
            },
          },
          '400': {
            description: 'Bad request',
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/ErrorResponse',
                },
              },
            },
          },
          '401': {
            description: 'Unauthorized',
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/ErrorResponse',
                },
              },
            },
          },
          '429': {
            description: 'Rate limit exceeded or quota exceeded',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    error: {
                      type: 'string',
                    },
                    retryAfter: {
                      type: 'string',
                    },
                    current: {
                      type: 'integer',
                    },
                    limit: {
                      type: 'integer',
                    },
                  },
                },
              },
            },
          },
        },
      },
      get: {
        summary: 'Get email jobs',
        description: 'Get email jobs for the authenticated user',
        tags: ['Email'],
        security: [
          {
            bearerAuth: [],
          },
        ],
        parameters: [
          {
            name: 'status',
            in: 'query',
            description: 'Filter by job status',
            schema: {
              type: 'string',
              enum: ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'RETRYING'],
            },
          },
        ],
        responses: {
          '200': {
            description: 'List of email jobs',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    jobs: {
                      type: 'array',
                      items: {
                        $ref: '#/components/schemas/EmailJob',
                      },
                    },
                  },
                },
              },
            },
          },
          '401': {
            description: 'Unauthorized',
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/ErrorResponse',
                },
              },
            },
          },
        },
      },
    },
    '/api/usage': {
      get: {
        summary: 'Get usage statistics',
        description: 'Get current usage statistics and limits for the authenticated user',
        tags: ['Usage'],
        security: [
          {
            bearerAuth: [],
          },
        ],
        responses: {
          '200': {
            description: 'Usage statistics',
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/UsageResponse',
                },
              },
            },
          },
          '401': {
            description: 'Unauthorized',
            content: {
              'application/json': {
                schema: {
                  $ref: '#/components/schemas/ErrorResponse',
                },
              },
            },
          },
        },
      },
    },
    '/api/metrics': {
      get: {
        summary: 'Get Prometheus metrics',
        description: 'Get application metrics in Prometheus format',
        tags: ['Monitoring'],
        responses: {
          '200': {
            description: 'Prometheus metrics',
            content: {
              'text/plain': {
                schema: {
                  type: 'string',
                },
              },
            },
          },
        },
      },
    },
  },
  tags: [
    {
      name: 'Email',
      description: 'Email service endpoints',
    },
    {
      name: 'Usage',
      description: 'Usage tracking and limits',
    },
    {
      name: 'Monitoring',
      description: 'Application monitoring and metrics',
    },
  ],
}

export async function GET(request: NextRequest) {
  return NextResponse.json(openApiSpec, {
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  })
}