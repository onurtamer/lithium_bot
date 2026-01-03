'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import {
    Gavel,
    AlertTriangle,
    Ban,
    VolumeX,
    Clock,
    User,
    Search,
    Filter,
    Loader2,
    ShieldAlert,
    MessageSquareWarning
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface Warning {
    id: string;
    user_id: string;
    username: string;
    reason: string;
    moderator: string;
    created_at: string;
    expires_at?: string;
}

interface MuteRecord {
    id: string;
    user_id: string;
    username: string;
    reason: string;
    moderator: string;
    duration: number;
    created_at: string;
    expires_at: string;
    active: boolean;
}

interface BanRecord {
    id: string;
    user_id: string;
    username: string;
    reason: string;
    moderator: string;
    created_at: string;
    permanent: boolean;
}

export default function ModerationPage() {
    const params = useParams();
    const guildId = params.guildId as string;
    const [activeTab, setActiveTab] = useState('warnings');
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    // Placeholder data - would come from API
    const [warnings, setWarnings] = useState<Warning[]>([]);
    const [mutes, setMutes] = useState<MuteRecord[]>([]);
    const [bans, setBans] = useState<BanRecord[]>([]);

    useEffect(() => {
        // Simulate loading - in production this would fetch from API
        setIsLoading(true);
        setTimeout(() => {
            setIsLoading(false);
        }, 500);
    }, [guildId, activeTab]);

    const stats = [
        { label: 'Aktif Uyarılar', value: warnings.length, icon: AlertTriangle, color: 'text-warning' },
        { label: 'Aktif Susturmalar', value: mutes.filter(m => m.active).length, icon: VolumeX, color: 'text-orange-400' },
        { label: 'Toplam Yasaklar', value: bans.length, icon: Ban, color: 'text-destructive' },
    ];

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Gavel className="h-6 w-6" />
                        Moderasyon
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Sunucu moderasyon işlemlerini yönetin
                    </p>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {stats.map((stat) => (
                    <Card key={stat.label}>
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-4">
                                <div className={`p-3 rounded-lg bg-muted ${stat.color}`}>
                                    <stat.icon className="h-5 w-5" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{stat.value}</p>
                                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList>
                    <TabsTrigger value="warnings">
                        <AlertTriangle className="h-4 w-4 mr-2" />
                        Uyarılar
                    </TabsTrigger>
                    <TabsTrigger value="mutes">
                        <VolumeX className="h-4 w-4 mr-2" />
                        Susturmalar
                    </TabsTrigger>
                    <TabsTrigger value="bans">
                        <Ban className="h-4 w-4 mr-2" />
                        Yasaklar
                    </TabsTrigger>
                </TabsList>

                {/* Search */}
                <div className="flex gap-4 mt-4">
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Kullanıcı ara..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 bg-muted/50"
                        />
                    </div>
                </div>

                <TabsContent value="warnings" className="mt-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Aktif Uyarılar</CardTitle>
                            <CardDescription>Sunucudaki aktif kullanıcı uyarıları</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                </div>
                            ) : warnings.length > 0 ? (
                                <div className="space-y-4">
                                    {warnings.map((warning) => (
                                        <div key={warning.id} className="flex items-start gap-4 p-4 rounded-lg border border-border bg-card/50">
                                            <User className="h-8 w-8 text-muted-foreground" />
                                            <div className="flex-1">
                                                <p className="font-medium">{warning.username}</p>
                                                <p className="text-sm text-muted-foreground">{warning.reason}</p>
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    Moderatör: {warning.moderator}
                                                </p>
                                            </div>
                                            <Badge variant="outline" className="bg-warning/20 text-warning">
                                                <Clock className="h-3 w-3 mr-1" />
                                                Aktif
                                            </Badge>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-muted-foreground">
                                    <MessageSquareWarning className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <h3 className="text-lg font-semibold mb-2">Uyarı Bulunamadı</h3>
                                    <p>Henüz aktif uyarı bulunmuyor.</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="mutes" className="mt-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Susturmalar</CardTitle>
                            <CardDescription>Aktif ve geçmiş susturmalar</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                </div>
                            ) : mutes.length > 0 ? (
                                <div className="space-y-4">
                                    {mutes.map((mute) => (
                                        <div key={mute.id} className="flex items-start gap-4 p-4 rounded-lg border border-border bg-card/50">
                                            <VolumeX className={`h-8 w-8 ${mute.active ? 'text-orange-400' : 'text-muted-foreground'}`} />
                                            <div className="flex-1">
                                                <p className="font-medium">{mute.username}</p>
                                                <p className="text-sm text-muted-foreground">{mute.reason}</p>
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    Süre: {Math.floor(mute.duration / 60)} dakika
                                                </p>
                                            </div>
                                            <Badge variant={mute.active ? "default" : "secondary"}>
                                                {mute.active ? 'Aktif' : 'Bitti'}
                                            </Badge>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-muted-foreground">
                                    <VolumeX className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <h3 className="text-lg font-semibold mb-2">Susturma Bulunamadı</h3>
                                    <p>Henüz susturma kaydı bulunmuyor.</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="bans" className="mt-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Yasaklar</CardTitle>
                            <CardDescription>Sunucudan yasaklanan kullanıcılar</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                </div>
                            ) : bans.length > 0 ? (
                                <div className="space-y-4">
                                    {bans.map((ban) => (
                                        <div key={ban.id} className="flex items-start gap-4 p-4 rounded-lg border border-border bg-card/50">
                                            <Ban className="h-8 w-8 text-destructive" />
                                            <div className="flex-1">
                                                <p className="font-medium">{ban.username}</p>
                                                <p className="text-sm text-muted-foreground">{ban.reason}</p>
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    Moderatör: {ban.moderator}
                                                </p>
                                            </div>
                                            <Badge variant="destructive">
                                                {ban.permanent ? 'Kalıcı' : 'Geçici'}
                                            </Badge>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-muted-foreground">
                                    <ShieldAlert className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <h3 className="text-lg font-semibold mb-2">Yasak Bulunamadı</h3>
                                    <p>Henüz yasaklanan kullanıcı bulunmuyor.</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
