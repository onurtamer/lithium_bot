'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api, type GuildMetrics } from '@/lib/api';
import {
    BarChart3,
    Users,
    MessageSquare,
    TrendingUp,
    TrendingDown,
    Activity,
    Calendar,
    Loader2,
    RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function AnalyticsPage() {
    const params = useParams();
    const guildId = params.guildId as string;
    const [metrics, setMetrics] = useState<GuildMetrics | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [timeRange, setTimeRange] = useState('week');

    useEffect(() => {
        loadMetrics();
    }, [guildId, timeRange]);

    const loadMetrics = async () => {
        setIsLoading(true);
        try {
            const data = await api.getMetrics(guildId);
            setMetrics(data);
        } catch (error) {
            console.error('Failed to load metrics:', error);
            setMetrics({
                members: { total: 0, online: 0, new_24h: 0 },
                messages: { today: 0, week: 0 },
                moderation: { actions_today: 0, warnings_active: 0 },
            });
        } finally {
            setIsLoading(false);
        }
    };

    const statCards = [
        {
            title: 'Toplam Üye',
            value: metrics?.members.total || 0,
            change: metrics?.members.new_24h || 0,
            changeLabel: 'son 24 saat',
            icon: Users,
            color: 'text-blue-400',
            bgColor: 'bg-blue-400/10',
            positive: true,
        },
        {
            title: 'Mesaj Trafiği',
            value: metrics?.messages.today || 0,
            change: metrics?.messages.week || 0,
            changeLabel: 'bu hafta',
            icon: MessageSquare,
            color: 'text-green-400',
            bgColor: 'bg-green-400/10',
            positive: true,
        },
        {
            title: 'Moderasyon Aksiyonları',
            value: metrics?.moderation.actions_today || 0,
            change: metrics?.moderation.warnings_active || 0,
            changeLabel: 'aktif uyarı',
            icon: Activity,
            color: 'text-orange-400',
            bgColor: 'bg-orange-400/10',
            positive: false,
        },
        {
            title: 'XP Kazanımı',
            value: metrics?.leveling?.xp_today || 0,
            change: metrics?.leveling?.active_users || 0,
            changeLabel: 'aktif kullanıcı',
            icon: TrendingUp,
            color: 'text-purple-400',
            bgColor: 'bg-purple-400/10',
            positive: true,
        },
    ];

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <BarChart3 className="h-6 w-6" />
                        Analytics
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Sunucu istatistiklerini ve trendleri inceleyin
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Button onClick={loadMetrics} variant="outline" size="sm">
                        <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                        Yenile
                    </Button>
                </div>
            </div>

            {/* Time Range */}
            <Tabs value={timeRange} onValueChange={setTimeRange}>
                <TabsList>
                    <TabsTrigger value="day">
                        <Calendar className="h-4 w-4 mr-2" />
                        Bugün
                    </TabsTrigger>
                    <TabsTrigger value="week">
                        Bu Hafta
                    </TabsTrigger>
                    <TabsTrigger value="month">
                        Bu Ay
                    </TabsTrigger>
                </TabsList>
            </Tabs>

            {/* Stats Grid */}
            {isLoading ? (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            ) : (
                <>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {statCards.map((stat) => (
                            <Card key={stat.title}>
                                <CardContent className="pt-6">
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <p className="text-sm text-muted-foreground">{stat.title}</p>
                                            <p className="text-2xl font-bold mt-1">
                                                {stat.value.toLocaleString('tr-TR')}
                                            </p>
                                            <div className="flex items-center gap-1 mt-1">
                                                {stat.positive ? (
                                                    <TrendingUp className="h-3 w-3 text-success" />
                                                ) : (
                                                    <TrendingDown className="h-3 w-3 text-warning" />
                                                )}
                                                <span className="text-xs text-muted-foreground">
                                                    {stat.change} {stat.changeLabel}
                                                </span>
                                            </div>
                                        </div>
                                        <div className={`${stat.bgColor} p-2 rounded-lg`}>
                                            <stat.icon className={`h-5 w-5 ${stat.color}`} />
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>

                    {/* Charts Placeholder */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Üye Büyümesi</CardTitle>
                                <CardDescription>Zaman içinde üye sayısı değişimi</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="h-64 flex items-center justify-center border border-dashed border-border rounded-lg bg-muted/20">
                                    <div className="text-center text-muted-foreground">
                                        <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
                                        <p>Grafik verisi hazırlanıyor...</p>
                                        <p className="text-xs mt-1">Discord API entegrasyonu sonrası aktif olacak</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle>Mesaj Aktivitesi</CardTitle>
                                <CardDescription>Saatlik mesaj dağılımı</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="h-64 flex items-center justify-center border border-dashed border-border rounded-lg bg-muted/20">
                                    <div className="text-center text-muted-foreground">
                                        <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                                        <p>Grafik verisi hazırlanıyor...</p>
                                        <p className="text-xs mt-1">Mesaj tracking aktif olunca gösterilecek</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Activity Heatmap Placeholder */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Aktivite Haritası</CardTitle>
                            <CardDescription>Haftalık aktivite yoğunluğu</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="h-48 flex items-center justify-center border border-dashed border-border rounded-lg bg-muted/20">
                                <div className="text-center text-muted-foreground">
                                    <Activity className="h-12 w-12 mx-auto mb-2 opacity-50" />
                                    <p>Aktivite haritası hazırlanıyor...</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </>
            )}
        </div>
    );
}
