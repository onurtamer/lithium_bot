'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { Bot, ArrowRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function LoginPage() {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    const handleDiscordLogin = () => {
        window.location.href = `${API_URL}/auth/discord`;
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
            {/* Background Effects */}
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
            </div>

            <Card className="w-full max-w-md border-border/50 bg-card/50 backdrop-blur">
                <CardHeader className="text-center space-y-4 pb-2">
                    <Link href="/" className="flex items-center justify-center gap-2 mx-auto">
                        <div className="h-12 w-12 rounded-xl gradient-blurple flex items-center justify-center">
                            <Bot className="h-6 w-6 text-white" />
                        </div>
                    </Link>
                    <div>
                        <CardTitle className="text-2xl font-bold">Lithium'a Hoş Geldiniz</CardTitle>
                        <CardDescription className="mt-2">
                            Discord hesabınızla giriş yaparak sunucularınızı yönetmeye başlayın.
                        </CardDescription>
                    </div>
                </CardHeader>

                <CardContent className="space-y-6 pt-6">
                    <Button
                        onClick={handleDiscordLogin}
                        className="w-full gap-3 h-12 text-base gradient-blurple border-0 glow-primary"
                    >
                        <svg
                            className="h-5 w-5"
                            fill="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
                        </svg>
                        Discord ile Giriş Yap
                        <ArrowRight className="h-4 w-4" />
                    </Button>

                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <span className="w-full border-t border-border" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-card px-2 text-muted-foreground">veya</span>
                        </div>
                    </div>

                    <div className="text-center space-y-4">
                        <p className="text-sm text-muted-foreground">
                            Hesabınız yok mu? Discord ile giriş yaparak otomatik olarak hesap oluşturulur.
                        </p>

                        <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
                            <Link href="/privacy" className="hover:text-foreground transition-colors">
                                Gizlilik Politikası
                            </Link>
                            <span>•</span>
                            <Link href="/terms" className="hover:text-foreground transition-colors">
                                Kullanım Koşulları
                            </Link>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
