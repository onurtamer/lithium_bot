'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { useGuildStore } from '@/lib/store';
import {
    Settings,
    Globe,
    Bell,
    Shield,
    Save,
    Loader2,
    Hash,
    MessageSquare,
    Languages,
    Palette
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface GuildSettings {
    prefix: string;
    language: string;
    logChannel: string;
    welcomeChannel: string;
    welcomeEnabled: boolean;
    welcomeMessage: string;
    notifyOnJoin: boolean;
    notifyOnLeave: boolean;
    notifyOnBan: boolean;
    dmOnWarn: boolean;
    dmOnMute: boolean;
}

export default function SettingsPage() {
    const params = useParams();
    const guildId = params.guildId as string;
    const { currentGuild } = useGuildStore();
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [activeTab, setActiveTab] = useState('general');

    const [settings, setSettings] = useState<GuildSettings>({
        prefix: '!',
        language: 'tr',
        logChannel: '',
        welcomeChannel: '',
        welcomeEnabled: false,
        welcomeMessage: 'Hoş geldin {user}!',
        notifyOnJoin: true,
        notifyOnLeave: true,
        notifyOnBan: true,
        dmOnWarn: true,
        dmOnMute: true,
    });

    useEffect(() => {
        // Simulate loading settings from API
        setIsLoading(true);
        setTimeout(() => {
            setIsLoading(false);
        }, 500);
    }, [guildId]);

    const handleSave = async () => {
        setIsSaving(true);
        // Simulate API save
        await new Promise(resolve => setTimeout(resolve, 1000));
        setIsSaving(false);
    };

    const updateSetting = <K extends keyof GuildSettings>(key: K, value: GuildSettings[K]) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-24">
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
                        {currentGuild?.name || 'Sunucu'} ayarlarını yönetin
                    </p>
                </div>
                <Button onClick={handleSave} disabled={isSaving}>
                    {isSaving ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                        <Save className="h-4 w-4 mr-2" />
                    )}
                    Kaydet
                </Button>
            </div>

            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList>
                    <TabsTrigger value="general">
                        <Globe className="h-4 w-4 mr-2" />
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

                <TabsContent value="general" className="mt-4 space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Genel Ayarlar</CardTitle>
                            <CardDescription>Bot'un temel davranışlarını yapılandırın</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <Label htmlFor="prefix">Komut Prefixi</Label>
                                    <div className="relative">
                                        <Hash className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                        <Input
                                            id="prefix"
                                            value={settings.prefix}
                                            onChange={(e) => updateSetting('prefix', e.target.value)}
                                            className="pl-9"
                                            placeholder="!"
                                        />
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        Slash komutları her zaman çalışır
                                    </p>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="language">Bot Dili</Label>
                                    <div className="relative">
                                        <Languages className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                        <Input
                                            id="language"
                                            value={settings.language === 'tr' ? 'Türkçe' : 'English'}
                                            className="pl-9"
                                            readOnly
                                        />
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        Bot yanıtlarının dili
                                    </p>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="logChannel">Log Kanalı ID</Label>
                                <Input
                                    id="logChannel"
                                    value={settings.logChannel}
                                    onChange={(e) => updateSetting('logChannel', e.target.value)}
                                    placeholder="Kanal ID'si girin"
                                />
                                <p className="text-xs text-muted-foreground">
                                    Moderasyon loglarının gönderileceği kanal
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="notifications" className="mt-4 space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Bildirim Ayarları</CardTitle>
                            <CardDescription>Hangi olaylarda bildirim gönderilsin</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="flex items-center justify-between">
                                <div className="space-y-0.5">
                                    <Label>Üye Katılımı</Label>
                                    <p className="text-xs text-muted-foreground">Yeni üye katıldığında log kanalına mesaj gönder</p>
                                </div>
                                <Switch
                                    checked={settings.notifyOnJoin}
                                    onCheckedChange={(v) => updateSetting('notifyOnJoin', v)}
                                />
                            </div>

                            <div className="flex items-center justify-between">
                                <div className="space-y-0.5">
                                    <Label>Üye Ayrılışı</Label>
                                    <p className="text-xs text-muted-foreground">Üye ayrıldığında log kanalına mesaj gönder</p>
                                </div>
                                <Switch
                                    checked={settings.notifyOnLeave}
                                    onCheckedChange={(v) => updateSetting('notifyOnLeave', v)}
                                />
                            </div>

                            <div className="flex items-center justify-between">
                                <div className="space-y-0.5">
                                    <Label>Yasaklamalar</Label>
                                    <p className="text-xs text-muted-foreground">Banlarda log kanalına mesaj gönder</p>
                                </div>
                                <Switch
                                    checked={settings.notifyOnBan}
                                    onCheckedChange={(v) => updateSetting('notifyOnBan', v)}
                                />
                            </div>

                            <div className="flex items-center justify-between">
                                <div className="space-y-0.5">
                                    <Label>Uyarılarda DM</Label>
                                    <p className="text-xs text-muted-foreground">Uyarı verildiğinde kullanıcıya DM gönder</p>
                                </div>
                                <Switch
                                    checked={settings.dmOnWarn}
                                    onCheckedChange={(v) => updateSetting('dmOnWarn', v)}
                                />
                            </div>

                            <div className="flex items-center justify-between">
                                <div className="space-y-0.5">
                                    <Label>Susturmalarda DM</Label>
                                    <p className="text-xs text-muted-foreground">Susturulduğunda kullanıcıya DM gönder</p>
                                </div>
                                <Switch
                                    checked={settings.dmOnMute}
                                    onCheckedChange={(v) => updateSetting('dmOnMute', v)}
                                />
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="welcome" className="mt-4 space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Hoş Geldin Mesajı</CardTitle>
                            <CardDescription>Yeni üyelere gönderilecek karşılama mesajı</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="flex items-center justify-between">
                                <div className="space-y-0.5">
                                    <Label>Hoş Geldin Mesajı</Label>
                                    <p className="text-xs text-muted-foreground">Yeni üyelere mesaj gönder</p>
                                </div>
                                <Switch
                                    checked={settings.welcomeEnabled}
                                    onCheckedChange={(v) => updateSetting('welcomeEnabled', v)}
                                />
                            </div>

                            {settings.welcomeEnabled && (
                                <>
                                    <div className="space-y-2">
                                        <Label htmlFor="welcomeChannel">Hoş Geldin Kanalı ID</Label>
                                        <Input
                                            id="welcomeChannel"
                                            value={settings.welcomeChannel}
                                            onChange={(e) => updateSetting('welcomeChannel', e.target.value)}
                                            placeholder="Kanal ID'si girin"
                                        />
                                    </div>

                                    <div className="space-y-2">
                                        <Label htmlFor="welcomeMessage">Mesaj Şablonu</Label>
                                        <Input
                                            id="welcomeMessage"
                                            value={settings.welcomeMessage}
                                            onChange={(e) => updateSetting('welcomeMessage', e.target.value)}
                                            placeholder="Hoş geldin {user}!"
                                        />
                                        <p className="text-xs text-muted-foreground">
                                            Kullanılabilir değişkenler: {'{user}'}, {'{server}'}, {'{membercount}'}
                                        </p>
                                    </div>
                                </>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
