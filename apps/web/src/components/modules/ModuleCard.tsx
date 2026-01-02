'use client';

import Link from 'next/link';
import { cn, MODULES, MODULE_CATEGORIES, type ModuleKey } from '@/lib/utils';
import type { ModuleStatus } from '@/lib/api';
import {
    FileText, Shield, Lock, VolumeX, ShieldAlert,
    Ticket, TrendingUp, Coins, Star, Smile,
    Gift, Cake, MessageSquarePlus, Gamepad2, Wrench,
    MoreVertical, ExternalLink
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

// Icon mapping
const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
    FileText,
    Shield,
    Lock,
    VolumeX,
    ShieldAlert,
    Ticket,
    TrendingUp,
    Coins,
    Star,
    Smile,
    Gift,
    Cake,
    MessageSquarePlus,
    Gamepad2,
    Wrench,
};

interface ModuleCardProps {
    module: ModuleStatus;
    guildId: string;
    onToggle?: (moduleKey: string, enabled: boolean) => void;
}

export function ModuleCard({ module, guildId, onToggle }: ModuleCardProps) {
    const moduleInfo = MODULES[module.module_key as ModuleKey];
    const category = moduleInfo ? MODULE_CATEGORIES[moduleInfo.category as keyof typeof MODULE_CATEGORIES] : null;
    const IconComponent = iconMap[module.icon] || Shield;

    const getRiskBadge = () => {
        switch (module.risk_level) {
            case 'high':
                return <Badge variant="destructive" className="text-[10px]">Yüksek Risk</Badge>;
            case 'medium':
                return <Badge variant="outline" className="text-[10px] border-warning text-warning">Orta Risk</Badge>;
            default:
                return null;
        }
    };

    return (
        <Card
            className={cn(
                'module-card group relative',
                module.enabled ? 'enabled' : 'disabled'
            )}
        >
            {/* Status indicator */}
            <div className={cn(
                'absolute top-4 right-4 h-2 w-2 rounded-full',
                module.enabled ? 'bg-success' : 'bg-muted-foreground'
            )} />

            <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                        <div className={cn(
                            'flex h-10 w-10 items-center justify-center rounded-lg',
                            module.enabled
                                ? 'bg-primary/10 text-primary'
                                : 'bg-muted text-muted-foreground'
                        )}>
                            <IconComponent className="h-5 w-5" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-foreground">{module.display_name}</h3>
                            {category && (
                                <span className={cn('text-xs', category.color)}>
                                    {category.label}
                                </span>
                            )}
                        </div>
                    </div>

                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity">
                                <MoreVertical className="h-4 w-4" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuItem asChild>
                                <Link href={`/app/${guildId}/modules/${module.module_key}`}>
                                    <ExternalLink className="mr-2 h-4 w-4" />
                                    Detayları Aç
                                </Link>
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </CardHeader>

            <CardContent>
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                    {module.description}
                </p>

                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        {getRiskBadge()}
                        {module.has_draft && (
                            <Badge variant="outline" className="text-[10px] border-info text-info">
                                Taslak
                            </Badge>
                        )}
                    </div>

                    <div className="flex items-center gap-3">
                        <Link
                            href={`/app/${guildId}/modules/${module.module_key}`}
                            className="text-xs text-primary hover:underline"
                        >
                            Ayarlar
                        </Link>
                        <Switch
                            checked={module.enabled}
                            onCheckedChange={(checked) => onToggle?.(module.module_key, checked)}
                        />
                    </div>
                </div>

                {module.last_updated && (
                    <p className="text-[10px] text-muted-foreground mt-3 pt-3 border-t border-border">
                        Son güncelleme: {new Date(module.last_updated).toLocaleDateString('tr-TR')}
                    </p>
                )}
            </CardContent>
        </Card>
    );
}

// Module Grid Component
interface ModuleGridProps {
    modules: ModuleStatus[];
    guildId: string;
    onToggle?: (moduleKey: string, enabled: boolean) => void;
    category?: string;
}

export function ModuleGrid({ modules, guildId, onToggle, category }: ModuleGridProps) {
    const filteredModules = category
        ? modules.filter(m => {
            const info = MODULES[m.module_key as ModuleKey];
            return info?.category === category;
        })
        : modules;

    if (filteredModules.length === 0) {
        return (
            <div className="text-center py-12 text-muted-foreground">
                Bu kategoride modül bulunamadı.
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredModules.map((module) => (
                <ModuleCard
                    key={module.module_key}
                    module={module}
                    guildId={guildId}
                    onToggle={onToggle}
                />
            ))}
        </div>
    );
}
