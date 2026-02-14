// ui/src/router.tsx
import { createBrowserRouter, redirect, RouteObject } from 'react-router-dom';
import * as api from './services/api';
import { useAuthStore } from './features/auth/store';
import {
  createNoteAction,
  updateNoteAction,
  deleteNoteAction,
} from './features/notes/actions';
import RouteError from './features/ui/components/RouteError';
import { STORAGE_KEYS } from './config/storage';

const requireAuth = async () => {
  const { isAuthenticated } = useAuthStore.getState();
  if (!isAuthenticated) {
    throw redirect('/login');
  }
  return null;
};

export const routes: RouteObject[] = [
  {
    path: '/',
    loader: () => {
      const { isAuthenticated } = useAuthStore.getState();
      return redirect(isAuthenticated ? '/notes' : '/login');
    },
  },
  {
    path: '/login',
    lazy: async () => {
      const { default: Component } = await import(
        './features/auth/components/LoginForm'
      );
      return { Component };
    },
  },
  {
    path: '/oidc/callback',
    lazy: async () => {
      const { default: Component } = await import(
        './features/auth/components/OIDCCallback'
      );
      return { Component };
    },
  },
  {
    id: 'notes-layout',
    path: '/notes',
    loader: async () => {
      await requireAuth();
      try {
        const notes = await api.getNotes();
        return { notes };
      } catch (error) {
        if (
          error instanceof TypeError &&
          !localStorage.getItem(STORAGE_KEYS.AUTH)
        ) {
          throw redirect('/login');
        }
        throw error;
      }
    },
    action: createNoteAction,
    lazy: async () => {
      const { default: Component } = await import(
        './features/notes/components/NotesLayout'
      );
      return { Component };
    },
    errorElement: <RouteError />,
    children: [
      {
        index: true,
        element: null,
      },
      {
        path: ':noteId',
        action: updateNoteAction,
        lazy: async () => {
          const { default: Component } = await import(
            './features/notes/components/NoteContent'
          );
          return { Component };
        },
        errorElement: <RouteError />,
        children: [
          {
            path: 'delete',
            action: deleteNoteAction,
          },
        ],
      },
    ],
  },
  {
    path: '/settings',
    loader: requireAuth,
    lazy: async () => {
      const { default: Component } = await import(
        './features/settings/components/Settings'
      );
      return { Component };
    },
  },
  {
    path: '*',
    lazy: async () => {
      const { default: Component } = await import(
        './features/ui/components/NotFoundPage'
      );
      return { Component };
    },
  },
];

export const router = createBrowserRouter(routes);
