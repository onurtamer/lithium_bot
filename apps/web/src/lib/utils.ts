import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Format date relative to now
export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const target = new Date(date);
  const diffMs = now.getTime() - target.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'Az önce';
  if (diffMins < 60) return `${diffMins} dakika önce`;
  if (diffHours < 24) return `${diffHours} saat önce`;
  if (diffDays < 7) return `${diffDays} gün önce`;

  return target.toLocaleDateString('tr-TR');
}

// Format duration in seconds to human readable
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
  return `${Math.floor(seconds / 86400)}d`;
}

// Parse duration string (e.g., "10m", "1h", "7d") to seconds
export function parseDuration(duration: string): number {
  const match = duration.match(/^(\d+)([smhd])$/);
  if (!match) return 0;

  const [, value, unit] = match;
  const num = parseInt(value, 10);

  switch (unit) {
    case 's': return num;
    case 'm': return num * 60;
    case 'h': return num * 3600;
    case 'd': return num * 86400;
    default: return 0;
  }
}

// Generate Discord CDN URLs
export function getDiscordAvatar(userId: string, avatarHash: string | null, size = 128): string {
  if (!avatarHash) {
    // Default avatar based on user ID
    const defaultIndex = BigInt(userId) % BigInt(5);
    return `https://cdn.discordapp.com/embed/avatars/${defaultIndex}.png`;
  }

  const extension = avatarHash.startsWith('a_') ? 'gif' : 'png';
  return `https://cdn.discordapp.com/avatars/${userId}/${avatarHash}.${extension}?size=${size}`;
}

export function getGuildIcon(guildId: string, iconHash: string | null, size = 128): string {
  if (!iconHash) {
    return `https://cdn.discordapp.com/embed/avatars/0.png`;
  }

  const extension = iconHash.startsWith('a_') ? 'gif' : 'png';
  return `https://cdn.discordapp.com/icons/${guildId}/${iconHash}.${extension}?size=${size}`;
}

// Discord permission check
export function hasPermission(permissions: number, permission: number): boolean {
  return (permissions & permission) === permission;
}

// Discord permission flags
export const PERMISSIONS = {
  MANAGE_GUILD: 0x20,
  ADMINISTRATOR: 0x8,
  MANAGE_CHANNELS: 0x10,
  MANAGE_ROLES: 0x10000000,
  KICK_MEMBERS: 0x2,
  BAN_MEMBERS: 0x4,
  MANAGE_MESSAGES: 0x2000,
} as const;

// Module categories with metadata
export const MODULE_CATEGORIES = {
  moderation: {
    label: 'Moderasyon',
    description: 'Sunucu güvenliği ve moderasyon araçları',
    color: 'text-red-400',
  },
  community: {
    label: 'Topluluk',
    description: 'Topluluk etkileşimi ve eğlence',
    color: 'text-green-400',
  },
  utility: {
    label: 'Araçlar',
    description: 'Yardımcı araçlar ve otomasyon',
    color: 'text-blue-400',
  },
  fun: {
    label: 'Eğlence',
    description: 'Oyunlar ve eğlenceli komutlar',
    color: 'text-purple-400',
  },
} as const;

// Module definitions
export const MODULES = {
  moderation_audit: {
    key: 'moderation_audit',
    name: 'Denetim Kayıtları',
    description: 'Mesaj düzenleme/silme, ses kanalı hareketleri, üye değişiklikleri',
    icon: 'FileText',
    category: 'moderation',
    risk: 'low',
  },
  automod: {
    key: 'automod',
    name: 'Otomatik Moderasyon',
    description: 'Küfür filtresi, link engelleyici, spam koruması',
    icon: 'Shield',
    category: 'moderation',
    risk: 'medium',
  },
  jail: {
    key: 'jail',
    name: 'Hapis Sistemi',
    description: 'Kural ihlali yapan kullanıcıları izole edin',
    icon: 'Lock',
    category: 'moderation',
    risk: 'high',
  },
  temp_mute: {
    key: 'temp_mute',
    name: 'Süreli Susturma',
    description: 'Kullanıcıları belirli süre susturun',
    icon: 'VolumeX',
    category: 'moderation',
    risk: 'medium',
  },
  anti_raid: {
    key: 'anti_raid',
    name: 'Raid Koruması',
    description: 'Toplu katılım ve bot saldırılarını engeller',
    icon: 'ShieldAlert',
    category: 'moderation',
    risk: 'high',
  },
  tickets: {
    key: 'tickets',
    name: 'Ticket Sistemi',
    description: 'Destek talepleri için özel kanal yönetimi',
    icon: 'Ticket',
    category: 'utility',
    risk: 'low',
  },
  leveling: {
    key: 'leveling',
    name: 'Seviye Sistemi',
    description: 'XP kazanma ve seviye atlama sistemi',
    icon: 'TrendingUp',
    category: 'community',
    risk: 'low',
  },
  economy: {
    key: 'economy',
    name: 'Ekonomi',
    description: 'Sunucu içi para birimi ve ticaret',
    icon: 'Coins',
    category: 'community',
    risk: 'low',
  },
  starboard: {
    key: 'starboard',
    name: 'Starboard',
    description: 'En beğenilen mesajları özel kanalda sergileyin',
    icon: 'Star',
    category: 'community',
    risk: 'low',
  },
  reaction_roles: {
    key: 'reaction_roles',
    name: 'Tepki Rolleri',
    description: 'Kullanıcıların emoji ile rol almasını sağlayın',
    icon: 'Smile',
    category: 'utility',
    risk: 'medium',
  },
  giveaways: {
    key: 'giveaways',
    name: 'Çekilişler',
    description: 'Kolay ve adil çekiliş sistemi',
    icon: 'Gift',
    category: 'community',
    risk: 'low',
  },
  birthdays: {
    key: 'birthdays',
    name: 'Doğum Günleri',
    description: 'Üyelerin doğum günlerini kutlayın',
    icon: 'Cake',
    category: 'community',
    risk: 'low',
  },
  suggestions: {
    key: 'suggestions',
    name: 'Öneri Sistemi',
    description: 'Kullanıcı önerilerini toplayın ve yönetin',
    icon: 'MessageSquarePlus',
    category: 'utility',
    risk: 'low',
  },
  fun_games: {
    key: 'fun_games',
    name: 'Eğlence & Oyunlar',
    description: 'Taş-kağıt-makas, 8ball, düellolar',
    icon: 'Gamepad2',
    category: 'fun',
    risk: 'low',
  },
  utilities: {
    key: 'utilities',
    name: 'Yardımcı Araçlar',
    description: 'Çeviri, anket, hava durumu, finans',
    icon: 'Wrench',
    category: 'utility',
    risk: 'low',
  },
} as const;

export type ModuleKey = keyof typeof MODULES;
