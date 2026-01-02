'use client';

import { MODULES, type ModuleKey } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Info } from 'lucide-react';

interface DefaultSettingsProps {
    moduleKey: ModuleKey;
    guildId: string;
}

export function DefaultSettings({ moduleKey, guildId }: DefaultSettingsProps) {
    const moduleInfo = MODULES[moduleKey];

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-primary/10">
                            <Info className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                            <CardTitle className="text-base">Temel Ayarlar</CardTitle>
                            <CardDescription>
                                {moduleInfo?.name || moduleKey} modülü için temel yapılandırma
                            </CardDescription>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="p-4 rounded-lg bg-muted/50 text-center">
                        <p className="text-muted-foreground">
                            Bu modül için detaylı ayarlar yakında eklenecek.
                        </p>
                        <p className="text-sm text-muted-foreground mt-2">
                            Şimdilik modülü aktif/pasif yapabilir ve temel ayarları kullanabilirsiniz.
                        </p>
                    </div>

                    <div className="space-y-4 pt-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <Label>Modül Durumu</Label>
                                <p className="text-xs text-muted-foreground">
                                    Modülü aktif veya pasif yapın
                                </p>
                            </div>
                            <Switch defaultChecked />
                        </div>

                        <div className="space-y-2">
                            <Label>Log Kanalı ID (Opsiyonel)</Label>
                            <Input placeholder="Kanal ID'si girin" />
                            <p className="text-xs text-muted-foreground">
                                Bu modülün olaylarının loglanacağı kanal
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
