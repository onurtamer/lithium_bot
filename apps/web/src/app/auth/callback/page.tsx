'use client';

import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function AuthCallbackPage() {
    const searchParams = useSearchParams();
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    useEffect(() => {
        const code = searchParams.get('code');

        if (code) {
            // Redirect to backend with the same code
            // The backend handles the token exchange and then redirects to /app
            window.location.href = `${API_URL}/auth/discord/callback?code=${code}`;
        } else {
            // If no code, maybe redirect to login or show error
            window.location.href = '/login?error=no_code';
        }
    }, [searchParams, API_URL]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-background">
            <div className="flex flex-col items-center gap-4">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-muted-foreground animate-pulse">Giriş yapılıyor...</p>
            </div>
        </div>
    );
}
