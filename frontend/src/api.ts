const BASE_URL = "http://localhost:8000";

export interface PageWithoutSource {
  url: string;
}

export interface SourceWithoutContent {
  url: string;
  pages: PageWithoutSource[];
}

export interface JobResponse {
  id: number;
  job_type: string;
  status: string;
}

export interface FileWithoutPage {
  id: number;
  url: string;
}

export interface ScrapeJobResponse {
  id: number;
  page_job_id: number;
  markdown: string;
  html: string;
}

export interface ExtractJobResponse {
  id: number;
  page_job_id: number;
  summary: string;
  input_tokens: number;
  output_tokens: number;
  files: FileWithoutPage[];
}

export interface SummarizeJobResponse {
  id: number;
  source_job_id: number;
  summary: string;
  data_origin: string;
  source_format: string;
  focus_area: string;
  input_tokens: number;
  output_tokens: number;
}

export async function getSources() {
  const response = await fetch(`${BASE_URL}/sources`);
  return (await response.json()) as SourceWithoutContent[];
}

export async function getSourceJobs(sourceUrl: string) {
  const response = await fetch(
    `${BASE_URL}/sources/jobs?source_url=${encodeURIComponent(sourceUrl)}`
  );
  return (await response.json()) as JobResponse[];
}

export async function getPageJobs(pageUrl: string) {
  const response = await fetch(
    `${BASE_URL}/pages/jobs?page_url=${encodeURIComponent(pageUrl)}`
  );
  return (await response.json()) as JobResponse[];
}

export async function getScrapeResult(jobId: number) {
  const response = await fetch(`${BASE_URL}/jobs/scrape/${jobId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch scrape result: ${response.statusText}`);
  }
  return (await response.json()) as ScrapeJobResponse;
}

export async function getExtractResult(jobId: number) {
  const response = await fetch(`${BASE_URL}/jobs/extract/${jobId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch extract result: ${response.statusText}`);
  }
  return (await response.json()) as ExtractJobResponse;
}

export async function getSummarizeResult(jobId: number) {
  const response = await fetch(`${BASE_URL}/jobs/summarize/${jobId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch summarize result: ${response.statusText}`);
  }
  return (await response.json()) as SummarizeJobResponse;
}

export async function crawlUrl(url: string) {
  const response = await fetch(`${BASE_URL}/crawl`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url }),
  });
  if (!response.ok) {
    const json = await response.json();
    throw new Error(json.detail);
  }
}

export async function resetTables() {
  const response = await fetch(`${BASE_URL}/reset`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`Failed to reset tables: ${response.statusText}`);
  }
}
