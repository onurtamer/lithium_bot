'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { api, type Guild } from '@/lib/api';
import { getGuildIcon } from '@/lib/utils';
import { useAuthStore, useGuildStore } from '@/lib/store';
import { Header } from '@/components/layout';
import {
    Bot,
    Plus,
    ExternalLink,
    Users,
    ArrowRight,
    Loader2,
    AlertCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';

export default function GuildsPage() {
    const router = useRouter();
    const { user, setUser, isLoading: authLoading } = useAuthStore();
    const { guilds, setGuilds, isLoading: guildsLoading, setLoading } = useGuildStore();
    const [searchQuery, setSearchQuery] = useState('');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadUserAndGuilds();
    }, []);

    const loadUserAndGuilds = async () => {
        try {
            const userData = await api.getMe();
            setUser(userData);

            const guildsData = await api.getGuilds();
            setGuilds(guildsData);
        } catch (err) {
            console.error('Failed to load data:', err);
            if (err instanceof Error && err.message.includes('401')) {
                router.push('/login');
            } else {
                setError('Veriler yüklenirken bir hata oluştu.');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleAddBot = (guildId?: string) => {
        const clientId = process.env.NEXT_PUBLIC_DISCORD_CLIENT_ID;
        const permissions = '8';
        let url = `https://discord.com/api/oauth2/authorize?client_id=${clientId}&permissions=${permissions}&scope=bot%20applications.commands`;
        if (guildId) {
            url += `&guild_id=${guildId}`;
        }
        window.open(url, '_blank');
    };

    const filteredGuilds = guilds.filter(guild =>
        guild.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const installedGuilds = filteredGuilds.filter(g => g.bot_installed !== false);
    const pendingGuilds = filteredGuilds.filter(g => g.bot_installed === false);

    if (authLoading || guildsLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
                    <p className="text-muted-foreground">Yükleniyor...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="text-center">
                    <AlertCircle className="h-12 w-12 mx-auto mb-4 text-destructive" />
                    <h2 className="text-lg font-semibold mb-2">Bir Hata Oluştu</h2>
                    <p className="text-muted-foreground mb-4">{error}</p>
                    <Button onClick={loadUserAndGuilds}>Tekrar Dene</Button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background">
            <Header showGuildSwitcher={false} />

            <main className="container mx-auto px-4 py-8">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold">Sunucularınız</h1>
                        <p className="text-muted-foreground mt-1">
                            Yönetim izniniz olan sunucuları görüntüleyin ve yapılandırın.
                        </p>
                    </div>

                    <Button onClick={() => handleAddBot()} className="gap-2 gradient-blurple border-0">
                        <Plus className="h-4 w-4" />
                        Yeni Sunucuya Ekle
                    </Button>
                </div>

                {/* Search */}
                <div className="mb-8 max-w-md">
                    <Input
                        placeholder="Sunucu ara..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="bg-muted/50"
                    />
                </div>

                {/* Bot Installed Guilds */}
                {installedGuilds.length > 0 && (
                    <section className="mb-12">
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Bot className="h-5 w-5 text-success" />
                            Bot Kurulu ({installedGuilds.length})
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {installedGuilds.map((guild) => (
                                <GuildCard
                                    key={guild.id}
                                    guild={guild}
                                    onManage={() => router.push(`/app/${guild.id}/dashboard`)}
                                />
                            ))}
                        </div>
                    </section>
                )}

                {/* Pending Guilds */}
                {pendingGuilds.length > 0 && (
                    <section>
                        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <Plus className="h-5 w-5 text-muted-foreground" />
                            Bot Kurulmamış ({pendingGuilds.length})
                        </h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {pendingGuilds.map((guild) => (
                                <GuildCard
                                    key={guild.id}
                                    guild={guild}
                                    onAddBot={() => handleAddBot(guild.id)}
                                />
                            ))}
                        </div>
                    </section>
                )}

                {/* Empty State */}
                {filteredGuilds.length === 0 && (
                    <Card className="text-center py-12">
                        <CardContent>
                            <Users className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                            <h3 className="text-lg font-semibold mb-2">Sunucu Bulunamadı</h3>
                            <p className="text-muted-foreground mb-4">
                                {searchQuery
                                    ? 'Aramanızla eşleşen sunucu bulunamadı.'
                                    : 'Yönetim izniniz olan sunucu bulunmuyor.'}
                            </p>
                            {!searchQuery && (
                                <Button onClick={() => handleAddBot()} variant="outline">
                                    Sunucuya Bot Ekle
                                </Button>
                            )}
                        </CardContent>
                    </Card>
                )}
            </main>
        </div>
    );
}

interface GuildCardProps {
    guild: Guild;
    onManage?: () => void;
    onAddBot?: () => void;
}

function GuildCard({ guild, onManage, onAddBot }: GuildCardProps) {
    const isInstalled = guild.bot_installed !== false;

    return (
        <Card className="card-hover group">
            <CardContent className="pt-6">
                <div className="flex items-start gap-4">
                    <div className="relative h-14 w-14 overflow-hidden rounded-xl flex-shrink-0">
                        <Image
                            src={getGuildIcon(guild.id, guild.icon)}
                            alt={guild.name}
                            fill
                            className="object-cover"
                        />
                    </div>

                    <div className="flex-1 min-w-0">
                        <h3 className="font-semibold truncate">{guild.name}</h3>
                        <div className="flex items-center gap-2 mt-1">
                            {guild.owner && (
                                <Badge variant="secondary" className="text-[10px]">Sahip</Badge>
                            )}
                            {isInstalled ? (
                                <Badge variant="outline" className="text-[10px] border-success text-success">
                                    Bot Aktif
                                </Badge>
                            ) : (
                                <Badge variant="outline" className="text-[10px] text-muted-foreground">
                                    Kurulum Bekliyor
                                </Badge>
                            )}
                        </div>
                    </div>
                </div>

                <div className="mt-4 pt-4 border-t border-border">
                    {isInstalled ? (
                        <Button onClick={onManage} className="w-full gap-2" variant="default">
                            Yönet
                            <ArrowRight className="h-4 w-4" />
                        </Button>
                    ) : (
                        <Button onClick={onAddBot} className="w-full gap-2" variant="outline">
                            <Plus className="h-4 w-4" />
                            Bot Ekle
                            <ExternalLink className="h-3 w-3 ml-auto" />
                        </Button>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
