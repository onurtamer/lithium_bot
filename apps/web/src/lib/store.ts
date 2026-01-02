import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Guild, ModuleStatus } from '@/lib/api';

// Auth Store
interface AuthState {
    user: User | null;
    isLoading: boolean;
    setUser: (user: User | null) => void;
    setLoading: (loading: boolean) => void;
    logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    isLoading: true,
    setUser: (user) => set({ user, isLoading: false }),
    setLoading: (isLoading) => set({ isLoading }),
    logout: () => set({ user: null, isLoading: false }),
}));

// Guild Store
interface GuildState {
    guilds: Guild[];
    currentGuild: Guild | null;
    isLoading: boolean;
    setGuilds: (guilds: Guild[]) => void;
    setCurrentGuild: (guild: Guild | null) => void;
    setLoading: (loading: boolean) => void;
}

export const useGuildStore = create<GuildState>((set) => ({
    guilds: [],
    currentGuild: null,
    isLoading: true,
    setGuilds: (guilds) => set({ guilds, isLoading: false }),
    setCurrentGuild: (currentGuild) => set({ currentGuild }),
    setLoading: (isLoading) => set({ isLoading }),
}));

// Module Store
interface ModuleState {
    modules: ModuleStatus[];
    isLoading: boolean;
    hasUnsavedChanges: boolean;
    setModules: (modules: ModuleStatus[]) => void;
    setLoading: (loading: boolean) => void;
    setUnsavedChanges: (hasChanges: boolean) => void;
    toggleModule: (moduleKey: string, enabled: boolean) => void;
}

export const useModuleStore = create<ModuleState>((set) => ({
    modules: [],
    isLoading: true,
    hasUnsavedChanges: false,
    setModules: (modules) => set({ modules, isLoading: false }),
    setLoading: (isLoading) => set({ isLoading }),
    setUnsavedChanges: (hasUnsavedChanges) => set({ hasUnsavedChanges }),
    toggleModule: (moduleKey, enabled) =>
        set((state) => ({
            modules: state.modules.map((m) =>
                m.module_key === moduleKey ? { ...m, enabled } : m
            ),
            hasUnsavedChanges: true,
        })),
}));

// UI Store (persisted)
interface UIState {
    theme: 'light' | 'dark' | 'system';
    sidebarCollapsed: boolean;
    setTheme: (theme: 'light' | 'dark' | 'system') => void;
    toggleSidebar: () => void;
    setSidebarCollapsed: (collapsed: boolean) => void;
}

export const useUIStore = create<UIState>()(
    persist(
        (set) => ({
            theme: 'dark',
            sidebarCollapsed: false,
            setTheme: (theme) => set({ theme }),
            toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
            setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
        }),
        {
            name: 'lithium-ui-settings',
        }
    )
);

// Notification Store
interface Notification {
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    message?: string;
    duration?: number;
}

interface NotificationState {
    notifications: Notification[];
    addNotification: (notification: Omit<Notification, 'id'>) => void;
    removeNotification: (id: string) => void;
    clearAll: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
    notifications: [],
    addNotification: (notification) =>
        set((state) => ({
            notifications: [
                ...state.notifications,
                { ...notification, id: Math.random().toString(36).substr(2, 9) },
            ],
        })),
    removeNotification: (id) =>
        set((state) => ({
            notifications: state.notifications.filter((n) => n.id !== id),
        })),
    clearAll: () => set({ notifications: [] }),
}));
