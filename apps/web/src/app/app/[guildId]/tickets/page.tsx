'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import {
    Ticket,
    Plus,
    Search,
    Filter,
    Loader2,
    Clock,
    CheckCircle2,
    XCircle,
    User,
    MessageSquare,
    Settings
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface TicketData {
    id: string;
    channel_id: string;
    user_id: string;
    username: string;
    subject: string;
    status: 'open' | 'pending' | 'closed';
    created_at: string;
    closed_at?: string;
    messages_count: number;
}

export default function TicketsPage() {
    const params = useParams();
    const guildId = params.guildId as string;
    const [activeTab, setActiveTab] = useState('open');
    const [isLoading, setIsLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    // Placeholder data - would come from API
    const [tickets, setTickets] = useState<TicketData[]>([]);

    useEffect(() => {
        setIsLoading(true);
        // Simulate API call
        setTimeout(() => {
            setIsLoading(false);
        }, 500);
    }, [guildId, activeTab]);

    const openCount = tickets.filter(t => t.status === 'open').length;
    const pendingCount = tickets.filter(t => t.status === 'pending').length;
    const closedCount = tickets.filter(t => t.status === 'closed').length;

    const stats = [
        { label: 'Açık', value: openCount, icon: Ticket, color: 'text-success' },
        { label: 'Beklemede', value: pendingCount, icon: Clock, color: 'text-warning' },
        { label: 'Kapalı', value: closedCount, icon: CheckCircle2, color: 'text-muted-foreground' },
    ];

    const filteredTickets = tickets.filter(t => {
        if (activeTab === 'open') return t.status === 'open';
        if (activeTab === 'pending') return t.status === 'pending';
        if (activeTab === 'closed') return t.status === 'closed';
        return true;
    }).filter(t =>
        t.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.subject.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'open':
                return <Badge className="bg-success/20 text-success">Açık</Badge>;
            case 'pending':
                return <Badge className="bg-warning/20 text-warning">Beklemede</Badge>;
            case 'closed':
                return <Badge variant="secondary">Kapalı</Badge>;
            default:
                return null;
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
                <Button>
                    <Settings className="h-4 w-4 mr-2" />
                    Ayarlar
                </Button>
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
                        Açık ({openCount})
                    </TabsTrigger>
                    <TabsTrigger value="pending">
                        Beklemede ({pendingCount})
                    </TabsTrigger>
                    <TabsTrigger value="closed">
                        Kapalı ({closedCount})
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
                        <CardContent className="pt-6">
                            {isLoading ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                                </div>
                            ) : filteredTickets.length > 0 ? (
                                <div className="space-y-4">
                                    {filteredTickets.map((ticket) => (
                                        <div key={ticket.id} className="flex items-start gap-4 p-4 rounded-lg border border-border bg-card/50 hover:bg-accent/50 transition-colors cursor-pointer">
                                            <div className="flex-shrink-0">
                                                <User className="h-8 w-8 text-muted-foreground" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <p className="font-medium">{ticket.username}</p>
                                                    {getStatusBadge(ticket.status)}
                                                </div>
                                                <p className="text-sm text-muted-foreground truncate">{ticket.subject}</p>
                                                <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                                    <span className="flex items-center gap-1">
                                                        <MessageSquare className="h-3 w-3" />
                                                        {ticket.messages_count} mesaj
                                                    </span>
                                                    <span className="flex items-center gap-1">
                                                        <Clock className="h-3 w-3" />
                                                        {new Date(ticket.created_at).toLocaleDateString('tr-TR')}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-12 text-muted-foreground">
                                    <Ticket className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <h3 className="text-lg font-semibold mb-2">Ticket Bulunamadı</h3>
                                    <p>Bu kategoride henüz ticket bulunmuyor.</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </Tabs>
        </div>
    );
}
