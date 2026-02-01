import axios from 'axios';
import { VideoData } from '../types';

const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isLocal ? 'http://localhost:8000/api' : '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 18000, // 18 seconds (accounting for multi-step extraction)
});

export const fetchVideoInfo = async (url: string): Promise<VideoData> => {
  try {
    const response = await apiClient.get<VideoData>('/info', {
      params: { url },
    });
    return response.data;
  } catch (error: any) {
    console.error('API Error:', error);
    if (error.response) {
      const detail = error.response.data?.detail || "The platform is currently blocking our requests. Please try again later.";
      throw new Error(detail);
    }
    throw new Error("Umii API is offline. Check your internet connection.");
  }
};

export const getDownloadLink = (videoData: VideoData): string => {
  const params = new URLSearchParams({
    url: videoData.download_url,
    title: videoData.title,
    ext: videoData.ext,
  });
  return `${API_BASE_URL}/download?${params.toString()}`;
};