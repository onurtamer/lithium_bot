'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api, type TicketItem } from '@/lib/api';
import {
    Ticket,
    Clock,
    User,
    Search,
    Loader2,
    MessageSquare,
    CheckCircle,
    AlertCircle,
    XCircle
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function TicketsPage() {
    const params = useParams();
    const guildId = params.guildId as string;
    const [activeTab, setActiveTab] = useState('open');
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [tickets, setTickets] = useState<TicketItem[]>([]);
    const [counts, setCounts] = useState({ open: 0, claimed: 0, closed: 0 });

    useEffect(() => {
        loadTickets();
    }, [guildId, activeTab]);

    const loadTickets = async () => {
        setIsLoading(true);
        try {
            const status = activeTab === 'pending' ? 'claimed' : activeTab;
            const response = await api.getTickets(guildId, status);

            if (response.ok) {
                setTickets(response.data.items);
                setCounts(response.data.counts);
            }
        } catch (error) {
            console.error('Failed to load tickets:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCloseTicket = async (ticketId: number) => {
        try {
            await api.updateTicket(guildId, ticketId, 'closed');
            loadTickets();
        } catch (error) {
            console.error('Failed to close ticket:', error);
        }
    };

    const filteredTickets = tickets.filter(t =>
        !searchQuery ||
        t.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.user_id.includes(searchQuery)
    );

    const stats = [
        { label: 'Açık Ticketlar', value: counts.open, icon: AlertCircle, color: 'text-blue-400' },
        { label: 'Beklemede', value: counts.claimed, icon: Clock, color: 'text-warning' },
        { label: 'Kapatılmış', value: counts.closed, icon: CheckCircle, color: 'text-success' },
    ];

    const getStatusBadge = (status: string) => {
        switch (status.toLowerCase()) {
            case 'open':
                return <Badge className="bg-blue-500/20 text-blue-400">Açık</Badge>;
            case 'claimed':
                return <Badge className="bg-warning/20 text-warning">Beklemede</Badge>;
            case 'closed':
                return <Badge variant="secondary">Kapalı</Badge>;
            default:
                return <Badge variant="outline">{status}</Badge>;
        }
    };

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Ticket className="h-6 w-6" />
                        Ticket Sistemi
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Destek taleplerini yönetin
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
                    <TabsTrigger value="open">
                        <AlertCircle className="h-4 w-4 mr-2" />
                        Açık ({counts.open})
                    </TabsTrigger>
                    <TabsTrigger value="pending">
                        <Clock className="h-4 w-4 mr-2" />
                        Beklemede ({counts.claimed})
                    </TabsTrigger>
                    <TabsTrigger value="closed">
                        <CheckCircle className="h-4 w-4 mr-2" />
                        Kapalı ({counts.closed})
                    </TabsTrigger>
                </TabsList>

                {/* Search */}
                <div className="flex gap-4 mt-4">
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Ticket ara..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 bg-muted/50"
                        />
                    </div>
                </div>

                <div className="mt-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Ticketlar</CardTitle>
                            <CardDescription>Destek talepleri listesi</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                </div>
                            ) : filteredTickets.length > 0 ? (
                                <div className="space-y-3">
                                    {filteredTickets.map((ticket) => (
                                        <div key={ticket.id} className="flex items-start gap-4 p-4 rounded-lg border border-border bg-card/50">
                                            <div className="p-2 rounded-lg bg-muted">
                                                <Ticket className="h-5 w-5 text-primary" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <p className="font-medium">#{ticket.id} - {ticket.subject}</p>
                                                </div>
                                                <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                                                    <User className="h-3 w-3" />
                                                    <span>{ticket.user_id}</span>
                                                    <span className="mx-1">•</span>
                                                    <MessageSquare className="h-3 w-3" />
                                                    <span>{ticket.messages_count} mesaj</span>
                                                </div>
                                            </div>
                                            <div className="flex flex-col items-end gap-2">
                                                {getStatusBadge(ticket.status)}
                                                <span className="text-xs text-muted-foreground flex items-center gap-1">
                                                    <Clock className="h-3 w-3" />
                                                    {new Date(ticket.created_at).toLocaleDateString('tr-TR')}
                                                </span>
                                                {ticket.status !== 'closed' && (
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        onClick={() => handleCloseTicket(ticket.id)}
                                                    >
                                                        <XCircle className="h-3 w-3 mr-1" />
                                                        Kapat
                                                    </Button>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-muted-foreground">
                                    <Ticket className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <h3 className="text-lg font-semibold mb-2">Ticket Bulunamadı</h3>
                                    <p>Bu kategoride ticket bulunmuyor.</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </Tabs>
        </div>
    );
}
