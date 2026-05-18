import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { AnalysisHistoryFilters, DesignCompareRequest, KnowledgeItemType, KnowledgeSubmissionRequest, KnowledgeVerificationStatus, LibraryFilters, NotificationFilter, ScoreRequest, StandardsLinkRequest } from '../types';
import { archiveNotification, compareDesignChange, createDesignCompareReport, createKnowledgeSubmission, createStandardsLink, deleteSavedCondition, fetchAnalysisHistory, fetchDashboardSummary, fetchKnowledgeSubmissions, fetchLibraryItemDetail, fetchLibraryItems, fetchNodes, fetchNotifications, fetchReports, fetchSavedConditions, fetchStandardEvidence, fetchStandardsLinks, markAllNotificationsRead, markNotificationRead, rerunAnalysis, revalidateStandards, saveCondition, setNotificationImportant, setReportShared, updateKnowledgeSubmissionStatus } from './client';

export function useNodeList(type: string) {
  return useQuery({
    queryKey: ['nodes', type],
    queryFn: () => fetchNodes(type),
    staleTime: 5 * 60 * 1000,
  });
}

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchDashboardSummary,
    staleTime: 5 * 60 * 1000,
  });
}

export function useLibraryItems(filters: LibraryFilters = {}) {
  return useQuery({
    queryKey: ['library-items', filters],
    queryFn: () => fetchLibraryItems(filters),
    staleTime: 5 * 60 * 1000,
  });
}

export function useLibraryItemDetail(riskId: string | null) {
  return useQuery({
    queryKey: ['library-item-detail', riskId],
    queryFn: () => fetchLibraryItemDetail(riskId ?? ''),
    enabled: Boolean(riskId),
    staleTime: 5 * 60 * 1000,
  });
}

export function useKnowledgeSubmissions(filters: { itemType?: KnowledgeItemType; verificationStatus?: KnowledgeVerificationStatus } = {}) {
  return useQuery({
    queryKey: ['knowledge-submissions', filters],
    queryFn: () => fetchKnowledgeSubmissions(filters),
    staleTime: 30 * 1000,
  });
}

export function useKnowledgeSubmissionActions() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['knowledge-submissions'] });
  return {
    create: useMutation({ mutationFn: (request: KnowledgeSubmissionRequest) => createKnowledgeSubmission(request), onSuccess: invalidate }),
    updateStatus: useMutation({
      mutationFn: ({ id, verificationStatus, reviewer, reviewNote }: { id: number; verificationStatus: KnowledgeVerificationStatus; reviewer?: string; reviewNote?: string }) => updateKnowledgeSubmissionStatus(id, {
        verification_status: verificationStatus,
        reviewer,
        review_note: reviewNote,
      }),
      onSuccess: invalidate,
    }),
  };
}

export function useStandardEvidence(query: string) {
  return useQuery({
    queryKey: ['standard-evidence', query],
    queryFn: () => fetchStandardEvidence(query),
    enabled: query.trim().length > 0,
    staleTime: 60 * 60 * 1000,
  });
}

export function useStandardsRevalidationAction() {
  return useMutation({ mutationFn: revalidateStandards });
}

export function useStandardsLinks() {
  return useQuery({
    queryKey: ['standards-links'],
    queryFn: () => fetchStandardsLinks(),
    staleTime: 30 * 1000,
  });
}

export function useStandardsLinkActions() {
  const queryClient = useQueryClient();
  return {
    create: useMutation({
      mutationFn: (request: StandardsLinkRequest) => createStandardsLink(request),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['standards-links'] }),
    }),
  };
}

export function useAnalysisHistory(filters: string | AnalysisHistoryFilters = '') {
  return useQuery({
    queryKey: ['analysis-history', filters],
    queryFn: () => fetchAnalysisHistory(filters),
    staleTime: 30 * 1000,
  });
}

export function useReports(query = '') {
  return useQuery({
    queryKey: ['reports', query],
    queryFn: () => fetchReports(query),
    staleTime: 30 * 1000,
  });
}

export function useReportShareAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ historyId, shared }: { historyId: number; shared: boolean }) => setReportShared(historyId, shared),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reports'] }),
  });
}

export function useRerunAnalysis() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: rerunAnalysis,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis-history'] });
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
  });
}

export function useSavedConditions() {
  return useQuery({
    queryKey: ['saved-conditions'],
    queryFn: fetchSavedConditions,
    staleTime: 30 * 1000,
  });
}

export function useSavedConditionActions() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['saved-conditions'] });
  return {
    save: useMutation({ mutationFn: (request: ScoreRequest) => saveCondition(request), onSuccess: invalidate }),
    delete: useMutation({ mutationFn: deleteSavedCondition, onSuccess: invalidate }),
  };
}

export function useDesignCompareAction() {
  return useMutation({ mutationFn: (request: DesignCompareRequest) => compareDesignChange(request) });
}

export function useDesignCompareReportAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: DesignCompareRequest) => createDesignCompareReport(request),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reports'] }),
  });
}

export function useNotifications(filter: NotificationFilter = 'all') {
  return useQuery({
    queryKey: ['notifications', filter],
    queryFn: () => fetchNotifications(filter),
    staleTime: 30 * 1000,
  });
}

export function useNotificationActions() {
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['notifications'] });
  return {
    markRead: useMutation({ mutationFn: markNotificationRead, onSuccess: invalidate }),
    setImportant: useMutation({
      mutationFn: ({ id, isImportant }: { id: number; isImportant: boolean }) => setNotificationImportant(id, isImportant),
      onSuccess: invalidate,
    }),
    markAllRead: useMutation({ mutationFn: markAllNotificationsRead, onSuccess: invalidate }),
    archive: useMutation({ mutationFn: archiveNotification, onSuccess: invalidate }),
  };
}
