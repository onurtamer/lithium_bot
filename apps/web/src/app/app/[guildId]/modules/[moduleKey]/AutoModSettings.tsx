'use client';

import { useState } from 'react';
import { useModuleStore } from '@/lib/store';
import type { AutoModConfig } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    Shield,
    Link as LinkIcon,
    Type,
    MessageSquare,
    Plus,
    X
} from 'lucide-react';

interface AutoModSettingsProps {
    guildId: string;
}

export function AutoModSettings({ guildId }: AutoModSettingsProps) {
    const { setUnsavedChanges } = useModuleStore();

    // Local state for form
    const [config, setConfig] = useState<AutoModConfig>({
        enabled: true,
        profanity: {
            enabled: true,
            customWords: ['spam', 'reklam'],
            action: 'delete',
            muteDuration: 300,
        },
        links: {
            enabled: true,
            whitelist: ['discord.gg', 'youtube.com', 'twitter.com'],
            allowedRoles: [],
            allowedChannels: [],
            action: 'delete',
        },
        caps: {
            enabled: true,
            threshold: 70,
            minLength: 10,
            action: 'warn',
        },
        spam: {
            enabled: true,
            messageThreshold: 5,
            interval: 5,
            action: 'mute',
            muteDuration: 300,
        },
        exemptRoles: [],
        exemptChannels: [],
    });

    const [newWord, setNewWord] = useState('');
    const [newDomain, setNewDomain] = useState('');

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

    const addWord = () => {
        if (newWord.trim() && !config.profanity.customWords.includes(newWord.trim())) {
            handleChange('profanity.customWords', [...config.profanity.customWords, newWord.trim()]);
            setNewWord('');
        }
    };

    const removeWord = (word: string) => {
        handleChange('profanity.customWords', config.profanity.customWords.filter(w => w !== word));
    };

    const addDomain = () => {
        if (newDomain.trim() && !config.links.whitelist.includes(newDomain.trim())) {
            handleChange('links.whitelist', [...config.links.whitelist, newDomain.trim()]);
            setNewDomain('');
        }
    };

    const removeDomain = (domain: string) => {
        handleChange('links.whitelist', config.links.whitelist.filter(d => d !== domain));
    };

    return (
        <div className="space-y-6">
            {/* Profanity Filter */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-red-500/10">
                                <Shield className="h-5 w-5 text-red-400" />
                            </div>
                            <div>
                                <CardTitle className="text-base">Küfür & Argo Filtresi</CardTitle>
                                <CardDescription>Yasaklı kelimeleri otomatik tespit et ve işlem yap</CardDescription>
                            </div>
                        </div>
                        <Switch
                            checked={config.profanity.enabled}
                            onCheckedChange={(checked) => handleChange('profanity.enabled', checked)}
                        />
                    </div>
                </CardHeader>
                {config.profanity.enabled && (
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label>İşlem</Label>
                            <Select
                                value={config.profanity.action}
                                onValueChange={(value) => handleChange('profanity.action', value)}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="warn">Uyar</SelectItem>
                                    <SelectItem value="delete">Sil</SelectItem>
                                    <SelectItem value="mute">Sustur</SelectItem>
                                    <SelectItem value="kick">At</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {config.profanity.action === 'mute' && (
                            <div className="space-y-2">
                                <Label>Susturma Süresi (saniye)</Label>
                                <Input
                                    type="number"
                                    value={config.profanity.muteDuration}
                                    onChange={(e) => handleChange('profanity.muteDuration', parseInt(e.target.value))}
                                />
                            </div>
                        )}

                        <Separator />

                        <div className="space-y-2">
                            <Label>Özel Yasaklı Kelimeler</Label>
                            <div className="flex gap-2">
                                <Input
                                    value={newWord}
                                    onChange={(e) => setNewWord(e.target.value)}
                                    placeholder="Kelime ekle..."
                                    onKeyPress={(e) => e.key === 'Enter' && addWord()}
                                />
                                <Button onClick={addWord} size="icon" variant="outline">
                                    <Plus className="h-4 w-4" />
                                </Button>
                            </div>
                            <div className="flex flex-wrap gap-2 mt-2">
                                {config.profanity.customWords.map((word) => (
                                    <Badge key={word} variant="secondary" className="gap-1 pr-1">
                                        {word}
                                        <button onClick={() => removeWord(word)} className="ml-1 hover:text-destructive">
                                            <X className="h-3 w-3" />
                                        </button>
                                    </Badge>
                                ))}
                            </div>
                        </div>
                    </CardContent>
                )}
            </Card>

            {/* Link Filter */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-blue-500/10">
                                <LinkIcon className="h-5 w-5 text-blue-400" />
                            </div>
                            <div>
                                <CardTitle className="text-base">Link Engelleyici</CardTitle>
                                <CardDescription>İzin verilmeyen bağlantıları engelle</CardDescription>
                            </div>
                        </div>
                        <Switch
                            checked={config.links.enabled}
                            onCheckedChange={(checked) => handleChange('links.enabled', checked)}
                        />
                    </div>
                </CardHeader>
                {config.links.enabled && (
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <Label>İşlem</Label>
                            <Select
                                value={config.links.action}
                                onValueChange={(value) => handleChange('links.action', value)}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="warn">Uyar</SelectItem>
                                    <SelectItem value="delete">Sil</SelectItem>
                                    <SelectItem value="mute">Sustur</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <Separator />

                        <div className="space-y-2">
                            <Label>İzin Verilen Domainler (Whitelist)</Label>
                            <div className="flex gap-2">
                                <Input
                                    value={newDomain}
                                    onChange={(e) => setNewDomain(e.target.value)}
                                    placeholder="domain.com"
                                    onKeyPress={(e) => e.key === 'Enter' && addDomain()}
                                />
                                <Button onClick={addDomain} size="icon" variant="outline">
                                    <Plus className="h-4 w-4" />
                                </Button>
                            </div>
                            <div className="flex flex-wrap gap-2 mt-2">
                                {config.links.whitelist.map((domain) => (
                                    <Badge key={domain} variant="outline" className="gap-1 pr-1">
                                        {domain}
                                        <button onClick={() => removeDomain(domain)} className="ml-1 hover:text-destructive">
                                            <X className="h-3 w-3" />
                                        </button>
                                    </Badge>
                                ))}
                            </div>
                        </div>
                    </CardContent>
                )}
            </Card>

            {/* Caps Protection */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-yellow-500/10">
                                <Type className="h-5 w-5 text-yellow-400" />
                            </div>
                            <div>
                                <CardTitle className="text-base">Caps Lock Koruması</CardTitle>
                                <CardDescription>Aşırı büyük harf kullanımını engelle</CardDescription>
                            </div>
                        </div>
                        <Switch
                            checked={config.caps.enabled}
                            onCheckedChange={(checked) => handleChange('caps.enabled', checked)}
                        />
                    </div>
                </CardHeader>
                {config.caps.enabled && (
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Eşik Değeri (%)</Label>
                                <Input
                                    type="number"
                                    min="50"
                                    max="100"
                                    value={config.caps.threshold}
                                    onChange={(e) => handleChange('caps.threshold', parseInt(e.target.value))}
                                />
                                <p className="text-xs text-muted-foreground">
                                    Mesajın bu yüzdesinden fazlası büyük harfse tetiklenir
                                </p>
                            </div>
                            <div className="space-y-2">
                                <Label>Minimum Mesaj Uzunluğu</Label>
                                <Input
                                    type="number"
                                    min="5"
                                    value={config.caps.minLength}
                                    onChange={(e) => handleChange('caps.minLength', parseInt(e.target.value))}
                                />
                                <p className="text-xs text-muted-foreground">
                                    Bu uzunluktan kısa mesajlar kontrol edilmez
                                </p>
                            </div>
                        </div>
                    </CardContent>
                )}
            </Card>

            {/* Spam Protection */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-purple-500/10">
                                <MessageSquare className="h-5 w-5 text-purple-400" />
                            </div>
                            <div>
                                <CardTitle className="text-base">Spam & Flood Koruması</CardTitle>
                                <CardDescription>Hızlı mesaj gönderimini engelle</CardDescription>
                            </div>
                        </div>
                        <Switch
                            checked={config.spam.enabled}
                            onCheckedChange={(checked) => handleChange('spam.enabled', checked)}
                        />
                    </div>
                </CardHeader>
                {config.spam.enabled && (
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Mesaj Eşiği</Label>
                                <Input
                                    type="number"
                                    min="3"
                                    value={config.spam.messageThreshold}
                                    onChange={(e) => handleChange('spam.messageThreshold', parseInt(e.target.value))}
                                />
                                <p className="text-xs text-muted-foreground">
                                    Kaç mesaj gönderilince tetiklensin
                                </p>
                            </div>
                            <div className="space-y-2">
                                <Label>Süre (saniye)</Label>
                                <Input
                                    type="number"
                                    min="3"
                                    value={config.spam.interval}
                                    onChange={(e) => handleChange('spam.interval', parseInt(e.target.value))}
                                />
                                <p className="text-xs text-muted-foreground">
                                    Bu süre içinde
                                </p>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>İşlem</Label>
                            <Select
                                value={config.spam.action}
                                onValueChange={(value) => handleChange('spam.action', value)}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="warn">Uyar</SelectItem>
                                    <SelectItem value="mute">Sustur</SelectItem>
                                    <SelectItem value="kick">At</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {config.spam.action === 'mute' && (
                            <div className="space-y-2">
                                <Label>Susturma Süresi (saniye)</Label>
                                <Input
                                    type="number"
                                    value={config.spam.muteDuration}
                                    onChange={(e) => handleChange('spam.muteDuration', parseInt(e.target.value))}
                                />
                            </div>
                        )}
                    </CardContent>
                )}
            </Card>
        </div>
    );
}
