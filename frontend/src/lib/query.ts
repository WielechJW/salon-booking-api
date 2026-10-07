import { QueryClient, useQuery } from '@tanstack/react-query'
import { ApiError, getEmployees, getSalon, getServices } from './api/client'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: (count, error) => !(error instanceof ApiError && error.status < 500) && count < 1,
    },
    mutations: { retry: false },
  },
})

export const useServices = () =>
  useQuery({ queryKey: ['services'], queryFn: ({ signal }) => getServices(signal) })
export const useEmployees = () =>
  useQuery({ queryKey: ['employees'], queryFn: ({ signal }) => getEmployees(signal) })
export const useSalon = () =>
  useQuery({ queryKey: ['salon'], queryFn: ({ signal }) => getSalon(signal), staleTime: Infinity })

export async function invalidateBookings() {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ['appointments'] }),
    queryClient.invalidateQueries({ queryKey: ['availability'] }),
  ])
}
