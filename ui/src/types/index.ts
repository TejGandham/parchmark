export interface Note {
  id: string;
  title: string;
  content: string;
  createdAt: string;
  updatedAt: string;
  accessCount?: number;
  lastAccessedAt?: string;
}

export interface User {
  username: string;
  password: string;
}
