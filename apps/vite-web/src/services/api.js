import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE || 'https://ac-research.onrender.com';

const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
});

/**
 * POST /api/research
 * @param {string} query
 * @returns {Promise<{ query: string, slug: string, results: object, meta: object }>}
 */
export async function postResearch(query) {
  const { data } = await api.post('/api/research', { query: String(query).trim() });
  return data;
}

/**
 * GET /api/research/{slug}/excel - triggers file download
 * @param {string} slug - from research response
 * @returns {Promise<Blob>}
 */
export async function getResearchExcel(slug) {
  const { data } = await api.get(`/api/research/${slug}/excel`, {
    responseType: 'blob',
  });
  return data;
}

export { baseURL };
