'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useAuthStore, useUIStore, useModuleStore } from '@/lib/store';
import { api } from '@/lib/api';
import { getDiscordAvatar } from '@/lib/utils';
import { GuildSwitcher } from './GuildSwitcher';
import {
    Bell,
    Moon,
    Sun,
    Search,
    LogOut,
    User,
    Settings,
    HelpCircle,
    AlertCircle
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
import { Input } from '@/components/ui/input';

interface HeaderProps {
    showGuildSwitcher?: boolean;
}

export function Header({ showGuildSwitcher = true }: HeaderProps) {
    const { user, logout } = useAuthStore();
    const { theme, setTheme } = useUIStore();
    const { hasUnsavedChanges } = useModuleStore();

    const handleLogout = async () => {
        try {
            await api.logout();
            logout();
            window.location.href = '/';
        } catch (error) {
            console.error('Logout failed:', error);
        }
    };

    const toggleTheme = () => {
        setTheme(theme === 'dark' ? 'light' : 'dark');
    };

    return (
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6">
            {/* Left Section */}
            <div className="flex items-center gap-4">
                {showGuildSwitcher && <GuildSwitcher />}
            </div>

            {/* Center - Search */}
            <div className="hidden md:flex flex-1 max-w-md mx-8">
                <div className="relative w-full">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                        placeholder="Modül, ayar veya komut ara..."
                        className="pl-9 bg-muted/50"
                    />
                </div>
            </div>

            {/* Right Section */}
            <div className="flex items-center gap-2">
                {/* Unsaved Changes Warning */}
                {hasUnsavedChanges && (
                    <Badge variant="outline" className="border-warning text-warning gap-1">
                        <AlertCircle className="h-3 w-3" />
                        Kaydedilmemiş değişiklikler
                    </Badge>
                )}

                {/* Theme Toggle */}
                <Button variant="ghost" size="icon" onClick={toggleTheme}>
                    {theme === 'dark' ? (
                        <Sun className="h-5 w-5" />
                    ) : (
                        <Moon className="h-5 w-5" />
                    )}
                </Button>

                {/* Notifications */}
                <Button variant="ghost" size="icon" className="relative">
                    <Bell className="h-5 w-5" />
                    <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-destructive" />
                </Button>

                {/* Help */}
                <Button variant="ghost" size="icon" asChild>
                    <Link href="/docs">
                        <HelpCircle className="h-5 w-5" />
                    </Link>
                </Button>

                {/* User Menu */}
                {user && (
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" className="relative h-9 w-9 rounded-full">
                                <Image
                                    src={getDiscordAvatar(user.discord_id, user.avatar_url)}
                                    alt={user.username}
                                    fill
                                    className="rounded-full object-cover"
                                />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-56">
                            <DropdownMenuLabel>
                                <div className="flex flex-col space-y-1">
                                    <p className="text-sm font-medium leading-none">{user.username}</p>
                                    <p className="text-xs leading-none text-muted-foreground">
                                        ID: {user.discord_id}
                                    </p>
                                </div>
                            </DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem asChild>
                                <Link href="/app/account">
                                    <User className="mr-2 h-4 w-4" />
                                    Hesabım
                                </Link>
                            </DropdownMenuItem>
                            <DropdownMenuItem asChild>
                                <Link href="/app/account/settings">
                                    <Settings className="mr-2 h-4 w-4" />
                                    Ayarlar
                                </Link>
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
                                <LogOut className="mr-2 h-4 w-4" />
                                Çıkış Yap
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                )}
            </div>
        </header>
    );
}
