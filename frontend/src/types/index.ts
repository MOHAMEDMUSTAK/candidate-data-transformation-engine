// Type definitions matching the backend models

export interface Location {
  city?: string;
  region?: string;
  country?: string;
}

export interface Links {
  linkedin?: string;
  github?: string;
  portfolio?: string;
  other: string[];
}

export interface SkillEntry {
  name: string;
  confidence: number;
  sources: string[];
}

export interface ExperienceEntry {
  company?: string;
  title?: string;
  start?: string;
  end?: string;
  summary?: string;
}

export interface EducationEntry {
  institution?: string;
  degree?: string;
  field?: string;
  end_year?: number;
}

export interface FieldConfidence {
  field: string;
  confidence: number;
  source_count: number;
  sources_agreeing: number;
}

export interface QualityScore {
  overall_score: number;
  missing_fields: string[];
  suggestions: string[];
  field_completeness: Record<string, boolean>;
}

export interface ProvenanceEntry {
  field: string;
  original_value: any;
  normalized_value: any;
  winning_value: any;
  source: string;
  source_type: string;
  source_priority: number;
  extraction_method: string;
  timestamp: string;
  rules_applied: string[];
  confidence: number;
  accepted: boolean;
  explanation: string;
}

export interface CanonicalCandidate {
  candidate_id: string;
  full_name: string;
  emails: string[];
  phones: string[];
  location: Location;
  headline?: string;
  years_experience?: number;
  skills: SkillEntry[];
  experience: ExperienceEntry[];
  education: EducationEntry[];
  links: Links;
  provenance: any[];
  overall_confidence: number;
  field_confidences?: FieldConfidence[];
  quality_score?: QualityScore;
}

export interface StageResult {
  stage_name: string;
  stage_index: number;
  status: "pending" | "running" | "success" | "warning" | "error" | "skipped";
  start_time?: string;
  end_time?: string;
  execution_time_ms: number;
  warnings: string[];
  errors: string[];
  fields_transformed: number;
  records_processed: number;
  details: Record<string, any>;
  changes: Record<string, any>[];
}

export interface RuleApplication {
  rule_name: string;
  rule_category: string;
  description: string;
  field: string;
  original_value: any;
  transformed_value: any;
  stage: string;
  timestamp: string;
}

export interface TransformationStep {
  step_name: string;
  stage: string;
  input_value: any;
  output_value: any;
  rule_applied: string;
  explanation: string;
  timestamp: string;
}

export interface FieldTransformationChain {
  field: string;
  steps: TransformationStep[];
  final_value: any;
  total_transformations: number;
}

export interface ConflictRecord {
  field: string;
  candidates: { value: any; source: string; priority: number }[];
  winner: { value: any; source: string; priority: number };
  rejected: { value: any; source: string; priority: number }[];
  explanation: string;
  confidence: number;
}

export interface PipelineResponse {
  success: boolean;
  candidate?: CanonicalCandidate;
  projected_output?: Record<string, any>;
  exported_json?: string;
  stage_results: StageResult[];
  provenance: ProvenanceEntry[];
  field_provenance: Record<string, any>;
  transformation_chains: Record<string, FieldTransformationChain>;
  rule_applications: RuleApplication[];
  conflicts: ConflictRecord[];
  analytics: Record<string, any>;
  validation_errors: any[];
  log_entries: any[];
  field_confidences: FieldConfidence[];
  quality_score?: QualityScore;
  total_time_ms: number;
  timestamp: string;
}

export interface OutputConfig {
  fields: {
    path: string;
    from?: string;
    type: string;
    required: boolean;
    normalize?: string;
  }[];
  include_confidence: boolean;
  include_provenance: boolean;
  include_analytics: boolean;
  on_missing: "null" | "omit" | "error";
}
