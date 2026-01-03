'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { ArrowRight, Loader2, Key, Sparkles, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function LoginPage() {
    const router = useRouter();
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    const [accessKey, setAccessKey] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleDiscordLogin = () => {
        window.location.href = `${API_URL}/auth/discord`;
    };

    const handleKeyLogin = async () => {
        if (!accessKey.trim()) {
            setError('Lütfen geçerli bir anahtar girin.');
            return;
        }

        if (accessKey.length !== 30) {
            setError('Anahtar 30 karakter olmalıdır.');
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_URL}/auth/key`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ key: accessKey }),
                credentials: 'include',
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Anahtar doğrulanamadı');
            }

            // Store token in cookie (handled by API) and redirect
            if (data.success && data.guild_id) {
                // Store token manually for key-based auth
                document.cookie = `access_token=${data.token}; path=/; max-age=86400; samesite=lax`;
                router.push(`/app/${data.guild_id}/dashboard`);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Bir hata oluştu');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
            {/* Background Effects */}
            <div className="fixed inset-0 -z-10">
                <div className="absolute inset-0 bg-grid-lithium opacity-20" />
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-float-slow" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-float-slow" style={{ animationDelay: '2s' }} />
            </div>

            <Card className="w-full max-w-md glass-card animate-neon-border">
                <CardHeader className="text-center space-y-4 pb-2">
                    <Link href="/" className="flex flex-col items-center gap-3 mx-auto group">
                        <div className="relative h-16 w-16 rounded-xl overflow-hidden glow-lithium-strong group-hover:scale-105 transition-transform">
                            <Image
                                src="/logo.jpg"
                                alt="Lithium"
                                fill
                                className="object-cover"
                            />
                        </div>
                    </Link>
                    <div>
                        <CardTitle className="text-2xl font-bold">
                            <span className="gradient-text-lithium">Lithium</span>&apos;a Hoş Geldiniz
                        </CardTitle>
                        <CardDescription className="mt-2">
                            Discord hesabınızla veya sunucu anahtarınızla giriş yapın.
                        </CardDescription>
                    </div>
                </CardHeader>

                <CardContent className="space-y-6 pt-6">
                    <Tabs defaultValue="discord" className="w-full">
                        <TabsList className="grid w-full grid-cols-2 bg-muted/50">
                            <TabsTrigger value="discord" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
                                <Sparkles className="h-4 w-4 mr-2" />
                                Discord
                            </TabsTrigger>
                            <TabsTrigger value="key" className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary">
                                <Key className="h-4 w-4 mr-2" />
                                Anahtar
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="discord" className="mt-6 space-y-4">
                            <Button
                                onClick={handleDiscordLogin}
                                className="w-full gap-3 h-12 text-base btn-lithium"
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
                            <p className="text-xs text-center text-muted-foreground">
                                Tüm sunucularınıza erişim için Discord hesabınızla giriş yapın.
                            </p>
                        </TabsContent>

                        <TabsContent value="key" className="mt-6 space-y-4">
                            <div className="space-y-3">
                                <Input
                                    type="text"
                                    placeholder="30 haneli anahtarınızı girin..."
                                    value={accessKey}
                                    onChange={(e) => {
                                        setAccessKey(e.target.value.toUpperCase());
                                        setError(null);
                                    }}
                                    maxLength={30}
                                    className="h-12 text-center tracking-widest font-mono bg-muted/50 border-primary/20 focus:border-primary/50 focus:ring-primary/20"
                                    disabled={isLoading}
                                />
                                <div className="flex justify-between text-xs text-muted-foreground px-1">
                                    <span>Discord&apos;da /key komutu ile alabilirsiniz</span>
                                    <span>{accessKey.length}/30</span>
                                </div>
                            </div>

                            {error && (
                                <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                                    <AlertCircle className="h-4 w-4 flex-shrink-0" />
                                    {error}
                                </div>
                            )}

                            <Button
                                onClick={handleKeyLogin}
                                disabled={isLoading || accessKey.length !== 30}
                                className="w-full gap-3 h-12 text-base btn-lithium disabled:opacity-50"
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="h-5 w-5 animate-spin" />
                                        Doğrulanıyor...
                                    </>
                                ) : (
                                    <>
                                        <Key className="h-5 w-5" />
                                        Anahtar ile Giriş Yap
                                        <ArrowRight className="h-4 w-4" />
                                    </>
                                )}
                            </Button>
                            <p className="text-xs text-center text-muted-foreground">
                                Sadece ilgili sunucunun dashboard&apos;una erişim sağlar.
                            </p>
                        </TabsContent>
                    </Tabs>

                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <span className="w-full border-t border-border/50" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-card px-2 text-muted-foreground">Güvenli Giriş</span>
                        </div>
                    </div>

                    <div className="text-center space-y-4">
                        <p className="text-sm text-muted-foreground">
                            Giriş yaparak{' '}
                            <Link href="/terms" className="text-primary hover:underline">
                                Kullanım Koşulları
                            </Link>
                            &apos;nı ve{' '}
                            <Link href="/privacy" className="text-primary hover:underline">
                                Gizlilik Politikası
                            </Link>
                            &apos;nı kabul etmiş olursunuz.
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
