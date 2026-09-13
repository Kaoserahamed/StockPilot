'use client';
import { useEffect, useCallback } from 'react';

type ShortcutMap = Record<string, () => void>;

/**
 * Hook for handling keyboard shortcuts.
 *
 * @param shortcuts - Map of key combinations to handler functions
 *   Format: 'ctrl+s', 'f2', 'escape', 'ctrl+shift+p'
 * @param enabled - Whether shortcuts are active (default: true)
 *
 * Usage:
 *   useKeyboardShortcuts({
 *     'f2': () => setShowSearch(true),
 *     'escape': () => setShowSearch(false),
 *     'ctrl+s': () => checkout(),
 *   });
 */
export function useKeyboardShortcuts(shortcuts: ShortcutMap, enabled: boolean = true) {
  const normalize = useCallback((e: KeyboardEvent): string => {
    const parts: string[] = [];
    if (e.ctrlKey || e.metaKey) parts.push('ctrl');
    if (e.shiftKey) parts.push('shift');
    if (e.altKey) parts.push('alt');
    const key = e.key.toLowerCase();
    if (!['control', 'shift', 'alt', 'meta'].includes(key)) {
      parts.push(key);
    }
    return parts.join('+');
  }, []);

  useEffect(() => {
    if (!enabled) return;

    const handler = (e: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
        // Only allow escape in inputs
        if (e.key === 'Escape') {
          const key = normalize(e);
          if (shortcuts[key]) {
            e.preventDefault();
            shortcuts[key]();
          }
        }
        return;
      }

      const key = normalize(e);
      if (shortcuts[key]) {
        e.preventDefault();
        shortcuts[key]();
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [shortcuts, enabled, normalize]);
}
