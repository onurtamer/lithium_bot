'use client';

import { useState } from 'react';
import { useModuleStore } from '@/lib/store';
import type { JailConfig } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { Lock, AlertTriangle, MessageSquare } from 'lucide-react';

interface JailSettingsProps {
    guildId: string;
}

export function JailSettings({ guildId }: JailSettingsProps) {
    const { setUnsavedChanges } = useModuleStore();

    const [config, setConfig] = useState<JailConfig>({
        enabled: true,
        jailRoleId: '',
        jailChannelId: '',
        logChannelId: '',
        autoJail: {
            onRaidDetection: true,
            onSpamThreshold: 5,
            onWarningThreshold: 3,
        },
        jailMessage: '⛓️ **{user}** hapse atıldı!\n\n**Sebep:** {reason}\n**Süre:** {duration}\n**Moderatör:** {moderator}',
        releaseMessage: '🔓 **{user}** hapisten serbest bırakıldı!',
    });

    const handleChange = (path: string, value: unknown) => {
        const keys = path.split('.');
        const updated = { ...config };
        let current: Record<string, unknown> = updated;

        for (let i = 0; i < keys.length - 1; i++) {
            current = current[keys[i]] as Record<string, unknown>;
        }
        current[keys[keys.length - 1]] = value;

        setConfig(updated);
        setUnsavedChanges(true);
    };

    return (
        <div className="space-y-6">
            {/* Warning Banner */}
            <div className="flex items-start gap-3 p-4 rounded-lg bg-destructive/10 border border-destructive/20">
                <AlertTriangle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                <div>
                    <p className="font-medium text-destructive">Yüksek Etkili Modül</p>
                    <p className="text-sm text-muted-foreground mt-1">
                        Bu modül kullanıcıların tüm rollerini alıp hapiste tutabilir.
                        Ayarları dikkatli yapılandırın ve test edin.
                    </p>
                </div>
            </div>

            {/* Temel Ayarlar */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-orange-500/10">
                            <Lock className="h-5 w-5 text-orange-400" />
                        </div>
                        <div>
                            <CardTitle className="text-base">Temel Ayarlar</CardTitle>
                            <CardDescription>Jail sistemi için gerekli kanal ve rol ayarları</CardDescription>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Jail Rolü ID</Label>
                            <Input
                                value={config.jailRoleId}
                                onChange={(e) => handleChange('jailRoleId', e.target.value)}
                                placeholder="Rol ID'si girin"
                            />
                            <p className="text-xs text-muted-foreground">
                                Hapise atılan kullanıcılara verilecek rol
                            </p>
                        </div>
                        <div className="space-y-2">
                            <Label>Jail Kanalı ID</Label>
                            <Input
                                value={config.jailChannelId}
                                onChange={(e) => handleChange('jailChannelId', e.target.value)}
                                placeholder="Kanal ID'si girin"
                            />
                            <p className="text-xs text-muted-foreground">
                                Hapisteki kullanıcıların görebileceği tek kanal
                            </p>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label>Log Kanalı ID (Opsiyonel)</Label>
                        <Input
                            value={config.logChannelId || ''}
                            onChange={(e) => handleChange('logChannelId', e.target.value)}
                            placeholder="Kanal ID'si girin"
                        />
                        <p className="text-xs text-muted-foreground">
                            Jail işlemlerinin loglanacağı kanal
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* Otomatik Jail */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-red-500/10">
                            <AlertTriangle className="h-5 w-5 text-red-400" />
                        </div>
                        <div>
                            <CardTitle className="text-base">Otomatik Jail Tetikleyicileri</CardTitle>
                            <CardDescription>Hangi durumlarda otomatik jail uygulansın</CardDescription>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <Label>Raid Algılandığında</Label>
                            <p className="text-xs text-muted-foreground">
                                Anti-Raid modülü raid algıladığında şüpheli kullanıcıları otomatik jail'e at
                            </p>
                        </div>
                        <Switch
                            checked={config.autoJail.onRaidDetection}
                            onCheckedChange={(checked) => handleChange('autoJail.onRaidDetection', checked)}
                        />
                    </div>

                    <Separator />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Spam İhlali Eşiği</Label>
                            <Input
                                type="number"
                                min="0"
                                value={config.autoJail.onSpamThreshold}
                                onChange={(e) => handleChange('autoJail.onSpamThreshold', parseInt(e.target.value))}
                            />
                            <p className="text-xs text-muted-foreground">
                                Bu kadar spam ihlali sonrası jail (0 = devre dışı)
                            </p>
                        </div>
                        <div className="space-y-2">
                            <Label>Uyarı Eşiği</Label>
                            <Input
                                type="number"
                                min="0"
                                value={config.autoJail.onWarningThreshold}
                                onChange={(e) => handleChange('autoJail.onWarningThreshold', parseInt(e.target.value))}
                            />
                            <p className="text-xs text-muted-foreground">
                                Bu kadar uyarı sonrası jail (0 = devre dışı)
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Mesaj Şablonları */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-blue-500/10">
                            <MessageSquare className="h-5 w-5 text-blue-400" />
                        </div>
                        <div>
                            <CardTitle className="text-base">Mesaj Şablonları</CardTitle>
                            <CardDescription>Jail ve serbest bırakma mesajlarını özelleştirin</CardDescription>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label>Jail Mesajı</Label>
                        <Textarea
                            value={config.jailMessage}
                            onChange={(e) => handleChange('jailMessage', e.target.value)}
                            rows={4}
                            className="font-mono text-sm"
                        />
                        <p className="text-xs text-muted-foreground">
                            Değişkenler: {'{user}'}, {'{reason}'}, {'{duration}'}, {'{moderator}'}
                        </p>
                    </div>

                    <div className="space-y-2">
                        <Label>Serbest Bırakma Mesajı</Label>
                        <Textarea
                            value={config.releaseMessage}
                            onChange={(e) => handleChange('releaseMessage', e.target.value)}
                            rows={2}
                            className="font-mono text-sm"
                        />
                        <p className="text-xs text-muted-foreground">
                            Değişkenler: {'{user}'}
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
