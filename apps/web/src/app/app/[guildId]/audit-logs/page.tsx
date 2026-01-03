'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api, type AuditLog, type BotEvent } from '@/lib/api';
import {
    FileText,
    Filter,
    CalendarDays,
    User,
    Settings,
    Loader2,
    RefreshCw,
    Activity
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';

export default function AuditLogsPage() {
    const params = useParams();
    const guildId = params.guildId as string;
    const [panelLogs, setPanelLogs] = useState<AuditLog[]>([]);
    const [botEvents, setBotEvents] = useState<BotEvent[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState('panel');

    useEffect(() => {
        loadLogs();
    }, [guildId, page, activeTab]);

    const loadLogs = async () => {
        setIsLoading(true);
        try {
            if (activeTab === 'panel') {
                const response = await api.getAuditLogs(guildId, page);
                setPanelLogs(response.items);
                setTotalPages(response.pages);
            } else {
                const response = await api.getBotEvents(guildId, page);
                setBotEvents(response.items);
                setTotalPages(response.pages);
            }
        } catch (error) {
            console.error('Failed to load logs:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleString('tr-TR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getActionBadgeColor = (action: string) => {
        if (action.includes('create') || action.includes('enable')) return 'bg-success/20 text-success';
        if (action.includes('delete') || action.includes('disable')) return 'bg-destructive/20 text-destructive';
        if (action.includes('update') || action.includes('change')) return 'bg-warning/20 text-warning';
        return 'bg-primary/20 text-primary';
    };

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <FileText className="h-6 w-6" />
                        Denetim Kayıtları
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Panel ve bot aktivitelerini takip edin
                    </p>
                </div>
                <Button onClick={loadLogs} variant="outline" size="sm">
                    <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                    Yenile
                </Button>
            </div>

            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={(v) => { setActiveTab(v); setPage(1); }}>
                <TabsList>
                    <TabsTrigger value="panel">
                        <Settings className="h-4 w-4 mr-2" />
                        Panel Kayıtları
                    </TabsTrigger>
                    <TabsTrigger value="bot">
                        <Activity className="h-4 w-4 mr-2" />
                        Bot Olayları
                    </TabsTrigger>
                </TabsList>

                {/* Search */}
                <div className="flex gap-4 mt-4">
                    <div className="relative flex-1 max-w-md">
                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Kayıtlarda ara..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 bg-muted/50"
                        />
                    </div>
                </div>

                <TabsContent value="panel" className="mt-4">
                    <Card>
                        <CardContent className="pt-6">
                            {isLoading ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                </div>
                            ) : panelLogs.length > 0 ? (
                                <div className="space-y-4">
                                    {panelLogs.map((log) => (
                                        <div key={log.id} className="flex items-start gap-4 p-4 rounded-lg border border-border bg-card/50">
                                            <div className="flex-shrink-0">
                                                <User className="h-5 w-5 text-muted-foreground" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    <span className="font-medium">{log.actor_name}</span>
                                                    <Badge variant="outline" className={getActionBadgeColor(log.action)}>
                                                        {log.action}
                                                    </Badge>
                                                    <span className="text-sm text-muted-foreground">
                                                        {log.target_type}: {log.target_id}
                                                    </span>
                                                </div>
                                                {log.diff_json && (
                                                    <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-x-auto">
                                                        {JSON.stringify(log.diff_json, null, 2)}
                                                    </pre>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-1 text-xs text-muted-foreground flex-shrink-0">
                                                <CalendarDays className="h-3 w-3" />
                                                {formatDate(log.created_at)}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-muted-foreground">
                                    <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <h3 className="text-lg font-semibold mb-2">Kayıt Bulunamadı</h3>
                                    <p>Henüz panel kayıtı bulunmuyor.</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="bot" className="mt-4">
                    <Card>
                        <CardContent className="pt-6">
                            {isLoading ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                </div>
                            ) : botEvents.length > 0 ? (
                                <div className="space-y-4">
                                    {botEvents.map((event) => (
                                        <div key={event.id} className="flex items-start gap-4 p-4 rounded-lg border border-border bg-card/50">
                                            <div className="flex-shrink-0">
                                                <Activity className="h-5 w-5 text-primary" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <Badge variant="outline">{event.event_type}</Badge>
                                                <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-x-auto">
                                                    {JSON.stringify(event.payload_json, null, 2)}
                                                </pre>
                                            </div>
                                            <div className="flex items-center gap-1 text-xs text-muted-foreground flex-shrink-0">
                                                <CalendarDays className="h-3 w-3" />
                                                {formatDate(event.created_at)}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-muted-foreground">
                                    <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <h3 className="text-lg font-semibold mb-2">Olay Bulunamadı</h3>
                                    <p>Henüz bot olayı bulunmuyor.</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                    >
                        Önceki
                    </Button>
                    <span className="text-sm text-muted-foreground">
                        Sayfa {page} / {totalPages}
                    </span>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                    >
                        Sonraki
                    </Button>
                </div>
            )}
        </div>
    );
}
