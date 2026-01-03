'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api, type ModerationCase, type Warning } from '@/lib/api';
import {
    Gavel,
    AlertTriangle,
    Ban,
    VolumeX,
    Clock,
    User,
    Search,
    Loader2,
    ShieldAlert,
    MessageSquareWarning
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function ModerationPage() {
    const params = useParams();
    const guildId = params.guildId as string;
    const [activeTab, setActiveTab] = useState('all');
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [cases, setCases] = useState<ModerationCase[]>([]);
    const [warnings, setWarnings] = useState<Warning[]>([]);
    const [stats, setStats] = useState({ total: 0, warnings: 0, mutes: 0, bans: 0 });

    useEffect(() => {
        loadModerationData();
    }, [guildId]);

    const loadModerationData = async () => {
        setIsLoading(true);
        try {
            const [casesRes, warningsRes] = await Promise.all([
                api.getModeration(guildId),
                api.getModerationWarnings(guildId)
            ]);

            if (casesRes.ok) {
                setCases(casesRes.data.items);

                // Calculate stats
                const muteCount = casesRes.data.items.filter(c => c.action_type === 'MUTE' && c.active).length;
                const banCount = casesRes.data.items.filter(c => c.action_type === 'BAN').length;
                setStats({
                    total: casesRes.data.total,
                    warnings: warningsRes.ok ? warningsRes.data.total : 0,
                    mutes: muteCount,
                    bans: banCount
                });
            }

            if (warningsRes.ok) {
                setWarnings(warningsRes.data.items);
            }
        } catch (error) {
            console.error('Failed to load moderation data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const filteredCases = cases.filter(c => {
        const matchesSearch = !searchQuery ||
            c.user_id.includes(searchQuery) ||
            c.reason?.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesTab = activeTab === 'all' || c.action_type === activeTab.toUpperCase();
        return matchesSearch && matchesTab;
    });

    const statCards = [
        { label: 'Aktif Uyarılar', value: stats.warnings, icon: AlertTriangle, color: 'text-warning' },
        { label: 'Aktif Susturmalar', value: stats.mutes, icon: VolumeX, color: 'text-orange-400' },
        { label: 'Toplam Yasaklar', value: stats.bans, icon: Ban, color: 'text-destructive' },
    ];

    const getActionIcon = (type: string) => {
        switch (type) {
            case 'WARN': return <AlertTriangle className="h-5 w-5 text-warning" />;
            case 'MUTE': return <VolumeX className="h-5 w-5 text-orange-400" />;
            case 'BAN': return <Ban className="h-5 w-5 text-destructive" />;
            case 'KICK': return <User className="h-5 w-5 text-muted-foreground" />;
            default: return <ShieldAlert className="h-5 w-5 text-muted-foreground" />;
        }
    };

    const getActionLabel = (type: string) => {
        const labels: Record<string, string> = {
            'WARN': 'Uyarı',
            'MUTE': 'Susturma',
            'BAN': 'Yasak',
            'KICK': 'Atılma',
            'KARA': 'Kara Liste'
        };
        return labels[type] || type;
    };

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
                {statCards.map((stat) => (
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
                    <TabsTrigger value="all">
                        <ShieldAlert className="h-4 w-4 mr-2" />
                        Tümü ({cases.length})
                    </TabsTrigger>
                    <TabsTrigger value="warn">
                        <AlertTriangle className="h-4 w-4 mr-2" />
                        Uyarılar
                    </TabsTrigger>
                    <TabsTrigger value="mute">
                        <VolumeX className="h-4 w-4 mr-2" />
                        Susturmalar
                    </TabsTrigger>
                    <TabsTrigger value="ban">
                        <Ban className="h-4 w-4 mr-2" />
                        Yasaklar
                    </TabsTrigger>
                </TabsList>

                {/* Search */}
                <div className="flex gap-4 mt-4">
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Kullanıcı ID veya sebep ara..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 bg-muted/50"
                        />
                    </div>
                </div>

                <div className="mt-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Moderasyon Kayıtları</CardTitle>
                            <CardDescription>Tüm moderasyon işlemleri</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                </div>
                            ) : filteredCases.length > 0 ? (
                                <div className="space-y-3">
                                    {filteredCases.map((modCase) => (
                                        <div key={modCase.id} className="flex items-start gap-4 p-4 rounded-lg border border-border bg-card/50">
                                            <div className="mt-1">
                                                {getActionIcon(modCase.action_type)}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <p className="font-medium">Kullanıcı: {modCase.user_id}</p>
                                                    <Badge variant="outline"># {modCase.case_id}</Badge>
                                                </div>
                                                <p className="text-sm text-muted-foreground truncate">
                                                    {modCase.reason || 'Sebep belirtilmedi'}
                                                </p>
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    Moderatör: {modCase.moderator_id}
                                                </p>
                                            </div>
                                            <div className="flex flex-col items-end gap-1">
                                                <Badge variant={modCase.active ? "default" : "secondary"}>
                                                    {getActionLabel(modCase.action_type)}
                                                </Badge>
                                                <span className="text-xs text-muted-foreground flex items-center gap-1">
                                                    <Clock className="h-3 w-3" />
                                                    {new Date(modCase.created_at).toLocaleDateString('tr-TR')}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-muted-foreground">
                                    <MessageSquareWarning className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <h3 className="text-lg font-semibold mb-2">Kayıt Bulunamadı</h3>
                                    <p>Henüz moderasyon kaydı bulunmuyor.</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </Tabs>
        </div>
    );
}
