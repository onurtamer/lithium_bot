'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api, type GuildMetrics } from '@/lib/api';
import { useGuildStore, useModuleStore } from '@/lib/store';
import { formatRelativeTime } from '@/lib/utils';
import {
    Users,
    MessageSquare,
    Shield,
    TrendingUp,
    Activity,
    AlertTriangle,
    CheckCircle2,
    Clock,
    ArrowRight,
    BarChart3
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export default function DashboardPage() {
    const params = useParams();
    const guildId = params.guildId as string;
    const { currentGuild } = useGuildStore();
    const { modules } = useModuleStore();
    const [metrics, setMetrics] = useState<GuildMetrics | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadMetrics();
    }, [guildId]);

    const loadMetrics = async () => {
        try {
            const data = await api.getMetrics(guildId);
            setMetrics(data);
        } catch (error) {
            console.error('Failed to load metrics:', error);
            // Use fallback data
            setMetrics({
                members: { total: 0, online: 0, new_24h: 0 },
                messages: { today: 0, week: 0 },
                moderation: { actions_today: 0, warnings_active: 0 },
            });
        } finally {
            setIsLoading(false);
        }
    };

    const enabledModules = modules.filter(m => m.enabled).length;
    const totalModules = modules.length;

    const statCards = [
        {
            title: 'Toplam Üye',
            value: metrics?.members.total.toLocaleString('tr-TR') || '—',
            subtitle: `${metrics?.members.online || 0} çevrimiçi`,
            icon: Users,
            color: 'text-blue-400',
            bgColor: 'bg-blue-400/10',
        },
        {
            title: 'Bugünkü Mesaj',
            value: metrics?.messages.today.toLocaleString('tr-TR') || '—',
            subtitle: `Bu hafta ${metrics?.messages.week.toLocaleString('tr-TR') || 0}`,
            icon: MessageSquare,
            color: 'text-green-400',
            bgColor: 'bg-green-400/10',
        },
        {
            title: 'Moderasyon',
            value: metrics?.moderation.actions_today.toString() || '—',
            subtitle: `${metrics?.moderation.warnings_active || 0} aktif uyarı`,
            icon: Shield,
            color: 'text-orange-400',
            bgColor: 'bg-orange-400/10',
        },
        {
            title: 'Aktif Modül',
            value: `${enabledModules}/${totalModules}`,
            subtitle: 'modül aktif',
            icon: Activity,
            color: 'text-purple-400',
            bgColor: 'bg-purple-400/10',
        },
    ];

    return (
        <div className="space-y-8 animate-fadeIn">
            {/* Welcome Header */}
            <div>
                <h1 className="text-2xl font-bold">
                    Hoş Geldiniz, {currentGuild?.name || 'Sunucu'}
                </h1>
                <p className="text-muted-foreground mt-1">
                    Sunucu durumunuza ve son aktivitelere buradan göz atabilirsiniz.
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {statCards.map((stat) => (
                    <Card key={stat.title}>
                        <CardContent className="pt-6">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">{stat.title}</p>
                                    <p className="text-2xl font-bold mt-1">{stat.value}</p>
                                    <p className="text-xs text-muted-foreground mt-1">{stat.subtitle}</p>
                                </div>
                                <div className={`${stat.bgColor} p-2 rounded-lg`}>
                                    <stat.icon className={`h-5 w-5 ${stat.color}`} />
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Quick Actions */}
                <Card className="lg:col-span-2">
                    <CardHeader>
                        <CardTitle>Hızlı Erişim</CardTitle>
                        <CardDescription>En çok kullanılan işlemler</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            <QuickActionButton
                                href={`/app/${guildId}/modules`}
                                icon={Activity}
                                label="Modüller"
                            />
                            <QuickActionButton
                                href={`/app/${guildId}/audit-logs`}
                                icon={Shield}
                                label="Denetim"
                            />
                            <QuickActionButton
                                href={`/app/${guildId}/analytics`}
                                icon={BarChart3}
                                label="Analytics"
                            />
                            <QuickActionButton
                                href={`/app/${guildId}/settings`}
                                icon={TrendingUp}
                                label="Ayarlar"
                            />
                        </div>
                    </CardContent>
                </Card>

                {/* System Status */}
                <Card>
                    <CardHeader>
                        <CardTitle>Sistem Durumu</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <StatusItem label="Bot" status="online" />
                        <StatusItem label="API" status="online" />
                        <StatusItem label="Database" status="online" />
                        <StatusItem label="Cache" status="online" />
                    </CardContent>
                </Card>
            </div>

            {/* Recent Activity */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                    <div>
                        <CardTitle>Son Aktiviteler</CardTitle>
                        <CardDescription>Sunucunuzdaki son olaylar</CardDescription>
                    </div>
                    <Button variant="outline" size="sm" asChild>
                        <Link href={`/app/${guildId}/audit-logs`}>
                            Tümünü Gör
                            <ArrowRight className="h-4 w-4 ml-2" />
                        </Link>
                    </Button>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <ActivityItem
                            icon={Shield}
                            title="AutoMod tetiklendi"
                            description="Spam mesaj algılandı ve silindi"
                            time="2 dakika önce"
                            type="warning"
                        />
                        <ActivityItem
                            icon={Users}
                            title="Yeni üye katıldı"
                            description="3 yeni üye sunucuya katıldı"
                            time="15 dakika önce"
                            type="info"
                        />
                        <ActivityItem
                            icon={CheckCircle2}
                            title="Modül güncellendi"
                            description="Leveling ayarları güncellendi"
                            time="1 saat önce"
                            type="success"
                        />
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

interface QuickActionButtonProps {
    href: string;
    icon: React.ComponentType<{ className?: string }>;
    label: string;
}

function QuickActionButton({ href, icon: Icon, label }: QuickActionButtonProps) {
    return (
        <Link
            href={href}
            className="flex flex-col items-center gap-2 p-4 rounded-lg border border-border bg-card hover:bg-accent transition-colors"
        >
            <Icon className="h-6 w-6 text-primary" />
            <span className="text-sm font-medium">{label}</span>
        </Link>
    );
}

interface StatusItemProps {
    label: string;
    status: 'online' | 'degraded' | 'offline';
}

function StatusItem({ label, status }: StatusItemProps) {
    const statusConfig = {
        online: { color: 'bg-success', text: 'Çalışıyor' },
        degraded: { color: 'bg-warning', text: 'Yavaş' },
        offline: { color: 'bg-destructive', text: 'Çevrimdışı' },
    };

    const config = statusConfig[status];

    return (
        <div className="flex items-center justify-between">
            <span className="text-sm">{label}</span>
            <div className="flex items-center gap-2">
                <div className={`h-2 w-2 rounded-full ${config.color}`} />
                <span className="text-xs text-muted-foreground">{config.text}</span>
            </div>
        </div>
    );
}

interface ActivityItemProps {
    icon: React.ComponentType<{ className?: string }>;
    title: string;
    description: string;
    time: string;
    type: 'success' | 'warning' | 'info' | 'error';
}

function ActivityItem({ icon: Icon, title, description, time, type }: ActivityItemProps) {
    const typeColors = {
        success: 'text-success',
        warning: 'text-warning',
        info: 'text-primary',
        error: 'text-destructive',
    };

    return (
        <div className="flex items-start gap-3">
            <div className={`mt-0.5 ${typeColors[type]}`}>
                <Icon className="h-4 w-4" />
            </div>
            <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{title}</p>
                <p className="text-xs text-muted-foreground truncate">{description}</p>
            </div>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                {time}
            </div>
        </div>
    );
}
