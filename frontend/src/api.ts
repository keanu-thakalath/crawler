"use server";
import { getAuthToken } from "./utils/auth";

const BASE_URL = process.env.BACKEND_URL;

// Enums from backend domain models
export enum DataOrigin {
  ACADEMIC = "Academic",
  GOVERNMENT = "Government",
  NEWS = "News",
  BLOG = "Blog",
  NON_PROFIT = "Non-Profit",
}

export enum SourceFormat {
  RESEARCH_PAPER = "Research Paper",
  ARTICLE = "Article",
  DATA_REPOSITORY = "Data Repository",
  HISTORICAL_INFO = "Historical Info",
  POLICY = "Policy",
  LAW = "Law",
  NARRATIVE = "Narrative",
  DATA_VISUALIZATION = "Data Visualization",
  LETTER = "Letter",
  GOVERNMENT_SOURCE = "Government Source",
}

export enum FocusArea {
  NON_HUMAN_ANIMALS = "Non-Human Animals",
  HUMANS = "Humans",
  ENVIRONMENT = "Environment",
  COMMUNITY = "Community",
  BUSINESS = "Business",
}

export enum DatasetPresence {
  PRESENT = "Present",
  ABSENT = "Absent",
}

export enum ReviewStatus {
  UNREVIEWED = "Unreviewed",
  APPROVED = "Approved",
}

export enum Relevancy {
  HIGH = "High",
  MEDIUM = "Medium",
  LOW = "Low",
  NOT_RELEVANT = "Not Relevant",
}

// Job outcome types based on backend domain models
export interface JobError {
  message: string;
  created_at: string;
}

export interface ScrapeJobResult {
  created_at: string;
  markdown: string;
  internal_links: string[];
  external_links: string[];
  file_links: string[];
}

export interface ExtractJobResult {
  created_at: string;
  summary: string;
  key_facts: string;
  key_quotes: string;
  key_figures: string;
  trustworthiness: string;
  relevancy: Relevancy;
  relevant_internal_links: string[];
  relevant_external_links: string[];
  relevant_file_links: string[];
  input_tokens: number;
  output_tokens: number;
  prompt: string;
  model: string;
  review_status: ReviewStatus;
}

export interface SummarizeJobResult {
  created_at: string;
  summary: string;
  key_facts: string;
  key_quotes: string;
  key_figures: string;
  data_origin: DataOrigin;
  source_format: SourceFormat;
  focus_area: FocusArea;
  dataset_presence: DatasetPresence;
  input_tokens: number;
  output_tokens: number;
  prompt: string;
  model: string;
  review_status: ReviewStatus;
}

export interface CrawlJobResult {
  created_at: string;
  pages_crawled: number;
  total_pages_found: number;
  max_pages_limit: number;
}

// Job types
export interface Job {
  job_id: string;
  created_at: string;
  outcome?:
    | ScrapeJobResult
    | ExtractJobResult
    | SummarizeJobResult
    | CrawlJobResult
    | JobError;
}

export interface Page {
  url: string;
  jobs: Job[];
}

export interface Source {
  url: string;
  pages: Page[];
  jobs: Job[];
}

export interface TokenResponse {
  token: string;
}

async function withAuth() {
  return {
    Authorization: `Bearer ${await getAuthToken()}`,
  };
}

export async function getUnreviewedJobs() {
  const response = await fetch(`${BASE_URL}/sources/unreviewed-jobs`, {
    headers: {
      ...(await withAuth()),
    },
  });
  return (await response.json()) as Source[];
}

export async function getFailedJobs() {
  const response = await fetch(`${BASE_URL}/sources/failed-jobs`, {
    headers: {
      ...(await withAuth()),
    },
  });
  return (await response.json()) as Source[];
}

export async function getCrawledSources() {
  const response = await fetch(`${BASE_URL}/sources/crawled`, {
    headers: {
      ...(await withAuth()),
    },
  });
  return (await response.json()) as Source[];
}

export async function getDiscoveredSources() {
  const response = await fetch(`${BASE_URL}/sources/discovered`, {
    headers: {
      ...(await withAuth()),
    },
  });
  return (await response.json()) as Source[];
}

export async function getInProgressSources() {
  const response = await fetch(`${BASE_URL}/sources/in_progress`, {
    headers: {
      ...(await withAuth()),
    },
  });
  return (await response.json()) as Source[];
}

export async function getSource(sourceUrl: string) {
  const response = await fetch(
    `${BASE_URL}/source?source_url=${encodeURIComponent(sourceUrl)}`,
    {
      headers: {
        ...(await withAuth()),
      },
    }
  );
  if (!response.ok) {
    const json = await response.json();
    throw new Error(json.detail);
  }
  return (await response.json()) as Source;
}

export async function getPage(pageUrl: string) {
  const response = await fetch(
    `${BASE_URL}/page?page_url=${encodeURIComponent(pageUrl)}`,
    {
      headers: {
        ...(await withAuth()),
      },
    }
  );
  if (!response.ok) {
    const json = await response.json();
    throw new Error(json.detail);
  }
  return (await response.json()) as Page;
}

export async function crawlUrl(
  url: string,
  maxPages: number,
  extractPrompt?: string,
  summarizePrompt?: string
) {
  const response = await fetch(`${BASE_URL}/crawl`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await withAuth()),
    },
    body: JSON.stringify({
      url,
      max_pages: maxPages,
      extract_prompt: extractPrompt,
      summarize_prompt: summarizePrompt,
    }),
  });
  if (!response.ok) {
    const json = await response.json();
    throw new Error(json.detail);
  }
}

export async function resetTables() {
  const response = await fetch(`${BASE_URL}/reset`, {
    method: "DELETE",
    headers: {
      ...(await withAuth()),
    },
  });
  if (!response.ok) {
    throw new Error(`Failed to reset tables: ${response.statusText}`);
  }
}

export async function exchangeKey(key: string) {
  const response = await fetch(`${BASE_URL}/exchange_key?key=${key}`, {
    method: "POST",
  });
  if (!response.ok) {
    return;
  }
  return (await response.json()) as TokenResponse;
}

export async function approveJob(jobId: string) {
  const response = await fetch(`${BASE_URL}/jobs/${jobId}/approve`, {
    method: "PATCH",
    headers: {
      ...(await withAuth()),
    },
  });
  if (!response.ok) {
    const json = await response.json();
    throw new Error(json.detail);
  }
  return (await response.json()) as Job;
}

export async function editJobSummary(jobId: string, summary: string) {
  const response = await fetch(`${BASE_URL}/jobs/${jobId}/summary`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...(await withAuth()),
    },
    body: JSON.stringify({ summary }),
  });
  if (!response.ok) {
    const json = await response.json();
    throw new Error(json.detail);
  }
  return (await response.json()) as Job;
}
