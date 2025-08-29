"use server";
import { getAuthToken } from "./utils/auth";

const BASE_URL = process.env.BACKEND_URL;

// Job outcome types based on backend domain models
export interface ScrapeJobOutcome {
  created_at: string;
  markdown: string;
  html: string;
}

export interface ExtractJobOutcome {
  input_tokens: number;
  output_tokens: number;
  summary: string;
  internal_links: string[];
  external_links: string[];
  file_links: string[];
  created_at: string;
}

export interface SummarizeJobOutcome {
  input_tokens: number;
  output_tokens: number;
  summary: string;
  data_origin: string;
  source_format: string;
  focus_area: string;
  created_at: string;
}

// Job types
export interface Job {
  job_id: string;
  created_at: string;
  outcome?: ScrapeJobOutcome | ExtractJobOutcome | SummarizeJobOutcome;
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

export async function crawlUrl(url: string, maxPages: number) {
  const response = await fetch(`${BASE_URL}/crawl`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await withAuth()),
    },
    body: JSON.stringify({ url, max_pages: maxPages }),
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
