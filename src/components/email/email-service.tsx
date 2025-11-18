'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Mail, 
  Send, 
  Inbox, 
  Plus, 
  Trash2, 
  Eye, 
  EyeOff,
  Clock,
  User,
  Search,
  Filter,
  RefreshCw,
  Paperclip
} from 'lucide-react';

interface Email {
  id: number;
  sender: string;
  recipient: string;
  subject: string;
  body_text?: string;
  status: string;
  is_read: boolean;
  is_spam: boolean;
  created_at: string;
  received_at?: string;
  attachments: Array<{filename: string; size: number}>;
}

interface EmailAlias {
  id: number;
  alias_name: string;
  alias_email: string;
  is_disposable: boolean;
  created_at: string;
  expires_at?: string;
}

export default function EmailService() {
  const { user, tokens } = useAuth();
  const [activeTab, setActiveTab] = useState('compose');
  const [emails, setEmails] = useState<Email[]>([]);
  const [aliases, setAliases] = useState<EmailAlias[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [unreadCount, setUnreadCount] = useState(0);

  // Compose form state
  const [recipient, setRecipient] = useState('');
  const [subject, setSubject] = useState('');
  const [bodyText, setBodyText] = useState('');
  const [attachments, setAttachments] = useState<FileList>([]);

  // Alias form state
  const [aliasName, setAliasName] = useState('');
  const [isDisposable, setIsDisposable] = useState(false);
  const [expiresHours, setExpiresHours] = useState('');

  const fetchEmails = async () => {
    if (!tokens) return;
    
    try {
      const response = await fetch('http://localhost:8000/mail/inbox', {
        headers: {
          'Authorization': `Bearer ${tokens.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setEmails(data);
      } else {
        throw new Error('Failed to fetch emails');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch emails');
    }
  };

  const fetchAliases = async () => {
    if (!tokens) return;
    
    try {
      const response = await fetch('http://localhost:8000/mail/aliases', {
        headers: {
          'Authorization': `Bearer ${tokens.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAliases(data);
      } else {
        throw new Error('Failed to fetch aliases');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch aliases');
    }
  };

  const fetchUnreadCount = async () => {
    if (!tokens) return;
    
    try {
      const response = await fetch('http://localhost:8000/mail/unread-count', {
        headers: {
          'Authorization': `Bearer ${tokens.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUnreadCount(data.unread_count);
      }
    } catch (err) {
      console.error('Failed to fetch unread count:', err);
    }
  };

  const sendEmail = async () => {
    if (!tokens || !recipient || !subject || !bodyText) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/mail/send', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${tokens.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          recipient,
          subject,
          body_text: bodyText,
        }),
      });

      if (response.ok) {
        // Clear form
        setRecipient('');
        setSubject('');
        setBodyText('');
        setAttachments([]);
        
        // Refresh emails
        fetchEmails();
        
        setError('');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send email');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to send email');
    } finally {
      setLoading(false);
    }
  };

  const createAlias = async () => {
    if (!tokens || !aliasName) {
      setError('Please enter an alias name');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const requestBody: any = {
        alias_name: aliasName,
        is_disposable: isDisposable,
      };

      if (expiresHours) {
        requestBody.expires_hours = parseInt(expiresHours);
      }

      const response = await fetch('http://localhost:8000/mail/alias', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${tokens.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        // Clear form
        setAliasName('');
        setIsDisposable(false);
        setExpiresHours('');
        
        // Refresh aliases
        fetchAliases();
        
        setError('');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create alias');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to create alias');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (emailId: number) => {
    if (!tokens) return;

    try {
      await fetch(`http://localhost:8000/mail/mark-read/${emailId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${tokens.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      // Refresh emails
      fetchEmails();
      fetchUnreadCount();
    } catch (err) {
      console.error('Failed to mark email as read:', err);
    }
  };

  const deleteAlias = async (aliasId: number) => {
    if (!tokens) return;

    try {
      await fetch(`http://localhost:8000/mail/alias/${aliasId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${tokens.access_token}`,
          'Content-Type': 'application/json',
        },
      });

      // Refresh aliases
      fetchAliases();
    } catch (err) {
      console.error('Failed to delete alias:', err);
    }
  };

  useEffect(() => {
    if (tokens) {
      fetchEmails();
      fetchAliases();
      fetchUnreadCount();
    }
  }, [tokens]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sent': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="bg-white dark:bg-slate-800 shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative w-8 h-8">
                <img
                  src="/logo.svg"
                  alt="Oxla Logo"
                  className="w-full h-full object-contain"
                />
              </div>
              <h1 className="text-xl font-semibold">Email Service</h1>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Inbox className="h-4 w-4" />
                <span className="text-sm font-medium">Unread</span>
                <Badge variant="destructive">{unreadCount}</Badge>
              </div>
              
              <Button variant="outline" size="sm" onClick={() => window.location.href = '/'}>
                Back to Dashboard
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="compose" className="flex items-center gap-2">
              <Mail className="h-4 w-4" />
              Compose
            </TabsTrigger>
            <TabsTrigger value="inbox" className="flex items-center gap-2">
              <Inbox className="h-4 w-4" />
              Inbox
            </TabsTrigger>
            <TabsTrigger value="aliases" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              Aliases
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <Filter className="h-4 w-4" />
              Settings
            </TabsTrigger>
          </TabsList>

          {/* Compose Tab */}
          <TabsContent value="compose">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  Compose Email
                </CardTitle>
                <CardDescription>
                  Send emails to any recipient
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="recipient">Recipient</Label>
                    <Input
                      id="recipient"
                      type="email"
                      placeholder="recipient@example.com"
                      value={recipient}
                      onChange={(e) => setRecipient(e.target.value)}
                      required
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="subject">Subject</Label>
                    <Input
                      id="subject"
                      placeholder="Email subject"
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      required
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="body">Message</Label>
                  <Textarea
                    id="body"
                    placeholder="Type your message here..."
                    value={bodyText}
                    onChange={(e) => setBodyText(e.target.value)}
                    rows={10}
                    required
                  />
                </div>

                <div className="flex items-center gap-4">
                  <Button onClick={sendEmail} disabled={loading}>
                    {loading ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>
                        <Send className="mr-2 h-4 w-4" />
                        Send Email
                      </>
                    )}
                  </Button>
                  
                  <Button variant="outline" disabled>
                    <Paperclip className="mr-2 h-4 w-4" />
                    Attach Files
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Inbox Tab */}
          <TabsContent value="inbox">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Inbox className="h-5 w-5" />
                    Inbox
                  </div>
                  <Button variant="outline" size="sm" onClick={fetchEmails}>
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </CardTitle>
                <CardDescription>
                  Your received emails
                </CardDescription>
              </CardHeader>
              <CardContent>
                {emails.length === 0 ? (
                  <div className="text-center py-8">
                    <Inbox className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">No emails in your inbox</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {emails.map((email) => (
                      <div key={email.id} className="p-4 border rounded-lg hover:bg-accent/50 transition-colors">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge className={getStatusColor(email.status)}>
                                {email.status}
                              </Badge>
                              {!email.is_read && (
                                <Badge variant="outline">Unread</Badge>
                              )}
                              {email.is_spam && (
                                <Badge variant="destructive">Spam</Badge>
                              )}
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-2">
                              <div>
                                <p className="text-sm font-medium">From:</p>
                                <p className="text-sm text-muted-foreground">{email.sender}</p>
                              </div>
                              <div>
                                <p className="text-sm font-medium">To:</p>
                                <p className="text-sm text-muted-foreground">{email.recipient}</p>
                              </div>
                              <div>
                                <p className="text-sm font-medium">Date:</p>
                                <p className="text-sm text-muted-foreground">
                                  {formatDate(email.received_at || email.created_at)}
                                </p>
                              </div>
                            </div>
                            
                            <h4 className="font-medium mb-2">{email.subject}</h4>
                            
                            {email.body_text && (
                              <div className="bg-muted/50 p-3 rounded text-sm">
                                {email.body_text.length > 200 
                                  ? `${email.body_text.substring(0, 200)}...`
                                  : email.body_text
                                }
                              </div>
                            )}
                            
                            {email.attachments && email.attachments.length > 0 && (
                              <div className="flex items-center gap-2 mt-2">
                                <Paperclip className="h-4 w-4" />
                                <span className="text-sm text-muted-foreground">
                                  {email.attachments.length} attachment(s)
                                </span>
                              </div>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-2">
                            {!email.is_read && (
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => markAsRead(email.id)}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Aliases Tab */}
          <TabsContent value="aliases">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Email Aliases
                </CardTitle>
                <CardDescription>
                  Create and manage email aliases
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Create Alias Form */}
                  <div className="p-4 border rounded-lg bg-muted/30">
                    <h4 className="font-medium mb-4">Create New Alias</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div className="space-y-2">
                        <Label htmlFor="alias-name">Alias Name</Label>
                        <Input
                          id="alias-name"
                          placeholder="my-alias"
                          value={aliasName}
                          onChange={(e) => setAliasName(e.target.value)}
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="disposable">Disposable</Label>
                        <select
                          id="disposable"
                          value={isDisposable.toString()}
                          onChange={(e) => setIsDisposable(e.target.value === 'true')}
                          className="w-full p-2 border rounded"
                        >
                          <option value="false">Permanent</option>
                          <option value="true">Disposable</option>
                        </select>
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="expires">Expires (hours)</Label>
                        <Input
                          id="expires"
                          type="number"
                          placeholder="24 (optional)"
                          value={expiresHours}
                          onChange={(e) => setExpiresHours(e.target.value)}
                        />
                      </div>
                    </div>
                    
                    <Button onClick={createAlias} disabled={loading}>
                      <Plus className="mr-2 h-4 w-4" />
                      Create Alias
                    </Button>
                  </div>

                  <Separator />

                  {/* Existing Aliases */}
                  <div>
                    <h4 className="font-medium mb-4">Your Aliases</h4>
                    {aliases.length === 0 ? (
                      <div className="text-center py-8">
                        <User className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                        <p className="text-muted-foreground">No aliases created yet</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {aliases.map((alias) => (
                          <div key={alias.id} className="flex items-center justify-between p-4 border rounded-lg">
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium">{alias.alias_name}</span>
                                <Badge variant={alias.is_disposable ? "destructive" : "outline"}>
                                  {alias.is_disposable ? 'Disposable' : 'Permanent'}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">{alias.alias_email}</p>
                              <div className="flex items-center gap-4 mt-1">
                                <span className="text-xs text-muted-foreground">
                                  Created: {formatDate(alias.created_at)}
                                </span>
                                {alias.expires_at && (
                                  <span className="text-xs text-muted-foreground">
                                    Expires: {formatDate(alias.expires_at)}
                                  </span>
                                )}
                              </div>
                            </div>
                            
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => deleteAlias(alias.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Filter className="h-5 w-5" />
                  Email Settings
                </CardTitle>
                <CardDescription>
                  Configure your email preferences
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="text-center py-8">
                    <Filter className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">Email settings coming soon</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}