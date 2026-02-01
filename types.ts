export interface VideoData {
  id: string;
  title: string;
  thumbnail: string;
  duration: number | null;
  platform: string;
  download_url: string;
  ext: string;
  isMock?: boolean;
}

export interface ApiError {
  detail: string;
}