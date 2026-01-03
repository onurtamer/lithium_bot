'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api, type DashboardData, type ServiceStatus, type RecentActivity } from '@/lib/api';
import { useGuildStore, useModuleStore } from '@/lib/store';
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
    BarChart3,
    Settings,
    VolumeX,
    Ban,
    Loader2,
    Wifi,
    WifiOff,
    type LucideIcon
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

// Icon mapping for dynamic activities
const ICON_MAP: Record<string, LucideIcon> = {
    Shield,
    Users,
    MessageSquare,
    CheckCircle2,
    Settings,
    AlertTriangle,
    VolumeX,
    Ban,
    Activity,
};

export default function DashboardPage() {
    const params = useParams();
    const guildId = params.guildId as string;
    const { currentGuild } = useGuildStore();
    const { modules } = useModuleStore();
    const [dashboard, setDashboard] = useState<DashboardData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isConnected, setIsConnected] = useState(false);
    const eventSourceRef = useRef<EventSource | null>(null);

    useEffect(() => {
        loadDashboardData();
        setupSSE();

        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, [guildId]);

    const loadDashboardData = async () => {
        setIsLoading(true);
        try {
            const response = await api.getDashboard(guildId);
            if (response.ok) {
                setDashboard(response.data);
            }
        } catch (error) {
            console.error('Failed to load dashboard:', error);
            // Fallback data
            setDashboard({
                members: { total: 0, online: 0, new_24h: 0 },
                messages: { today: 0, week: 0 },
                moderation: { actions_today: 0, warnings_active: 0 },
                modules: { enabled: 0, total: 15 },
                system_status: [
                    { name: 'Bot', status: 'online' },
                    { name: 'API', status: 'online' },
                    { name: 'Database', status: 'online' },
                    { name: 'Cache', status: 'online' },
                ],
                recent_activities: []
            });
        } finally {
            setIsLoading(false);
        }
    };

    const setupSSE = () => {
        try {
            const es = api.createEventSource(guildId);
            eventSourceRef.current = es;

            es.onopen = () => {
                setIsConnected(true);
            };

            es.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'stats_update' && dashboard) {
                        setDashboard(prev => prev ? {
                            ...prev,
                            members: data.data.members || prev.members,
                            messages: data.data.messages || prev.messages,
                            system_status: prev.system_status.map(s =>
                                s.name === 'Bot' ? { ...s, status: data.data.bot_status } : s
                            )
                        } : prev);
                    }
                } catch (e) {
                    console.warn('SSE parse error:', e);
                }
            };

            es.onerror = () => {
                setIsConnected(false);
                es.close();
                // Retry after 5s
                setTimeout(setupSSE, 5000);
            };
        } catch (e) {
            console.warn('SSE setup failed:', e);
        }
    };

    const enabledModules = modules.filter(m => m.enabled).length;
    const totalModules = modules.length || dashboard?.modules.total || 15;

    const statCards = [
        {
            title: 'Toplam Üye',
            value: dashboard?.members.total.toLocaleString('tr-TR') || '—',
            subtitle: `${dashboard?.members.online || 0} çevrimiçi`,
            icon: Users,
            color: 'text-blue-400',
            bgColor: 'bg-blue-400/10',
        },
        {
            title: 'Bugünkü Mesaj',
            value: dashboard?.messages.today.toLocaleString('tr-TR') || '—',
            subtitle: `Bu hafta ${dashboard?.messages.week.toLocaleString('tr-TR') || 0}`,
            icon: MessageSquare,
            color: 'text-green-400',
            bgColor: 'bg-green-400/10',
        },
        {
            title: 'Moderasyon',
            value: dashboard?.moderation.actions_today.toString() || '—',
            subtitle: `${dashboard?.moderation.warnings_active || 0} aktif uyarı`,
            icon: Shield,
            color: 'text-orange-400',
            bgColor: 'bg-orange-400/10',
        },
        {
            title: 'Aktif Modül',
            value: `${enabledModules || dashboard?.modules.enabled || 0}/${totalModules}`,
            subtitle: 'modül aktif',
            icon: Activity,
            color: 'text-purple-400',
            bgColor: 'bg-purple-400/10',
        },
    ];

    return (
        <div className="space-y-8 animate-fadeIn">
            {/* Welcome Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">
                        Hoş Geldiniz, {currentGuild?.name || 'Sunucu'}
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Sunucu durumunuza ve son aktivitelere buradan göz atabilirsiniz.
                    </p>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {isConnected ? (
                        <>
                            <Wifi className="h-3 w-3 text-success" />
                            <span>Canlı</span>
                        </>
                    ) : (
                        <>
                            <WifiOff className="h-3 w-3 text-muted-foreground" />
                            <span>Bağlantı yok</span>
                        </>
                    )}
                </div>
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
                                icon={Settings}
                                label="Ayarlar"
                            />
                        </div>
                    </CardContent>
                </Card>

                {/* System Status - DYNAMIC */}
                <Card>
                    <CardHeader>
                        <CardTitle>Sistem Durumu</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {isLoading ? (
                            <div className="flex items-center justify-center py-4">
                                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                            </div>
                        ) : (
                            dashboard?.system_status.map((service) => (
                                <StatusItem
                                    key={service.name}
                                    label={service.name}
                                    status={service.status as 'online' | 'degraded' | 'offline'}
                                    latency={service.latency_ms}
                                />
                            ))
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Recent Activity - DYNAMIC */}
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
                    {isLoading ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        </div>
                    ) : dashboard?.recent_activities && dashboard.recent_activities.length > 0 ? (
                        <div className="space-y-4">
                            {dashboard.recent_activities.map((activity) => (
                                <ActivityItem
                                    key={activity.id}
                                    icon={ICON_MAP[activity.icon] || Activity}
                                    title={activity.title}
                                    description={activity.description}
                                    time={activity.time}
                                    type={activity.severity as 'success' | 'warning' | 'info' | 'error'}
                                />
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-muted-foreground">
                            <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                            <p>Henüz aktivite bulunmuyor</p>
                        </div>
                    )}
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
    latency?: number;
}

function StatusItem({ label, status, latency }: StatusItemProps) {
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
                <span className="text-xs text-muted-foreground">
                    {config.text}
                    {latency !== undefined && latency !== null && ` (${latency}ms)`}
                </span>
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
