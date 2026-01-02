'use client';

import { useParams } from 'next/navigation';
import { MODULES, type ModuleKey } from '@/lib/utils';
import { ModuleTemplate } from '@/components/modules';
import { AutoModSettings } from './AutoModSettings';
import { JailSettings } from './JailSettings';
import { LevelingSettings } from './LevelingSettings';
import { DefaultSettings } from './DefaultSettings';

export default function ModuleDetailPage() {
    const params = useParams();
    const guildId = params.guildId as string;
    const moduleKey = params.moduleKey as ModuleKey;

    const moduleInfo = MODULES[moduleKey];

    if (!moduleInfo) {
        return (
            <div className="text-center py-12">
                <h1 className="text-2xl font-bold mb-2">Modül Bulunamadı</h1>
                <p className="text-muted-foreground">
                    "{moduleKey}" adında bir modül bulunamadı.
                </p>
            </div>
        );
    }

    // Get risk level
    const riskLevel = moduleInfo.risk as 'low' | 'medium' | 'high' || 'low';

    // Render appropriate settings component
    const renderSettings = () => {
        switch (moduleKey) {
            case 'automod':
                return <AutoModSettings guildId={guildId} />;
            case 'jail':
                return <JailSettings guildId={guildId} />;
            case 'leveling':
                return <LevelingSettings guildId={guildId} />;
            default:
                return <DefaultSettings moduleKey={moduleKey} guildId={guildId} />;
        }
    };

    return (
        <ModuleTemplate
            guildId={guildId}
            moduleKey={moduleKey}
            moduleName={moduleInfo.name}
            moduleDescription={moduleInfo.description}
            moduleRisk={riskLevel}
        >
            {{
                settings: renderSettings(),
                channels: <ChannelSettings guildId={guildId} moduleKey={moduleKey} />,
                preview: <PreviewSection guildId={guildId} moduleKey={moduleKey} />,
            }}
        </ModuleTemplate>
    );
}

// Channel/Role Settings Component
function ChannelSettings({ guildId, moduleKey }: { guildId: string; moduleKey: string }) {
    return (
        <div className="space-y-6">
            <div className="p-6 border border-border rounded-lg bg-card">
                <h3 className="font-semibold mb-4">Kanal Ayarları</h3>
                <p className="text-muted-foreground text-sm">
                    Bu modül için kanal yapılandırmaları burada gösterilecek.
                </p>
            </div>

            <div className="p-6 border border-border rounded-lg bg-card">
                <h3 className="font-semibold mb-4">Rol Ayarları</h3>
                <p className="text-muted-foreground text-sm">
                    Bu modül için rol yapılandırmaları burada gösterilecek.
                </p>
            </div>
        </div>
    );
}

// Preview Section Component
function PreviewSection({ guildId, moduleKey }: { guildId: string; moduleKey: string }) {
    return (
        <div className="p-6 border border-border rounded-lg bg-card">
            <h3 className="font-semibold mb-4">Önizleme & Test</h3>
            <p className="text-muted-foreground text-sm mb-4">
                Ayarlarınızın nasıl çalışacağını test edin.
            </p>

            <div className="p-4 bg-muted/50 rounded-lg">
                <p className="text-sm text-muted-foreground text-center">
                    Önizleme alanı - yakında aktif olacak
                </p>
            </div>
        </div>
    );
}
