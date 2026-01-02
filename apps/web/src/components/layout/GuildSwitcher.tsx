'use client';

import { useState } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { cn, getGuildIcon } from '@/lib/utils';
import { useGuildStore } from '@/lib/store';
import type { Guild } from '@/lib/api';
import {
    ChevronDown,
    Check,
    Plus,
    Bot
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';

interface GuildSwitcherProps {
    className?: string;
}

export function GuildSwitcher({ className }: GuildSwitcherProps) {
    const router = useRouter();
    const { guilds, currentGuild, setCurrentGuild } = useGuildStore();
    const [isOpen, setIsOpen] = useState(false);

    const handleGuildSelect = (guild: Guild) => {
        setCurrentGuild(guild);
        router.push(`/app/${guild.id}/dashboard`);
        setIsOpen(false);
    };

    const handleAddBot = (guildId: string) => {
        // Open Discord OAuth with bot invite
        const clientId = process.env.NEXT_PUBLIC_DISCORD_CLIENT_ID;
        const permissions = '8'; // Administrator for full functionality
        const redirectUri = encodeURIComponent(window.location.origin + '/app');
        window.open(
            `https://discord.com/api/oauth2/authorize?client_id=${clientId}&permissions=${permissions}&scope=bot%20applications.commands&guild_id=${guildId}&redirect_uri=${redirectUri}`,
            '_blank'
        );
    };

    if (!currentGuild) {
        return (
            <div className={cn('flex items-center gap-2 px-3 py-2 text-muted-foreground', className)}>
                <Bot className="h-5 w-5" />
                <span className="text-sm">Sunucu seçin</span>
            </div>
        );
    }

    return (
        <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="ghost"
                    className={cn(
                        'flex items-center gap-3 px-3 py-2 h-auto justify-start',
                        className
                    )}
                >
                    <div className="relative h-8 w-8 overflow-hidden rounded-lg">
                        <Image
                            src={getGuildIcon(currentGuild.id, currentGuild.icon)}
                            alt={currentGuild.name}
                            fill
                            className="object-cover"
                        />
                    </div>
                    <div className="flex flex-col items-start text-left">
                        <span className="text-sm font-medium truncate max-w-[150px]">
                            {currentGuild.name}
                        </span>
                        {currentGuild.owner && (
                            <span className="text-xs text-muted-foreground">Sahip</span>
                        )}
                    </div>
                    <ChevronDown className="h-4 w-4 ml-auto text-muted-foreground" />
                </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="start" className="w-[280px]">
                <DropdownMenuLabel>Sunucularınız</DropdownMenuLabel>
                <DropdownMenuSeparator />

                <div className="max-h-[300px] overflow-y-auto">
                    {guilds.map((guild) => (
                        <DropdownMenuItem
                            key={guild.id}
                            className="flex items-center gap-3 cursor-pointer py-2"
                            onClick={() => handleGuildSelect(guild)}
                        >
                            <div className="relative h-8 w-8 overflow-hidden rounded-lg flex-shrink-0">
                                <Image
                                    src={getGuildIcon(guild.id, guild.icon)}
                                    alt={guild.name}
                                    fill
                                    className="object-cover"
                                />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium truncate">{guild.name}</span>
                                    {guild.id === currentGuild.id && (
                                        <Check className="h-4 w-4 text-primary flex-shrink-0" />
                                    )}
                                </div>
                                <div className="flex items-center gap-2 mt-0.5">
                                    {guild.owner && (
                                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                                            Sahip
                                        </Badge>
                                    )}
                                    {guild.bot_installed !== false ? (
                                        <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-success text-success">
                                            Bot Aktif
                                        </Badge>
                                    ) : (
                                        <Badge
                                            variant="outline"
                                            className="text-[10px] px-1.5 py-0 border-warning text-warning cursor-pointer hover:bg-warning/10"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleAddBot(guild.id);
                                            }}
                                        >
                                            <Plus className="h-3 w-3 mr-0.5" />
                                            Bot Ekle
                                        </Badge>
                                    )}
                                </div>
                            </div>
                        </DropdownMenuItem>
                    ))}
                </div>

                <DropdownMenuSeparator />
                <DropdownMenuItem
                    className="text-muted-foreground"
                    onClick={() => {
                        const clientId = process.env.NEXT_PUBLIC_DISCORD_CLIENT_ID;
                        window.open(
                            `https://discord.com/api/oauth2/authorize?client_id=${clientId}&permissions=8&scope=bot%20applications.commands`,
                            '_blank'
                        );
                    }}
                >
                    <Plus className="h-4 w-4 mr-2" />
                    Yeni sunucuya ekle
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
