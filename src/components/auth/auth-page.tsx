'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { User, Rocket, Sparkles } from 'lucide-react';

export default function AuthPage() {
  const { login, isLoading } = useAuth();
  const [error, setError] = useState<string>('');
  
  // Simple login form state
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Generate random alphabet-based username
  const generateRandomUsername = () => {
    const adjectives = ['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta', 'Iota', 'Kappa', 'Lambda', 'Mu', 'Nu', 'Xi', 'Omicron', 'Pi'];
    const nouns = ['Wave', 'Photon', 'Quantum', 'Nebula', 'Cosmos', 'Nova', 'Pulsar', 'Quasar', 'Vega', 'Sirius', 'Orion', 'Phoenix', 'Comet', 'Asteroid', 'Galaxy'];
    
    const randomAdjective = adjectives[Math.floor(Math.random() * adjectives.length)];
    const randomNoun = nouns[Math.floor(Math.random() * nouns.length)];
    const randomNum = Math.floor(Math.random() * 9999);
    
    return `${randomAdjective}${randomNoun}${randomNum}`;
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    // Auto-generate username if empty
    const finalUsername = username.trim() || generateRandomUsername();
    
    if (!finalUsername || !password) {
      setError('Please enter username and password');
      return;
    }
    
    try {
      await login(finalUsername, password);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    }
  };

  const handleQuickAccess = (userType: string) => {
    // Quick access with predefined users
    const users = {
      'alpha': { username: 'AlphaCentauri', password: 'seed123' },
      'beta': { username: 'BetaPulsar', password: 'seed123' },
      'gamma': { username: 'GammaWave', password: 'seed123' },
      'delta': { username: 'DeltaPhoton', password: 'seed123' }
    };
    
    const user = users[userType as keyof typeof users];
    if (user) {
      setUsername(user.username);
      setPassword(user.password);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <div className="relative w-16 h-16">
            <img
              src="/logo.svg"
              alt="Oxla Logo"
              className="w-full h-full object-contain"
            />
          </div>
        </div>

        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold flex items-center gap-2">
              <Rocket className="h-6 w-6 text-blue-500" />
              Oxla Suite
            </CardTitle>
            <CardDescription>
              Quick Access - Enter username & password
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Quick Access Buttons */}
            <div className="grid grid-cols-2 gap-2 mb-6">
              <Button
                variant="outline"
                className="flex items-center gap-2"
                onClick={() => handleQuickAccess('alpha')}
              >
                <User className="h-4 w-4" />
                Alpha Access
              </Button>
              <Button
                variant="outline"
                className="flex items-center gap-2"
                onClick={() => handleQuickAccess('beta')}
              >
                <Sparkles className="h-4 w-4" />
                Beta Access
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-2 mb-6">
              <Button
                variant="outline"
                className="flex items-center gap-2"
                onClick={() => handleQuickAccess('gamma')}
              >
                <User className="h-4 w-4" />
                Gamma Access
              </Button>
              <Button
                variant="outline"
                className="flex items-center gap-2"
                onClick={() => handleQuickAccess('delta')}
              >
                <User className="h-4 w-4" />
                Delta Access
              </Button>
            </div>

            {/* OR Manual Login */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-gray-50 px-2">OR</span>
              </div>
            </div>

            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="username"
                    type="text"
                    placeholder="Enter username or leave empty for random"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
                  
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type="password"
                    placeholder="Enter password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
                    Accessing...
                  </>
                ) : (
                  'Launch Dashboard'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Instructions */}
        <div className="mt-6 text-center text-sm text-muted-foreground">
          <p className="mb-2">
            <strong>Quick Access:</strong> Click any colored button above for instant access
          </p>
          <p className="mb-2">
            <strong>Manual Login:</strong> Enter any username and password
          </p>
          <p className="text-xs">
            <em>Tip: Leave username empty for a random alphanumeric name</em>
          </p>
        </div>
      </div>
    </div>
  );
}