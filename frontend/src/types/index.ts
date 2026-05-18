export type NodeType = 'process' | 'ground' | 'location' | 'method' | 'equipment' | 'impact';

export interface NodeItem {
  'id:ID': string;
  ':LABEL': string;
  [key: string]: string | undefined;
  name?: string;
  condition_name?: string;
  loc_name?: string;
  method_name?: string;
  equip_name?: string;
  impact_type?: string;
  description?: string;
  action?: string;
}

export interface RiskNode {
  id: string;
  description: string;
  project?: string;
  score: number;
  level: string;
  color: string;
  cluster_band?: string;
  cluster_label?: string;
  cluster_rank?: number;
  cluster_color?: string;
  cluster_score_min?: number;
  cluster_score_max?: number;
  cluster_size?: number;
  matched: string;
  strategies: string[];
  likelihood?: number;
  impact?: string;
  impact_score?: number;
  confidence?: number;
  frequency?: number;
  recency?: number;
  expert_weight?: number;
  project_similarity?: number;
  score_explanation?: {
    model_version?: string;
    base_score?: number;
    adjusted_score?: number;
    matched_factors?: string[];
    rationale?: string[];
    source_evidence?: {
      source_project?: string;
      source_version?: string;
      source_ll?: string;
      cause?: string;
      impact_text?: string;
    };
    [key: string]: unknown;
  };
  standards?: string[];
  roles?: string[];
  source_evidence?: {
    source_project?: string;
    source_version?: string;
    source_ll?: string;
    cause?: string;
    impact_text?: string;
  };
}

export interface GraphNode {
  id: string;
  label: string;
  title: string;
  color: string;
  size: number;
  detail?: {
    project?: string;
    sourceVersion?: string;
    sourceLL?: string;
    cause?: string;
    impactText?: string;
    matched?: string[];
    strategies?: string[];
    impacts?: string[];
    roles?: string[];
    standards?: string[];
    targetRisk?: string;
    expectedEffect?: string;
    requiredEquipment?: string;
    relatedStandard?: string;
    responsibleRole?: string;
  };
}

