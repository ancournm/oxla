'use client';

import { useAuth } from '@/contexts/auth-context';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  User, 
  Mail, 
  HardDrive, 
  Settings, 
  LogOut, 
  Crown,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

export default function Dashboard() {
  const { user, logout } = useAuth();

  const getPlanIcon = (plan: string) => {
    switch (plan) {
      case 'enterprise':
        return <Crown className="h-4 w-4 text-purple-500" />;
      case 'pro':
        return <Crown className="h-4 w-4 text-blue-500" />;
      default:
        return <User className="h-4 w-4 text-gray-500" />;
    }
  };

  const getPlanColor = (plan: string) => {
    switch (plan) {
      case 'enterprise':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'pro':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
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
              <h1 className="text-xl font-semibold">Oxla Suite</h1>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Welcome,</span>
                <span className="font-medium">{user.name}</span>
                <Badge className={getPlanColor(user.plan)}>
                  {getPlanIcon(user.plan)}
                  <span className="ml-1 capitalize">{user.plan}</span>
                </Badge>
              </div>
              
              <Button variant="outline" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* User Info Card */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              User Profile
            </CardTitle>
            <CardDescription>
              Your account information and current status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Name</label>
                <p className="font-semibold">{user.name}</p>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Email</label>
                <p className="font-semibold">{user.email}</p>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Plan</label>
                <div className="flex items-center gap-2">
                  <Badge className={getPlanColor(user.plan)}>
                    {getPlanIcon(user.plan)}
                    <span className="ml-1 capitalize">{user.plan}</span>
                  </Badge>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Email Status</label>
                <div className="flex items-center gap-2">
                  {user.is_verified ? (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span className="text-sm">Verified</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="h-4 w-4 text-yellow-500" />
                      <span className="text-sm">Not Verified</span>
                    </>
                  )}
                </div>
              </div>
            </div>
            
            <Separator className="my-4" />
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">Member Since</label>
              <p className="text-sm">{new Date(user.created_at).toLocaleDateString()}</p>
            </div>
          </CardContent>
        </Card>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                Email Service
              </CardTitle>
              <CardDescription>
                Send and receive emails with smart aliases
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Monthly Limit</span>
                  <Badge variant="outline">
                    {user.features?.emails_per_month || '500'} emails
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Rate Limit</span>
                  <Badge variant="outline">
                    {user.features?.email_rate_limit || '5'}/min
                  </Badge>
                </div>
                <Button className="w-full mt-4" onClick={() => window.location.href = '/email'}>
                  Open Email
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HardDrive className="h-5 w-5" />
                File Storage
              </CardTitle>
              <CardDescription>
                Secure cloud storage with sharing capabilities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Storage Limit</span>
                  <Badge variant="outline">
                    {user.features?.storage_limit || '5 GB'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Max File Size</span>
                  <Badge variant="outline">
                    {user.features?.max_file_size || '50 MB'}
                  </Badge>
                </div>
                <Button className="w-full mt-4">
                  Open Drive
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow cursor-pointer">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Settings
              </CardTitle>
              <CardDescription>
                Manage your account and preferences
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Account Type</span>
                  <Badge variant="outline">
                    {user.plan}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Two-Factor Auth</span>
                  <Badge variant="outline">
                    Disabled
                  </Badge>
                </div>
                <Button className="w-full mt-4" variant="outline">
                  Manage Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Plan Features */}
        <Card>
          <CardHeader>
            <CardTitle>Plan Features</CardTitle>
            <CardDescription>
              Features available with your current plan
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(user.features || {}).map(([key, value]) => (
                <div key={key} className="flex items-center gap-2 p-3 rounded-lg border">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <div>
                    <p className="font-medium text-sm capitalize">
                      {key.replace(/_/g, ' ')}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {typeof value === 'boolean' ? (value ? 'Available' : 'Not Available') : String(value)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}