"use server";
import { getAuthToken } from "./utils/auth";

const BASE_URL = process.env.BACKEND_URL;

// Job outcome types based on backend domain models
export interface JobError {
  message: string;
  created_at: string;
}
export interface ScrapeJobOutcome {
  created_at: string;
  markdown: string;
}

export interface ExtractJobOutcome {
  input_tokens: number;
  output_tokens: number;
  summary: string;
  internal_links: string[];
  external_links: string[];
  file_links: string[];
  created_at: string;
  review_status: string;
}

export interface SummarizeJobOutcome {
  input_tokens: number;
  output_tokens: number;
  summary: string;
  data_origin: string;
  source_format: string;
  focus_area: string;
  created_at: string;
  review_status: string;
}

// Job types
export interface Job {
  job_id: string;
  created_at: string;
  outcome?: ScrapeJobOutcome | ExtractJobOutcome | SummarizeJobOutcome | JobError;
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

export async function getSources() {
  const response = await fetch(`${BASE_URL}/sources`, {
    headers: {
      ...(await withAuth()),
    },
  });
  return (await response.json()) as Source[];
}

export async function addSource(url: string) {
  const response = await fetch(`${BASE_URL}/sources?source_url=${url}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await withAuth()),
    },
  });
  if (!response.ok) {
    const json = await response.json();
    throw new Error(json.detail);
  }
}

export async function crawlUrl(url: string, maxPages: number, extractPrompt?: string, summarizePrompt?: string) {
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
      summarize_prompt: summarizePrompt
    }),
  });
  if (!response.ok) {
    const json = await response.json();
    throw new Error(json.detail);
  }
}

export async function deleteSource(url: string) {
  const response = await fetch(
    `${BASE_URL}/sources?source_url=${encodeURIComponent(url)}`,
    {
      method: "DELETE",
      headers: {
        ...(await withAuth()),
      },
    }
  );
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

export async function extractPage(pageUrl: string, markdownContent: string, prompt?: string) {
  const response = await fetch(`${BASE_URL}/extract`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await withAuth()),
    },
    body: JSON.stringify({ 
      page_url: pageUrl, 
      markdown_content: markdownContent,
      prompt: prompt
    }),
  });
  if (!response.ok) {
    const json = await response.json();
    throw new Error(json.detail);
  }
  return (await response.json()) as Job;
}

export async function summarizeSource(sourceUrl: string, allPageSummaries: string, prompt?: string) {
  const response = await fetch(`${BASE_URL}/summarize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await withAuth()),
    },
    body: JSON.stringify({ 
      source_url: sourceUrl, 
      all_page_summaries: allPageSummaries,
      prompt: prompt
    }),
  });
  if (!response.ok) {
    const json = await response.json();
    throw new Error(json.detail);
  }
  return (await response.json()) as Job;
}
