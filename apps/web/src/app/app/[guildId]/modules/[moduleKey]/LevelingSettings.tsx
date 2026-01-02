'use client';

import { useState } from 'react';
import { useModuleStore } from '@/lib/store';
import type { LevelingConfig } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { TrendingUp, Gift, Palette, Plus, Trash2 } from 'lucide-react';

interface LevelingSettingsProps {
    guildId: string;
}

export function LevelingSettings({ guildId }: LevelingSettingsProps) {
    const { setUnsavedChanges } = useModuleStore();

    const [config, setConfig] = useState<LevelingConfig>({
        enabled: true,
        xpPerMessage: { min: 15, max: 25 },
        xpCooldown: 60,
        levelUpChannel: '',
        levelUpMessage: '🎉 Tebrikler {user}! **Seviye {level}** oldun!',
        rewards: [
            { level: 5, roleId: '', removeOnLevelUp: false },
            { level: 10, roleId: '', removeOnLevelUp: true },
        ],
        roleMultipliers: [],
        ignoredChannels: [],
        ignoredRoles: [],
        rankCard: {
            backgroundColor: '#1a1a24',
            accentColor: '#5865F2',
            showAvatar: true,
        },
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

    const addReward = () => {
        const newReward = { level: 1, roleId: '', removeOnLevelUp: false };
        handleChange('rewards', [...config.rewards, newReward]);
    };

    const removeReward = (index: number) => {
        handleChange('rewards', config.rewards.filter((_, i) => i !== index));
    };

    const updateReward = (index: number, field: string, value: unknown) => {
        const updated = [...config.rewards];
        (updated[index] as Record<string, unknown>)[field] = value;
        handleChange('rewards', updated);
    };

    return (
        <div className="space-y-6">
            {/* XP Ayarları */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-green-500/10">
                            <TrendingUp className="h-5 w-5 text-green-400" />
                        </div>
                        <div>
                            <CardTitle className="text-base">XP Ayarları</CardTitle>
                            <CardDescription>Mesaj başına kazanılan XP ve cooldown</CardDescription>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="space-y-2">
                            <Label>Minimum XP</Label>
                            <Input
                                type="number"
                                min="1"
                                value={config.xpPerMessage.min}
                                onChange={(e) => handleChange('xpPerMessage.min', parseInt(e.target.value))}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Maksimum XP</Label>
                            <Input
                                type="number"
                                min="1"
                                value={config.xpPerMessage.max}
                                onChange={(e) => handleChange('xpPerMessage.max', parseInt(e.target.value))}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label>Cooldown (saniye)</Label>
                            <Input
                                type="number"
                                min="0"
                                value={config.xpCooldown}
                                onChange={(e) => handleChange('xpCooldown', parseInt(e.target.value))}
                            />
                        </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                        Her mesaj için {config.xpPerMessage.min}-{config.xpPerMessage.max} arası rastgele XP kazanılır.
                        {config.xpCooldown > 0 ? ` ${config.xpCooldown} saniye cooldown.` : ' Cooldown yok.'}
                    </p>
                </CardContent>
            </Card>

            {/* Level Up Mesajı */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-base">Level Up Bildirimi</CardTitle>
                    <CardDescription>Seviye atlama mesajını özelleştirin</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label>Bildirim Kanalı ID (Boş = Aynı Kanal)</Label>
                        <Input
                            value={config.levelUpChannel || ''}
                            onChange={(e) => handleChange('levelUpChannel', e.target.value)}
                            placeholder="Kanal ID'si girin veya boş bırakın"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label>Mesaj Şablonu</Label>
                        <Textarea
                            value={config.levelUpMessage}
                            onChange={(e) => handleChange('levelUpMessage', e.target.value)}
                            rows={2}
                            className="font-mono text-sm"
                        />
                        <p className="text-xs text-muted-foreground">
                            Değişkenler: {'{user}'}, {'{level}'}, {'{xp}'}
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* Rol Ödülleri */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-purple-500/10">
                                <Gift className="h-5 w-5 text-purple-400" />
                            </div>
                            <div>
                                <CardTitle className="text-base">Seviye Ödülleri</CardTitle>
                                <CardDescription>Belirli seviyelerde otomatik rol ver</CardDescription>
                            </div>
                        </div>
                        <Button onClick={addReward} size="sm" variant="outline" className="gap-2">
                            <Plus className="h-4 w-4" />
                            Ekle
                        </Button>
                    </div>
                </CardHeader>
                <CardContent>
                    {config.rewards.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-4">
                            Henüz ödül eklenmemiş. "Ekle" butonuna tıklayarak başlayın.
                        </p>
                    ) : (
                        <div className="space-y-3">
                            {config.rewards.map((reward, index) => (
                                <div
                                    key={index}
                                    className="flex items-center gap-3 p-3 rounded-lg bg-muted/50"
                                >
                                    <div className="flex-1 grid grid-cols-3 gap-3">
                                        <div className="space-y-1">
                                            <Label className="text-xs">Seviye</Label>
                                            <Input
                                                type="number"
                                                min="1"
                                                value={reward.level}
                                                onChange={(e) => updateReward(index, 'level', parseInt(e.target.value))}
                                                className="h-9"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <Label className="text-xs">Rol ID</Label>
                                            <Input
                                                value={reward.roleId}
                                                onChange={(e) => updateReward(index, 'roleId', e.target.value)}
                                                placeholder="Rol ID"
                                                className="h-9"
                                            />
                                        </div>
                                        <div className="flex items-end gap-2">
                                            <div className="flex items-center gap-2">
                                                <Switch
                                                    checked={reward.removeOnLevelUp}
                                                    onCheckedChange={(checked) => updateReward(index, 'removeOnLevelUp', checked)}
                                                />
                                                <Label className="text-xs">Sonraki seviyede kaldır</Label>
                                            </div>
                                        </div>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => removeReward(index)}
                                        className="h-9 w-9 text-destructive hover:text-destructive"
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Rank Card Özelleştirme */}
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-blue-500/10">
                            <Palette className="h-5 w-5 text-blue-400" />
                        </div>
                        <div>
                            <CardTitle className="text-base">Rank Kartı Özelleştirme</CardTitle>
                            <CardDescription>/rank komutu için kart görünümü</CardDescription>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Arkaplan Rengi</Label>
                            <div className="flex gap-2">
                                <Input
                                    type="color"
                                    value={config.rankCard.backgroundColor}
                                    onChange={(e) => handleChange('rankCard.backgroundColor', e.target.value)}
                                    className="w-12 h-10 p-1 cursor-pointer"
                                />
                                <Input
                                    value={config.rankCard.backgroundColor}
                                    onChange={(e) => handleChange('rankCard.backgroundColor', e.target.value)}
                                    className="flex-1"
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>Vurgu Rengi</Label>
                            <div className="flex gap-2">
                                <Input
                                    type="color"
                                    value={config.rankCard.accentColor}
                                    onChange={(e) => handleChange('rankCard.accentColor', e.target.value)}
                                    className="w-12 h-10 p-1 cursor-pointer"
                                />
                                <Input
                                    value={config.rankCard.accentColor}
                                    onChange={(e) => handleChange('rankCard.accentColor', e.target.value)}
                                    className="flex-1"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center justify-between">
                        <div>
                            <Label>Avatar Göster</Label>
                            <p className="text-xs text-muted-foreground">
                                Rank kartında kullanıcı avatarını göster
                            </p>
                        </div>
                        <Switch
                            checked={config.rankCard.showAvatar}
                            onCheckedChange={(checked) => handleChange('rankCard.showAvatar', checked)}
                        />
                    </div>

                    {/* Preview */}
                    <Separator />
                    <div className="space-y-2">
                        <Label>Önizleme</Label>
                        <div
                            className="rounded-lg p-4 flex items-center gap-4"
                            style={{ backgroundColor: config.rankCard.backgroundColor }}
                        >
                            {config.rankCard.showAvatar && (
                                <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center">
                                    <span className="text-2xl">👤</span>
                                </div>
                            )}
                            <div className="flex-1">
                                <div className="text-white font-semibold">Kullanıcı Adı</div>
                                <div className="text-gray-400 text-sm">Seviye 15 • #3</div>
                                <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
                                    <div
                                        className="h-full rounded-full"
                                        style={{
                                            width: '65%',
                                            backgroundColor: config.rankCard.accentColor
                                        }}
                                    />
                                </div>
                                <div className="text-gray-400 text-xs mt-1">1,250 / 2,000 XP</div>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
