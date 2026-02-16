export interface Note {
  id: string;
  title: string;
  content: string;
  createdAt: string;
  updatedAt: string;
  accessCount?: number;
  lastAccessedAt?: string;
}

export interface SimilarNote {
  id: string;
  title: string;
  similarity: number;
  updatedAt: string;
}

export interface User {
  username: string;
  password: string;
}
