/**
 * 本地存储工具函数
 * 提供本地存储的读写工具函数
 */

// 存储键前缀
const STORAGE_PREFIX = 'openmanus_';

// 存储项类型
export interface StorageItem<T> {
    value: T;
    timestamp: number;
    expiry?: number;
}

// 存储工具
export const storage = {
    // 设置存储项
    set: <T>(key: string, value: T, expiry?: number): void => {
        const item: StorageItem<T> = {
            value,
            timestamp: Date.now(),
            expiry,
        };
        localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(item));
    },

    // 获取存储项
    get: <T>(key: string): T | null => {
        const data = localStorage.getItem(STORAGE_PREFIX + key);
        if (!data) return null;

        try {
            const item: StorageItem<T> = JSON.parse(data);

            // 检查是否过期
            if (item.expiry && Date.now() - item.timestamp > item.expiry) {
                localStorage.removeItem(STORAGE_PREFIX + key);
                return null;
            }

            return item.value;
        } catch (error) {
            console.error('解析存储数据失败:', error);
            return null;
        }
    },

    // 删除存储项
    remove: (key: string): void => {
        localStorage.removeItem(STORAGE_PREFIX + key);
    },

    // 清除所有存储项
    clear: (): void => {
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith(STORAGE_PREFIX)) {
                localStorage.removeItem(key);
            }
        });
    },

    // 获取所有存储项
    getAll: <T>(): Record<string, T> => {
        const result: Record<string, T> = {};
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith(STORAGE_PREFIX)) {
                const value = storage.get<T>(key.slice(STORAGE_PREFIX.length));
                if (value) {
                    result[key.slice(STORAGE_PREFIX.length)] = value;
                }
            }
        });
        return result;
    },
};
