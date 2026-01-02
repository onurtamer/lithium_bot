'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuthStore, useGuildStore, useModuleStore, useUIStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { Sidebar, Header } from '@/components/layout';

interface GuildLayoutProps {
    children: React.ReactNode;
}

export default function GuildLayout({ children }: GuildLayoutProps) {
    const params = useParams();
    const router = useRouter();
    const guildId = params.guildId as string;

    const { user, setUser } = useAuthStore();
    const { guilds, setGuilds, setCurrentGuild } = useGuildStore();
    const { setModules } = useModuleStore();
    const { sidebarCollapsed } = useUIStore();
    const [isLoading, setIsLoading] = useState(true);

    const loadData = useCallback(async () => {
        try {
            // Load user if not already loaded
            if (!user) {
                const userData = await api.getMe();
                setUser(userData);
            }

            // Load guilds if not already loaded
            if (guilds.length === 0) {
                const guildsData = await api.getGuilds();
                setGuilds(guildsData);

                // Set current guild
                const guild = guildsData.find(g => g.id === guildId);
                if (guild) {
                    setCurrentGuild(guild);
                } else {
                    router.push('/app');
                    return;
                }
            } else {
                const guild = guilds.find(g => g.id === guildId);
                if (guild) {
                    setCurrentGuild(guild);
                } else {
                    router.push('/app');
                    return;
                }
            }

            // Load modules
            const modulesData = await api.getGuildModules(guildId);
            setModules(modulesData);

        } catch (error) {
            console.error('Failed to load guild data:', error);
            if (error instanceof Error && error.message.includes('401')) {
                router.push('/login');
            }
        } finally {
            setIsLoading(false);
        }
    }, [guildId, user, guilds, setUser, setGuilds, setCurrentGuild, setModules, router]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    if (isLoading) {
        return (
            <div className="min-h-screen bg-background">
                <div className="animate-pulse">
                    <div className="fixed left-0 top-0 h-screen w-[240px] bg-sidebar border-r border-border" />
                    <div className="ml-[240px]">
                        <div className="h-16 border-b border-border bg-background" />
                        <div className="p-6 space-y-4">
                            <div className="h-8 bg-muted rounded w-1/4" />
                            <div className="h-64 bg-muted rounded" />
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background">
            <Sidebar guildId={guildId} />
            <div className={cn(
                'transition-all duration-300',
                sidebarCollapsed ? 'ml-[68px]' : 'ml-[240px]'
            )}>
                <Header />
                <main className="p-6">
                    {children}
                </main>
            </div>
        </div>
    );
}
