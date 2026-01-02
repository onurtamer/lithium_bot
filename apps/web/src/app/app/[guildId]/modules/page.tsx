'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useModuleStore, useNotificationStore } from '@/lib/store';
import { api } from '@/lib/api';
import { MODULE_CATEGORIES } from '@/lib/utils';
import { ModuleGrid } from '@/components/modules';
import {
    Search,
    Filter,
    Grid3X3,
    List
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';

export default function ModulesPage() {
    const params = useParams();
    const guildId = params.guildId as string;
    const { modules, toggleModule, setUnsavedChanges } = useModuleStore();
    const { addNotification } = useNotificationStore();

    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<string>('all');
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

    const handleToggle = async (moduleKey: string, enabled: boolean) => {
        try {
            // Optimistic update
            toggleModule(moduleKey, enabled);

            // API call
            await api.updateModuleConfig(guildId, moduleKey, {
                enabled,
                publish: true,
            });

            addNotification({
                type: 'success',
                title: enabled ? 'Modül Aktif' : 'Modül Devre Dışı',
                message: `${moduleKey} başarıyla ${enabled ? 'aktifleştirildi' : 'devre dışı bırakıldı'}.`,
            });

            setUnsavedChanges(false);
        } catch (error) {
            // Revert on error
            toggleModule(moduleKey, !enabled);
            addNotification({
                type: 'error',
                title: 'Hata',
                message: 'Modül durumu güncellenemedi.',
            });
        }
    };

    // Filter modules
    const filteredModules = modules.filter((module) => {
        const matchesSearch = module.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            module.description.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesCategory = selectedCategory === 'all' || module.category === selectedCategory;
        return matchesSearch && matchesCategory;
    });

    const enabledCount = modules.filter(m => m.enabled).length;

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold">Modüller</h1>
                    <p className="text-muted-foreground mt-1">
                        Bot özelliklerini yönetin ve yapılandırın.{' '}
                        <Badge variant="outline" className="ml-2">
                            {enabledCount}/{modules.length} aktif
                        </Badge>
                    </p>
                </div>
            </div>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-4">
                {/* Search */}
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Modül ara..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-9 bg-muted/50"
                    />
                </div>

                {/* Category Tabs */}
                <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
                    <TabsList>
                        <TabsTrigger value="all">Tümü</TabsTrigger>
                        {Object.entries(MODULE_CATEGORIES).map(([key, category]) => (
                            <TabsTrigger key={key} value={key}>
                                {category.label}
                            </TabsTrigger>
                        ))}
                    </TabsList>
                </Tabs>

                {/* View Mode Toggle */}
                <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
                    <Button
                        variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => setViewMode('grid')}
                    >
                        <Grid3X3 className="h-4 w-4" />
                    </Button>
                    <Button
                        variant={viewMode === 'list' ? 'secondary' : 'ghost'}
                        size="icon"
                        className="h-8 w-8"
                        onClick={() => setViewMode('list')}
                    >
                        <List className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* Modules Grid */}
            <ModuleGrid
                modules={filteredModules}
                guildId={guildId}
                onToggle={handleToggle}
                category={selectedCategory === 'all' ? undefined : selectedCategory}
            />

            {/* Empty State */}
            {filteredModules.length === 0 && (
                <div className="text-center py-12">
                    <Filter className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                    <h3 className="text-lg font-semibold mb-2">Modül Bulunamadı</h3>
                    <p className="text-muted-foreground">
                        Arama veya filtre kriterlerinize uygun modül bulunamadı.
                    </p>
                </div>
            )}
        </div>
    );
}
