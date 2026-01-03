// API Configuration and Types for Lithium Control Center

// Environment
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API Client
class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;

        const response = await fetch(url, {
            ...options,
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new ApiError(response.status, error.detail || 'Request failed');
        }

        return response.json();
    }

    // Auth
    async getMe(): Promise<User> {
        return this.request<User>('/auth/me');
    }

    async logout(): Promise<void> {
        return this.request('/auth/logout', { method: 'POST' });
    }

    // Guilds
    async getGuilds(): Promise<Guild[]> {
        return this.request<Guild[]>('/guilds');
    }

    async getGuildModules(guildId: string): Promise<ModuleStatus[]> {
        return this.request<ModuleStatus[]>(`/guilds/${guildId}/modules`);
    }

    async getModuleConfig(guildId: string, moduleKey: string): Promise<ModuleConfig> {
        return this.request<ModuleConfig>(`/guilds/${guildId}/modules/${moduleKey}`);
    }

    async updateModuleConfig(
        guildId: string,
        moduleKey: string,
        data: ModuleUpdateRequest
    ): Promise<ModuleUpdateResponse> {
        return this.request<ModuleUpdateResponse>(`/guilds/${guildId}/modules/${moduleKey}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async testModule(
        guildId: string,
        moduleKey: string,
        testData: ModuleTestRequest
    ): Promise<ModuleTestResponse> {
        return this.request<ModuleTestResponse>(`/guilds/${guildId}/modules/${moduleKey}/test`, {
            method: 'POST',
            body: JSON.stringify(testData),
        });
    }

    // Audit Logs
    async getAuditLogs(guildId: string, page = 1): Promise<PaginatedResponse<AuditLog>> {
        return this.request<PaginatedResponse<AuditLog>>(`/guilds/${guildId}/audit-logs?page=${page}`);
    }

    async getBotEvents(guildId: string, page = 1): Promise<PaginatedResponse<BotEvent>> {
        return this.request<PaginatedResponse<BotEvent>>(`/guilds/${guildId}/bot-events?page=${page}`);
    }

    // Config Versioning
    async getConfigVersions(guildId: string): Promise<ConfigVersion[]> {
        return this.request<ConfigVersion[]>(`/guilds/${guildId}/config/versions`);
    }

    async publishConfig(guildId: string): Promise<{ version: number }> {
        return this.request<{ version: number }>(`/guilds/${guildId}/config/publish`, {
            method: 'POST',
        });
    }

    async rollbackConfig(guildId: string, versionId: number): Promise<{ success: boolean }> {
        return this.request<{ success: boolean }>(`/guilds/${guildId}/config/rollback/${versionId}`, {
            method: 'POST',
        });
    }

    // Giveaways
    async getGiveaways(guildId: string): Promise<Giveaway[]> {
        return this.request<Giveaway[]>(`/guilds/${guildId}/giveaways`);
    }

    async createGiveaway(guildId: string, data: CreateGiveawayRequest): Promise<Giveaway> {
        return this.request<Giveaway>(`/guilds/${guildId}/giveaways`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async endGiveaway(guildId: string, giveawayId: string): Promise<Giveaway> {
        return this.request<Giveaway>(`/guilds/${guildId}/giveaways/${giveawayId}/end`, {
            method: 'POST',
        });
    }

    async rerollGiveaway(guildId: string, giveawayId: string): Promise<Giveaway> {
        return this.request<Giveaway>(`/guilds/${guildId}/giveaways/${giveawayId}/reroll`, {
            method: 'POST',
        });
    }

    // Metrics
    async getMetrics(guildId: string): Promise<GuildMetrics> {
        return this.request<GuildMetrics>(`/guilds/${guildId}/metrics`);
    }

    // System Status
    async getSystemStatus(guildId: string): Promise<SystemStatusResponse> {
        return this.request<SystemStatusResponse>(`/guilds/${guildId}/system-status`);
    }

    // Recent Activities
    async getRecentActivities(guildId: string, limit = 10): Promise<RecentActivitiesResponse> {
        return this.request<RecentActivitiesResponse>(`/guilds/${guildId}/recent-activities?limit=${limit}`);
    }

    // ============================================
    // V2 API - Production Endpoints
    // ============================================

    // Dashboard - Single endpoint for all data
    async getDashboard(guildId: string): Promise<ApiResponse<DashboardData>> {
        return this.request<ApiResponse<DashboardData>>(`/guilds/${guildId}/dashboard`);
    }

    // Moderation
    async getModeration(guildId: string, status?: string, page = 1): Promise<ApiResponse<ModerationResponse>> {
        const params = new URLSearchParams({ page: String(page) });
        if (status) params.set('status', status);
        return this.request<ApiResponse<ModerationResponse>>(`/guilds/${guildId}/moderation?${params}`);
    }

    async getModerationWarnings(guildId: string): Promise<ApiResponse<WarningsResponse>> {
        return this.request<ApiResponse<WarningsResponse>>(`/guilds/${guildId}/moderation/warnings`);
    }

    // Tickets
    async getTickets(guildId: string, status?: string, page = 1): Promise<ApiResponse<TicketsResponse>> {
        const params = new URLSearchParams({ page: String(page) });
        if (status) params.set('status', status);
        return this.request<ApiResponse<TicketsResponse>>(`/guilds/${guildId}/tickets?${params}`);
    }

    async updateTicket(guildId: string, ticketId: number, status: string): Promise<ApiResponse<{ updated: boolean }>> {
        return this.request<ApiResponse<{ updated: boolean }>>(`/guilds/${guildId}/tickets/${ticketId}?status=${status}`, {
            method: 'PUT',
        });
    }

    // Audit Logs v2
    async getAuditLogsV2(guildId: string, filters: AuditFilters = {}): Promise<ApiResponse<AuditLogsResponse>> {
        const params = new URLSearchParams();
        if (filters.action) params.set('action', filters.action);
        if (filters.actor) params.set('actor', filters.actor);
        if (filters.from_date) params.set('from_date', filters.from_date);
        if (filters.to_date) params.set('to_date', filters.to_date);
        if (filters.page) params.set('page', String(filters.page));
        return this.request<ApiResponse<AuditLogsResponse>>(`/guilds/${guildId}/audit?${params}`);
    }

    // Analytics
    async getAnalytics(guildId: string, metric = 'messages', from_date?: string, to_date?: string): Promise<ApiResponse<AnalyticsResponse>> {
        const params = new URLSearchParams({ metric });
        if (from_date) params.set('from_date', from_date);
        if (to_date) params.set('to_date', to_date);
        return this.request<ApiResponse<AnalyticsResponse>>(`/guilds/${guildId}/analytics?${params}`);
    }

    // Settings
    async getSettings(guildId: string): Promise<ApiResponse<GuildSettings>> {
        return this.request<ApiResponse<GuildSettings>>(`/guilds/${guildId}/settings`);
    }

    async updateSettings(guildId: string, settings: GuildSettings): Promise<ApiResponse<{ updated: boolean }>> {
        return this.request<ApiResponse<{ updated: boolean }>>(`/guilds/${guildId}/settings`, {
            method: 'PUT',
            body: JSON.stringify(settings),
        });
    }

    // SSE Event Stream
    createEventSource(guildId: string): EventSource {
        return new EventSource(`${this.baseUrl}/guilds/${guildId}/events`, {
            withCredentials: true,
        });
    }
}

// Custom Error
export class ApiError extends Error {
    constructor(public status: number, message: string) {
        super(message);
        this.name = 'ApiError';
    }
}

// Export singleton
export const api = new ApiClient(API_URL);

// ============================================
// TYPES
// ============================================

export interface User {
    id: number;
    discord_id: string;
    username: string;
    avatar_url: string | null;
    created_at: string;
    key_auth?: boolean;
    guild_id?: string;
}

export interface Guild {
    id: string;
    name: string;
    icon: string | null;
    owner: boolean;
    permissions: number;
    bot_installed?: boolean;
}

export interface ModuleStatus {
    module_key: string;
    display_name: string;
    description: string;
    icon: string;
    category: 'moderation' | 'community' | 'utility' | 'fun';
    enabled: boolean;
    risk_level: 'low' | 'medium' | 'high';
    has_draft: boolean;
    last_updated?: string;
}

export interface ModuleConfig {
    module_key: string;
    enabled: boolean;
    config: Record<string, unknown>;
    last_updated: string;
    updated_by: {
        id: string;
        username: string;
    } | null;
    version: number;
    has_draft: boolean;
    draft_config?: Record<string, unknown>;
}

export interface ModuleUpdateRequest {
    enabled?: boolean;
    config?: Record<string, unknown>;
    publish?: boolean;
}

export interface ModuleUpdateResponse {
    status: 'success' | 'error';
    version: number;
    published: boolean;
    bot_notified: boolean;
}

export interface ModuleTestRequest {
    test_type: 'message' | 'user' | 'event';
    content?: string;
    user_id?: string;
    event_data?: Record<string, unknown>;
}

export interface ModuleTestResponse {
    would_trigger: boolean;
    rules_matched: Array<{
        rule: string;
        reason: string;
        action: string;
    }>;
    preview_response?: {
        type: 'embed' | 'message';
        title?: string;
        description?: string;
        color?: string;
    };
}

export interface AuditLog {
    id: number;
    actor_id: string;
    actor_name: string;
    action: string;
    target_type: string;
    target_id: string;
    diff_json: Record<string, unknown> | null;
    created_at: string;
}

export interface BotEvent {
    id: number;
    event_type: string;
    payload_json: Record<string, unknown>;
    created_at: string;
}

export interface ConfigVersion {
    id: number;
    version_number: number;
    created_by: string;
    created_at: string;
    note: string | null;
    is_published: boolean;
}

export interface Giveaway {
    id: string;
    channel_id: string;
    message_id: string;
    prize: string;
    winners_count: number;
    required_roles: string[];
    ends_at: string;
    ended: boolean;
    winners: string[];
    entries_count: number;
}

export interface CreateGiveawayRequest {
    channel_id: string;
    prize: string;
    winners_count: number;
    duration_minutes: number;
    required_roles?: string[];
}

export interface GuildMetrics {
    members: {
        total: number;
        online: number;
        new_24h: number;
    };
    messages: {
        today: number;
        week: number;
    };
    moderation: {
        actions_today: number;
        warnings_active: number;
    };
    leveling?: {
        active_users: number;
        xp_today: number;
    };
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    pages: number;
}

// System Status Types
export interface ServiceStatus {
    name: string;
    status: 'online' | 'degraded' | 'offline';
    latency_ms?: number;
}

export interface SystemStatusResponse {
    services: ServiceStatus[];
    timestamp: string;
}

// Recent Activities Types
export interface RecentActivity {
    id: number;
    icon: string;
    title: string;
    description: string;
    time: string;
    type: 'success' | 'warning' | 'info' | 'error';
    created_at: string;
}

export interface RecentActivitiesResponse {
    items: RecentActivity[];
    total: number;
}

// Module-specific config types
export interface AutoModConfig {
    enabled: boolean;
    profanity: {
        enabled: boolean;
        customWords: string[];
        action: 'warn' | 'delete' | 'mute' | 'kick';
        muteDuration?: number;
        logChannel?: string;
    };
    links: {
        enabled: boolean;
        whitelist: string[];
        allowedRoles: string[];
        allowedChannels: string[];
        action: 'warn' | 'delete' | 'mute';
    };
    caps: {
        enabled: boolean;
        threshold: number;
        minLength: number;
        action: 'warn' | 'delete';
    };
    spam: {
        enabled: boolean;
        messageThreshold: number;
        interval: number;
        action: 'warn' | 'mute' | 'kick';
        muteDuration: number;
    };
    exemptRoles: string[];
    exemptChannels: string[];
}

export interface JailConfig {
    enabled: boolean;
    jailRoleId: string;
    jailChannelId: string;
    logChannelId?: string;
    autoJail: {
        onRaidDetection: boolean;
        onSpamThreshold: number;
        onWarningThreshold: number;
    };
    jailMessage: string;
    releaseMessage: string;
}

export interface LevelingConfig {
    enabled: boolean;
    xpPerMessage: { min: number; max: number };
    xpCooldown: number;
    levelUpChannel?: string;
    levelUpMessage: string;
    rewards: Array<{
        level: number;
        roleId: string;
        removeOnLevelUp: boolean;
    }>;
    roleMultipliers: Array<{
        roleId: string;
        multiplier: number;
    }>;
    ignoredChannels: string[];
    ignoredRoles: string[];
    rankCard: {
        backgroundColor: string;
        accentColor: string;
        showAvatar: boolean;
    };
}

export interface ReactionRolesConfig {
    enabled: boolean;
    maxMenusPerGuild: number;
}

export interface ReactionRoleMenu {
    id: string;
    channelId: string;
    messageId: string;
    title: string;
    description?: string;
    type: 'reaction' | 'button' | 'dropdown';
    exclusive: boolean;
    roles: Array<{
        emoji: string;
        roleId: string;
        label?: string;
        description?: string;
    }>;
}

// ============================================
// V2 API Types
// ============================================

export interface ApiResponse<T> {
    ok: boolean;
    data: T;
    meta: {
        request_id: string;
        timestamp: string;
    };
}

export interface MemberStats {
    total: number;
    online: number;
    new_24h: number;
}

export interface MessageStats {
    today: number;
    week: number;
}

export interface ModerationStats {
    actions_today: number;
    warnings_active: number;
}

export interface ModuleStats {
    enabled: number;
    total: number;
}

export interface DashboardData {
    members: MemberStats;
    messages: MessageStats;
    moderation: ModerationStats;
    modules: ModuleStats;
    system_status: ServiceStatus[];
    recent_activities: RecentActivity[];
}

export interface ModerationCase {
    id: number;
    case_id: number;
    action_type: string;
    user_id: string;
    username?: string;
    moderator_id: string;
    reason?: string;
    active: boolean;
    duration?: number;
    created_at: string;
}

export interface ModerationResponse {
    items: ModerationCase[];
    total: number;
    page: number;
    pages: number;
}

export interface Warning {
    id: number;
    user_id: string;
    moderator_id: string;
    reason: string;
    created_at: string;
}

export interface WarningsResponse {
    items: Warning[];
    total: number;
}

export interface TicketItem {
    id: number;
    channel_id?: string;
    user_id: string;
    username?: string;
    subject: string;
    status: string;
    messages_count: number;
    created_at: string;
    closed_at?: string;
}

export interface TicketsResponse {
    items: TicketItem[];
    counts: {
        open: number;
        claimed: number;
        closed: number;
    };
    page: number;
}

export interface AuditFilters {
    action?: string;
    actor?: string;
    from_date?: string;
    to_date?: string;
    page?: number;
}

export interface AuditLogItem {
    id: number;
    actor_id: string;
    actor_name?: string;
    action: string;
    target_type?: string;
    target_id?: string;
    diff_json?: Record<string, unknown>;
    created_at: string;
}

export interface AuditLogsResponse {
    items: AuditLogItem[];
    page: number;
    total: number;
}

export interface AnalyticsDataPoint {
    date: string;
    messages?: number;
    users?: number;
    actions?: number;
}

export interface AnalyticsResponse {
    metric: string;
    from_date: string;
    to_date: string;
    data: AnalyticsDataPoint[];
}

export interface GuildSettings {
    prefix: string;
    language: string;
    log_channel_id?: string;
    welcome_enabled: boolean;
    welcome_channel_id?: string;
    welcome_message?: string;
    dm_on_warn: boolean;
    dm_on_mute: boolean;
    notify_on_join: boolean;
    notify_on_leave: boolean;
    notify_on_ban: boolean;
}