export interface GraphEdge {
  from: string;
  to: string;
  title: string;
  color: string;
  width?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface DataVersion {
  source_file: string;
  source_file_hash: string;
  source_file_mtime: string;
  ontology_build_at: string;
}

export interface ScoreResponse {
  total_risks: number;
  critical_count: number;
  max_score: number;
  risks: RiskNode[];
  graph: GraphData;
  recommendations?: MissingReviewRecommendation[];
  data_version?: DataVersion;
  model_version?: string;
  banding_method?: string;
  banding_model_version?: string;
  band_boundaries?: Array<Record<string, unknown>>;
  band_fallback_reason?: string;
  history_id?: number;
}

export interface MissingReviewRecommendation {
  type: string;
  title: string;
  reason: string;
  suggested_filter: Record<string, string>;
}

export type Filters = Record<NodeType, string | null>;

export interface ScoreRequest extends Filters {
  query: string;
}

export interface CompareRiskItem {
  id: string;
  description: string;
  score: number;
  level: string;
  color: string;
  cluster_band?: string;
  cluster_label?: string;
  matched: string[];
}

export interface CompareSummary {
  total_risks: number;
  max_score: number;
  critical_count: number;
}

export interface DesignCompareRequest {
  before: ScoreRequest;
  after: ScoreRequest;
}

export interface DesignCompareResponse {
  model_version: string;
  before: CompareSummary;
  after: CompareSummary;
  new_risks: CompareRiskItem[];
  removed_risks: CompareRiskItem[];
  increased_risks: CompareRiskItem[];
  decreased_risks: CompareRiskItem[];
  additional_strategies: string[];
  related_standards: string[];
}

export interface DesignCompareReportResponse {
  id: number;
  report_type: 'comparison';
  title: string;
  created_at: string;
  download_url: string;
  pdf_url: string;
  package_url: string;
  model_version: string;
  data_version: DataVersion;
}

export interface SavedCondition {
  id: number;
  created_at: string;
  title: string;
  query: string;
  filters: Filters;
}

export interface SavedConditionsResponse {
  items: SavedCondition[];
}

export interface DeleteConditionResponse {
  id: number;
  deleted: boolean;
}

export interface DashboardMetric {
  label: string;
  value: string;
  subValue: string;
  accentColor: string;
}

export interface DashboardRiskSummary {
  id: string;
  title: string;
  project: string;
  score: number;
}

export interface DashboardNotification {
  title: string;
  desc: string;
  time: string;
  color: string;
}

export interface DashboardOperationalStatus {
  label: string;
  value: string;
  status: string;
  description: string;
  color: string;
}

export interface DashboardDistributionItem {
  label: string;
  value: number;
  color: string;
}

export interface DashboardSummary {
  kpis: DashboardMetric[];
  distribution: DashboardDistributionItem[];
  impactDistribution?: DashboardDistributionItem[];
  operationalStatus?: DashboardOperationalStatus[];
  trend: number[];
  recentAnalyses: DashboardRiskSummary[];
  notifications: DashboardNotification[];
}

export interface LibraryItem {
  id: string;
  title: string;
  category: string;
  tags: string[];
  relationTypes?: string[];
  project: string;
  relationCount: number;
}

export interface CountItem {
  label: string;
  count: number;
}

export interface LibraryResponse {
  items: LibraryItem[];
  categories: CountItem[];
  popularTags: CountItem[];
  relationTypes?: CountItem[];
  filters?: {
    query: string;
    category: string;
    tag: string;
    relation_type?: string;
  };
}

export interface LibraryFilters {
  query?: string;
  category?: string;
  tag?: string;
  relationType?: string;
}

export type KnowledgeItemType = 'risk' | 'strategy' | 'lesson' | 'project' | 'standard' | 'equipment' | 'method';
export type KnowledgeVerificationStatus = 'pending_review' | 'verified' | 'rejected';

export interface KnowledgeSubmissionRequest {
  item_type: KnowledgeItemType;
  title: string;
  content: string;
  tags?: string[];
  source?: string;
}

export interface KnowledgeSubmissionItem {
  id: number;
  created_at: string;
  updated_at: string;
  item_type: KnowledgeItemType;
  title: string;
  content: string;
  tags: string[];
  source: string;
  verification_status: KnowledgeVerificationStatus;
  data_version: DataVersion;
  reviewer: string;
  review_note: string;
}

export interface KnowledgeSubmissionsResponse {
  items: KnowledgeSubmissionItem[];
}

export interface KnowledgeStatusRequest {
  verification_status: KnowledgeVerificationStatus;
  reviewer?: string;
  review_note?: string;
}

export interface LibraryRelatedItem {
  id: string;
  label: string;
}

export interface LibraryItemDetail {
  id: string;
  title: string;
  project: string;
  sourceVersion: string;
  sourceLL: string;
  cause: string;
  impactText: string;
  relationCount: number;
  relatedConditions: Record<NodeType, LibraryRelatedItem[]>;
  strategies: LibraryRelatedItem[];
  impacts: LibraryRelatedItem[];
  roles: LibraryRelatedItem[];
  standards: LibraryRelatedItem[];
  lessons: LibraryRelatedItem[];
  graph?: GraphData;
}

export interface AnalysisHistoryItem {
  id: number;
  created_at: string;
  query: string;
  filters: Filters;
  top_risk: string;
  total_risks: number;
  critical_count: number;
  max_score: number;
  model_version?: string;
}

export interface AnalysisHistoryResponse {
  items: AnalysisHistoryItem[];
}

export interface AnalysisHistoryFilters {
  query?: string;
  project?: string;
  dateFrom?: string;
  dateTo?: string;
}

export interface ReportItem {
  id: number | string;
  history_id: number;
  title: string;
  created_at: string;
  top_risk: string;
  total_risks: number;
  critical_count: number;
  max_score: number;
  format: 'HTML';
  download_url: string;
  pdf_url: string;
  package_url?: string;
  shared: boolean;
  share_url?: string;
  data_version?: DataVersion;
  model_version?: string;
  report_type?: 'analysis' | 'comparison';
}

export interface ReportsResponse {
  items: ReportItem[];
  summary: {
    total: number;
    shared: number;
    html: number;
  };
}

export interface StandardEvidenceItem {
  code: string;
  name: string;
  version: string;
  source_url: string;
  section_path: string[];
  section_label: string;
  text: string;
  confidence: string;
}

export interface StandardEvidenceResponse {
  query: string;
  source: string;
  items: StandardEvidenceItem[];
}

export interface StandardSummaryItem {
  code: string;
  name: string;
  version: string;
  source_url: string;
  clause_count: number;
}

export interface StandardsSearchResponse {
  query: string;
  source: string;
  items: StandardSummaryItem[];
}

export interface StandardsClausesResponse {
  query: string;
  code: string;
  source: string;
  items: StandardEvidenceItem[];
}

export interface StandardsVerifyResponse {
  code: string;
  is_valid: boolean;
  standard: Omit<StandardSummaryItem, 'clause_count'> | null;
  clause_count: number;
}

export interface StandardRevalidationItem {
  id: string;
  doc_name: string;
  status: string;
  verified_code: string;
  candidate_codes: string[];
  message: string;
}

export interface StandardsRevalidationResponse {
  total: number;
  verified_count: number;
  candidate_count: number;
  unknown_count: number;
  source: string;
  items: StandardRevalidationItem[];
}

export interface StandardsLinkItem {
  id: number;
  created_at: string;
  updated_at: string;
  target_type: 'risk' | 'strategy';
  target_id: string;
  standard_code: string;
  standard_name: string;
  clause_path: string;
  clause_label: string;
  clause_text: string;
  source_url: string;
  note: string;
}

export interface StandardsLinkRequest {
  target_type: 'risk' | 'strategy';
  target_id: string;
  standard_code: string;
  standard_name?: string;
  clause_path: string;
  clause_label?: string;
  clause_text?: string;
  source_url?: string;
  note?: string;
}

export interface StandardsLinksResponse {
  items: StandardsLinkItem[];
}

export type NotificationFilter = 'all' | 'unread' | 'important';

export interface NotificationItem {
  id: number;
  created_at: string;
  category: string;
  title: string;
  message: string;
  is_read: boolean;
  is_important: boolean;
  is_archived?: boolean;
}

export interface NotificationsResponse {
  items: NotificationItem[];
  summary: {
    total: number;
    unread: number;
    important: number;
  };
}
