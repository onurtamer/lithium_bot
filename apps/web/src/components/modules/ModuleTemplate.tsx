'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { cn, formatRelativeTime } from '@/lib/utils';
import { useModuleStore, useNotificationStore } from '@/lib/store';
import { api, type ModuleConfig } from '@/lib/api';
import {
    Info,
    Settings,
    Hash,
    Eye,
    Activity,
    History,
    Save,
    RotateCcw,
    AlertTriangle,
    CheckCircle2
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

interface ModuleTemplateProps {
    guildId: string;
    moduleKey: string;
    moduleName: string;
    moduleDescription: string;
    moduleRisk?: 'low' | 'medium' | 'high';
    children: {
        settings: React.ReactNode;
        channels?: React.ReactNode;
        preview?: React.ReactNode;
    };
}

export function ModuleTemplate({
    guildId,
    moduleKey,
    moduleName,
    moduleDescription,
    moduleRisk = 'low',
    children,
}: ModuleTemplateProps) {
    const router = useRouter();
    const { setUnsavedChanges, hasUnsavedChanges } = useModuleStore();
    const { addNotification } = useNotificationStore();

    const [config, setConfig] = useState<ModuleConfig | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [activeTab, setActiveTab] = useState('overview');

    useEffect(() => {
        loadConfig();
    }, [guildId, moduleKey]);

    const loadConfig = async () => {
        try {
            setIsLoading(true);
            const data = await api.getModuleConfig(guildId, moduleKey);
            setConfig(data);
        } catch (error) {
            console.error('Failed to load config:', error);
            addNotification({
                type: 'error',
                title: 'Hata',
                message: 'Modül ayarları yüklenemedi',
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSave = async (publish = true) => {
        if (!config) return;

        try {
            setIsSaving(true);
            await api.updateModuleConfig(guildId, moduleKey, {
                enabled: config.enabled,
                config: config.config,
                publish,
            });

            setUnsavedChanges(false);
            addNotification({
                type: 'success',
                title: publish ? 'Kaydedildi ve Yayınlandı' : 'Taslak Kaydedildi',
                message: 'Ayarlarınız başarıyla güncellendi',
            });

            if (publish) {
                await loadConfig(); // Reload to get new version
            }
        } catch (error) {
            console.error('Failed to save config:', error);
            addNotification({
                type: 'error',
                title: 'Kaydetme Hatası',
                message: 'Ayarlar kaydedilemedi',
            });
        } finally {
            setIsSaving(false);
        }
    };

    const handleToggle = (enabled: boolean) => {
        if (!config) return;
        setConfig({ ...config, enabled });
        setUnsavedChanges(true);
    };

    const getRiskInfo = () => {
        switch (moduleRisk) {
            case 'high':
                return {
                    color: 'text-destructive',
                    bgColor: 'bg-destructive/10',
                    label: 'Yüksek Etki',
                    description: 'Bu modül kullanıcıları susturabilir, atabilir veya yasaklayabilir.',
                };
            case 'medium':
                return {
                    color: 'text-warning',
                    bgColor: 'bg-warning/10',
                    label: 'Orta Etki',
                    description: 'Bu modül mesaj silebilir veya kullanıcı rollerini değiştirebilir.',
                };
            default:
                return {
                    color: 'text-success',
                    bgColor: 'bg-success/10',
                    label: 'Düşük Etki',
                    description: 'Bu modül sadece bilgi toplar ve görüntüler.',
                };
        }
    };

    const riskInfo = getRiskInfo();

    if (isLoading) {
        return (
            <div className="space-y-4 animate-pulse">
                <div className="h-8 bg-muted rounded w-1/3" />
                <div className="h-4 bg-muted rounded w-2/3" />
                <div className="h-64 bg-muted rounded" />
            </div>
        );
    }

    if (!config) {
        return (
            <div className="text-center py-12">
                <AlertTriangle className="h-12 w-12 mx-auto text-warning mb-4" />
                <h2 className="text-lg font-semibold">Modül yüklenemedi</h2>
                <p className="text-muted-foreground">Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-2xl font-bold">{moduleName}</h1>
                        <Switch
                            checked={config.enabled}
                            onCheckedChange={handleToggle}
                        />
                        <Badge
                            variant={config.enabled ? 'default' : 'secondary'}
                            className={config.enabled ? 'bg-success' : ''}
                        >
                            {config.enabled ? 'Aktif' : 'Devre Dışı'}
                        </Badge>
                    </div>
                    <p className="text-muted-foreground mt-1">{moduleDescription}</p>
                </div>

                <div className="flex items-center gap-2">
                    {hasUnsavedChanges && (
                        <Badge variant="outline" className="border-warning text-warning">
                            Kaydedilmemiş değişiklikler
                        </Badge>
                    )}
                    <Button
                        variant="outline"
                        onClick={() => handleSave(false)}
                        disabled={isSaving || !hasUnsavedChanges}
                    >
                        Taslak Kaydet
                    </Button>
                    <Button
                        onClick={() => handleSave(true)}
                        disabled={isSaving}
                        className="gap-2"
                    >
                        <Save className="h-4 w-4" />
                        {isSaving ? 'Kaydediliyor...' : 'Kaydet ve Yayınla'}
                    </Button>
                </div>
            </div>

            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList>
                    <TabsTrigger value="overview" className="gap-2">
                        <Info className="h-4 w-4" />
                        Genel Bakış
                    </TabsTrigger>
                    <TabsTrigger value="settings" className="gap-2">
                        <Settings className="h-4 w-4" />
                        Ayarlar
                    </TabsTrigger>
                    {children.channels && (
                        <TabsTrigger value="channels" className="gap-2">
                            <Hash className="h-4 w-4" />
                            Kanal/Roller
                        </TabsTrigger>
                    )}
                    {children.preview && (
                        <TabsTrigger value="preview" className="gap-2">
                            <Eye className="h-4 w-4" />
                            Önizleme
                        </TabsTrigger>
                    )}
                    <TabsTrigger value="events" className="gap-2">
                        <Activity className="h-4 w-4" />
                        Son Olaylar
                    </TabsTrigger>
                    <TabsTrigger value="history" className="gap-2">
                        <History className="h-4 w-4" />
                        Geçmiş
                    </TabsTrigger>
                </TabsList>

                {/* Overview Tab */}
                <TabsContent value="overview" className="space-y-4 mt-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Status Card */}
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium">Durum</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="flex items-center gap-2">
                                    {config.enabled ? (
                                        <CheckCircle2 className="h-5 w-5 text-success" />
                                    ) : (
                                        <AlertTriangle className="h-5 w-5 text-muted-foreground" />
                                    )}
                                    <span className="font-medium">
                                        {config.enabled ? 'Aktif' : 'Devre Dışı'}
                                    </span>
                                </div>
                                <p className="text-sm text-muted-foreground mt-2">
                                    Versiyon: {config.version}
                                </p>
                            </CardContent>
                        </Card>

                        {/* Risk Level Card */}
                        <Card className={cn(riskInfo.bgColor)}>
                            <CardHeader className="pb-2">
                                <CardTitle className={cn('text-sm font-medium', riskInfo.color)}>
                                    Etki Seviyesi
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className={cn('font-medium', riskInfo.color)}>
                                    {riskInfo.label}
                                </span>
                                <p className="text-sm text-muted-foreground mt-2">
                                    {riskInfo.description}
                                </p>
                            </CardContent>
                        </Card>

                        {/* Last Updated Card */}
                        <Card>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium">Son Güncelleme</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <span className="font-medium">
                                    {formatRelativeTime(config.last_updated)}
                                </span>
                                {config.updated_by && (
                                    <p className="text-sm text-muted-foreground mt-2">
                                        Tarafından: {config.updated_by.username}
                                    </p>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    {/* Quick Settings */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Hızlı Ayarlar</CardTitle>
                            <CardDescription>
                                En sık kullanılan ayarlara buradan erişebilirsiniz.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <p className="text-muted-foreground text-sm">
                                Detaylı ayarlar için "Ayarlar" sekmesine gidin.
                            </p>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* Settings Tab */}
                <TabsContent value="settings" className="mt-6">
                    {children.settings}
                </TabsContent>

                {/* Channels Tab */}
                {children.channels && (
                    <TabsContent value="channels" className="mt-6">
                        {children.channels}
                    </TabsContent>
                )}

                {/* Preview Tab */}
                {children.preview && (
                    <TabsContent value="preview" className="mt-6">
                        {children.preview}
                    </TabsContent>
                )}

                {/* Events Tab */}
                <TabsContent value="events" className="mt-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Son Olaylar</CardTitle>
                            <CardDescription>
                                Bu modül tarafından tetiklenen son olaylar
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="text-center py-8 text-muted-foreground">
                                <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                <p>Henüz olay kaydı yok</p>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* History Tab */}
                <TabsContent value="history" className="mt-6">
                    <Card>
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <div>
                                    <CardTitle>Konfigürasyon Geçmişi</CardTitle>
                                    <CardDescription>
                                        Önceki versiyonlara geri dönebilirsiniz
                                    </CardDescription>
                                </div>
                                <Button variant="outline" size="sm" className="gap-2">
                                    <RotateCcw className="h-4 w-4" />
                                    Geri Al
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                                    <div>
                                        <p className="font-medium">Versiyon {config.version}</p>
                                        <p className="text-sm text-muted-foreground">
                                            {formatRelativeTime(config.last_updated)} • {config.updated_by?.username || 'Sistem'}
                                        </p>
                                    </div>
                                    <Badge>Aktif</Badge>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
