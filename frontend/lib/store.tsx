'use client';
import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

type CartItem = { product_id: number; name: string; quantity: number; unit_price: number };
type ToastType = { id: number; message: string; type: 'success' | 'error' | 'info' };

type Store = {
  cart: CartItem[];
  toasts: ToastType[];
  userPreferences: { theme: 'light' | 'dark'; compact: boolean };
  addToCart: (item: Omit<CartItem, 'quantity'> & { quantity?: number }) => void;
  removeFromCart: (product_id: number) => void;
  updateCartQty: (product_id: number, quantity: number) => void;
  clearCart: () => void;
  cartTotal: number;
  toast: (message: string, type?: ToastType['type']) => void;
  dismissToast: (id: number) => void;
  setPreference: (key: keyof Store['userPreferences'], value: boolean | string) => void;
};

const Ctx = createContext<Store | null>(null);

let toastId = 0;

export function StoreProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<CartItem[]>([]);
  const [toasts, setToasts] = useState<ToastType[]>([]);
  const [userPreferences, setUserPreferences] = useState({ theme: 'light' as const, compact: false });

  const addToCart = useCallback((item: Omit<CartItem, 'quantity'> & { quantity?: number }) => {
    setCart((prev) => {
      const existing = prev.find((x) => x.product_id === item.product_id);
      if (existing) return prev.map((x) => x.product_id === item.product_id ? { ...x, quantity: x.quantity + (item.quantity || 1) } : x);
      return [...prev, { ...item, quantity: item.quantity || 1 }];
    });
  }, []);

  const removeFromCart = useCallback((product_id: number) => {
    setCart((prev) => prev.filter((x) => x.product_id !== product_id));
  }, []);

  const updateCartQty = useCallback((product_id: number, quantity: number) => {
    setCart((prev) => quantity <= 0
      ? prev.filter((x) => x.product_id !== product_id)
      : prev.map((x) => x.product_id === product_id ? { ...x, quantity } : x));
  }, []);

  const clearCart = useCallback(() => setCart([]), []);

  const toast = useCallback((message: string, type: ToastType['type'] = 'info') => {
    const id = ++toastId;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const setPreference = useCallback((key: keyof Store['userPreferences'], value: boolean | string) => {
    setUserPreferences((prev) => ({ ...prev, [key]: value }));
  }, []);

  const cartTotal = cart.reduce((sum, item) => sum + item.quantity * item.unit_price, 0);

  return (
    <Ctx.Provider value={{
      cart, toasts, userPreferences,
      addToCart, removeFromCart, updateCartQty, clearCart, cartTotal,
      toast, dismissToast, setPreference,
    }}>
      {children}
    </Ctx.Provider>
  );
}

export function useStore() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useStore must be used within StoreProvider');
  return ctx;
}
