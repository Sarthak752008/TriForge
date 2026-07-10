// Central API base URL configuration
// In production (Vercel), reads from NEXT_PUBLIC_API_URL environment variable.
// In local development, falls back to http://localhost:8000.
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
