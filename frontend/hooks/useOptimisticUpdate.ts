'use client';
import { useQueryClient, useMutation } from '@tanstack/react-query';
import { useToast } from '@/components/Toast';

type OptimisticContext = {
  previousData: unknown;
};

/**
 * Hook for optimistic updates with automatic rollback on error.
 *
 * @param queryKey - The query key to update optimistically
 * @param mutationFn - The async mutation function
 * @param onSuccess - Optional callback on success
 *
 * Usage:
 *   const mutation = useOptimisticUpdate(
 *     ['products'],
 *     (newProduct) => api.post('/products', newProduct),
 *     () => showToast('Product created'),
 *   );
 */
export function useOptimisticUpdate<TData = unknown, TVariables = unknown>(
  queryKey: string[],
  mutationFn: (variables: TVariables) => Promise<TData>,
  onSuccess?: (data: TData, variables: TVariables) => void,
) {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<TData, Error, TVariables, OptimisticContext>({
    mutationFn,
    onMutate: async (variables: TVariables): Promise<OptimisticContext> => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey });

      // Snapshot previous value
      const previousData = queryClient.getQueryData(queryKey);

      // Return context for rollback
      return { previousData };
    },
    onError: (_err: Error, _variables: TVariables, context?: OptimisticContext) => {
      // Rollback on error
      if (context?.previousData !== undefined) {
        queryClient.setQueryData(queryKey, context.previousData);
      }
      const message = _err instanceof Error ? _err.message : 'Operation failed';
      toast.error(message);
    },
    onSuccess: (data: TData, variables: TVariables, _context: OptimisticContext) => {
      if (onSuccess) {
        onSuccess(data, variables);
      }
    },
    onSettled: () => {
      // Always refetch after mutation
      queryClient.invalidateQueries({ queryKey });
    },
  });
}
