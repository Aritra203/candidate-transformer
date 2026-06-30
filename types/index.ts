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

export interface Skill {
  name: string;
  confidence: number;
  sources: string[];
}

export interface Experience {
  company?: string;
  title?: string;
  start?: string;
  end?: string;
  summary?: string;
}

export interface Education {
  institution?: string;
  degree?: string;
  field?: string;
  end_year?: string;
}

export interface ProvenanceRecord {
  field: string;
  source: string;
  method: string;
  confidence: number;
}

export interface CandidateProfile {
  candidate_id: string;
  full_name?: string;
  emails: string[];
  phones: string[];
  location: Location;
  links: Links;
  headline?: string;
  years_experience?: number;
  skills: Skill[];
  experience: Experience[];
  education: Education[];
  provenance: ProvenanceRecord[];
  overall_confidence: number;
}

export interface FieldProjection {
  path: string;
  from?: string;
  type?: 'string' | 'string[]' | 'number' | 'object' | 'object[]';
  normalize?: 'E164' | 'canonical';
  required?: boolean;
}

export interface ProjectionConfig {
  fields: FieldProjection[];
  include_confidence: boolean;
  include_provenance: boolean;
  on_missing: 'null' | 'omit' | 'error';
}

export interface UploadResponse {
  filename: string;
  size: number;
  type: 'csv' | 'pdf' | 'json';
  path: string;
}

export interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR' | 'DEBUG';
  stage: string;
  message: string;
}

export interface TransformResponse {
  success: boolean;
  profiles: any[]; // Depending on projection config, structure might change from CandidateProfile
  logs: LogEntry[];
  outputPath: string;
}

export type ActivePage = 'dashboard' | 'upload' | 'configuration' | 'pipeline' | 'output' | 'logs' | 'about';
