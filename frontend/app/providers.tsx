'use client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import { AuthProvider } from '@/lib/auth';
import { ToastProvider } from '@/components/Toast';

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        retry: 1,
        staleTime: 30_000,        // Data fresh for 30s
        gcTime: 5 * 60 * 1000,    // Cache unused data for 5 min
        refetchOnWindowFocus: false, // Don't refetch when tab regains focus
        refetchOnReconnect: true,    // Refetch when network reconnects
      },
      mutations: {
        retry: 0,                   // Don't auto-retry mutations
      },
    },
  }));
  return (
    <QueryClientProvider client={client}>
      <ToastProvider>
        <AuthProvider>{children}</AuthProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
