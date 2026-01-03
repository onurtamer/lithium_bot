'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api, type GuildSettings as GuildSettingsType } from '@/lib/api';
import {
    Settings,
    Save,
    Loader2,
    Bell,
    MessageSquare,
    Globe,
    CheckCircle
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function SettingsPage() {
    const params = useParams();
    const guildId = params.guildId as string;
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [settings, setSettings] = useState<GuildSettingsType>({
        prefix: '!',
        language: 'tr',
        log_channel_id: '',
        welcome_enabled: false,
        welcome_channel_id: '',
        welcome_message: '',
        dm_on_warn: true,
        dm_on_mute: true,
        notify_on_join: true,
        notify_on_leave: true,
        notify_on_ban: true,
    });

    useEffect(() => {
        loadSettings();
    }, [guildId]);

    const loadSettings = async () => {
        setIsLoading(true);
        try {
            const response = await api.getSettings(guildId);
            if (response.ok) {
                setSettings(response.data);
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        setSaveSuccess(false);
        try {
            const response = await api.updateSettings(guildId, settings);
            if (response.ok) {
                setSaveSuccess(true);
                setTimeout(() => setSaveSuccess(false), 3000);
            }
        } catch (error) {
            console.error('Failed to save settings:', error);
        } finally {
            setIsSaving(false);
        }
    };

    const updateSetting = <K extends keyof GuildSettingsType>(key: K, value: GuildSettingsType[K]) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-20">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Settings className="h-6 w-6" />
                        Ayarlar
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Sunucu yapılandırmasını yönetin
                    </p>
                </div>
                <Button onClick={handleSave} disabled={isSaving}>
                    {isSaving ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : saveSuccess ? (
                        <CheckCircle className="h-4 w-4 mr-2 text-success" />
                    ) : (
                        <Save className="h-4 w-4 mr-2" />
                    )}
                    {saveSuccess ? 'Kaydedildi!' : 'Kaydet'}
                </Button>
            </div>

            <Tabs defaultValue="general">
                <TabsList>
                    <TabsTrigger value="general">
                        <Settings className="h-4 w-4 mr-2" />
                        Genel
                    </TabsTrigger>
                    <TabsTrigger value="notifications">
                        <Bell className="h-4 w-4 mr-2" />
                        Bildirimler
                    </TabsTrigger>
                    <TabsTrigger value="welcome">
                        <MessageSquare className="h-4 w-4 mr-2" />
                        Hoş Geldin
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="general" className="mt-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Genel Ayarlar</CardTitle>
                            <CardDescription>Temel bot yapılandırması</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="grid gap-4 md:grid-cols-2">
                                <div className="space-y-2">
                                    <Label htmlFor="prefix">Bot Prefix</Label>
                                    <Input
                                        id="prefix"
                                        value={settings.prefix}
                                        onChange={(e) => updateSetting('prefix', e.target.value)}
                                        placeholder="!"
                                    />
                                    <p className="text-xs text-muted-foreground">
                                        Komutlar için kullanılacak önek (ör: !help)
                                    </p>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="language">Dil</Label>
                                    <Input
                                        id="language"
                                        value={settings.language}
                                        onChange={(e) => updateSetting('language', e.target.value)}
                                        placeholder="tr"
                                    />
                                    <p className="text-xs text-muted-foreground">
                                        Bot mesajları için dil kodu (tr, en)
                                    </p>
                                </div>

                                <div className="space-y-2 md:col-span-2">
                                    <Label htmlFor="log_channel">Log Kanalı ID</Label>
                                    <Input
                                        id="log_channel"
                                        value={settings.log_channel_id || ''}
                                        onChange={(e) => updateSetting('log_channel_id', e.target.value)}
                                        placeholder="Kanal ID girin"
                                    />
                                    <p className="text-xs text-muted-foreground">
                                        Bot loglarının gönderileceği kanal
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="notifications" className="mt-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Bildirim Ayarları</CardTitle>
                            <CardDescription>DM ve sunucu bildirimleri</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <Label>Uyarıda DM Gönder</Label>
                                        <p className="text-xs text-muted-foreground">
                                            Kullanıcı uyarıldığında DM ile bilgilendir
                                        </p>
                                    </div>
                                    <Switch
                                        checked={settings.dm_on_warn}
                                        onCheckedChange={(v) => updateSetting('dm_on_warn', v)}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div>
                                        <Label>Susturmada DM Gönder</Label>
                                        <p className="text-xs text-muted-foreground">
                                            Kullanıcı susturulduğunda DM ile bilgilendir
                                        </p>
                                    </div>
                                    <Switch
                                        checked={settings.dm_on_mute}
                                        onCheckedChange={(v) => updateSetting('dm_on_mute', v)}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div>
                                        <Label>Katılma Bildirimi</Label>
                                        <p className="text-xs text-muted-foreground">
                                            Yeni üye katıldığında log kanalına bildir
                                        </p>
                                    </div>
                                    <Switch
                                        checked={settings.notify_on_join}
                                        onCheckedChange={(v) => updateSetting('notify_on_join', v)}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div>
                                        <Label>Ayrılma Bildirimi</Label>
                                        <p className="text-xs text-muted-foreground">
                                            Üye ayrıldığında log kanalına bildir
                                        </p>
                                    </div>
                                    <Switch
                                        checked={settings.notify_on_leave}
                                        onCheckedChange={(v) => updateSetting('notify_on_leave', v)}
                                    />
                                </div>

                                <div className="flex items-center justify-between">
                                    <div>
                                        <Label>Yasak Bildirimi</Label>
                                        <p className="text-xs text-muted-foreground">
                                            Kullanıcı yasaklandığında log kanalına bildir
                                        </p>
                                    </div>
                                    <Switch
                                        checked={settings.notify_on_ban}
                                        onCheckedChange={(v) => updateSetting('notify_on_ban', v)}
                                    />
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="welcome" className="mt-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Hoş Geldin Ayarları</CardTitle>
                            <CardDescription>Yeni üye karşılama mesajları</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <Label>Hoş Geldin Mesajı Aktif</Label>
                                    <p className="text-xs text-muted-foreground">
                                        Yeni üyelere hoş geldin mesajı gönder
                                    </p>
                                </div>
                                <Switch
                                    checked={settings.welcome_enabled}
                                    onCheckedChange={(v) => updateSetting('welcome_enabled', v)}
                                />
                            </div>

                            {settings.welcome_enabled && (
                                <div className="space-y-4 pl-4 border-l-2 border-primary/20">
                                    <div className="space-y-2">
                                        <Label htmlFor="welcome_channel">Hoş Geldin Kanalı ID</Label>
                                        <Input
                                            id="welcome_channel"
                                            value={settings.welcome_channel_id || ''}
                                            onChange={(e) => updateSetting('welcome_channel_id', e.target.value)}
                                            placeholder="Kanal ID girin"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="welcome_message">Hoş Geldin Mesajı</Label>
                                        <Input
                                            id="welcome_message"
                                            value={settings.welcome_message || ''}
                                            onChange={(e) => updateSetting('welcome_message', e.target.value)}
                                            placeholder="Hoş geldin {user}! 🎉"
                                        />
                                        <p className="text-xs text-muted-foreground">
                                            Değişkenler: {'{user}'} = kullanıcı adı, {'{server}'} = sunucu adı
                                        </p>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
