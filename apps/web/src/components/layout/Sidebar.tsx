'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useUIStore } from '@/lib/store';
import {
    LayoutDashboard,
    Grid3X3,
    FileText,
    Gavel,
    Ticket,
    BarChart3,
    Settings,
    ChevronLeft,
    ChevronRight,
    Home,
    type LucideIcon
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface NavItem {
    label: string;
    href: string;
    icon: LucideIcon;
}

interface SidebarProps {
    guildId: string;
}

export function Sidebar({ guildId }: SidebarProps) {
    const pathname = usePathname();
    const { sidebarCollapsed, toggleSidebar } = useUIStore();

    const navItems: NavItem[] = [
        { label: 'Dashboard', href: `/app/${guildId}/dashboard`, icon: LayoutDashboard },
        { label: 'Modüller', href: `/app/${guildId}/modules`, icon: Grid3X3 },
        { label: 'Denetim Kayıtları', href: `/app/${guildId}/audit-logs`, icon: FileText },
        { label: 'Moderasyon', href: `/app/${guildId}/moderation`, icon: Gavel },
        { label: 'Tickets', href: `/app/${guildId}/tickets`, icon: Ticket },
        { label: 'Analytics', href: `/app/${guildId}/analytics`, icon: BarChart3 },
        { label: 'Ayarlar', href: `/app/${guildId}/settings`, icon: Settings },
    ];

    return (
        <TooltipProvider delayDuration={0}>
            <aside
                className={cn(
                    'fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-border bg-sidebar transition-all duration-300',
                    sidebarCollapsed ? 'w-[68px]' : 'w-[240px]'
                )}
            >
                {/* Logo */}
                <div className="flex h-16 items-center justify-between border-b border-border px-4">
                    {!sidebarCollapsed && (
                        <Link href="/app" className="flex items-center gap-2">
                            <div className="h-8 w-8 rounded-lg bg-gradient-blurple flex items-center justify-center">
                                <span className="text-white font-bold text-sm">Li</span>
                            </div>
                            <span className="font-semibold text-foreground">Lithium</span>
                        </Link>
                    )}
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={toggleSidebar}
                        className="h-8 w-8"
                    >
                        {sidebarCollapsed ? (
                            <ChevronRight className="h-4 w-4" />
                        ) : (
                            <ChevronLeft className="h-4 w-4" />
                        )}
                    </Button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 space-y-1 p-3 overflow-y-auto">
                    {/* Back to Guilds */}
                    <NavLink
                        item={{ label: 'Sunucu Listesi', href: '/app', icon: Home }}
                        isActive={false}
                        collapsed={sidebarCollapsed}
                    />

                    <div className="my-3 h-px bg-border" />

                    {navItems.map((item) => {
                        const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
                        return (
                            <NavLink
                                key={item.href}
                                item={item}
                                isActive={isActive}
                                collapsed={sidebarCollapsed}
                            />
                        );
                    })}
                </nav>

                {/* Footer */}
                <div className="border-t border-border p-3">
                    {!sidebarCollapsed && (
                        <div className="text-xs text-muted-foreground text-center">
                            Lithium Control Center v1.0
                        </div>
                    )}
                </div>
            </aside>
        </TooltipProvider>
    );
}

interface NavLinkProps {
    item: NavItem;
    isActive: boolean;
    collapsed: boolean;
}

function NavLink({ item, isActive, collapsed }: NavLinkProps) {
    const content = (
        <Link
            href={item.href}
            className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                collapsed && 'justify-center px-2'
            )}
        >
            <item.icon className="h-5 w-5 flex-shrink-0" />
            {!collapsed && <span>{item.label}</span>}
        </Link>
    );

    if (collapsed) {
        return (
            <Tooltip>
                <TooltipTrigger asChild>{content}</TooltipTrigger>
                <TooltipContent side="right">{item.label}</TooltipContent>
            </Tooltip>
        );
    }

    return content;
}
