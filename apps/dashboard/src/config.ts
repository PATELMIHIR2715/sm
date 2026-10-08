// Centralized API configuration supporting local development and production deployments
export const API_BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000').replace(/\/+$/, '');
export const NOTIFICATIONS_API_BASE = (import.meta.env.VITE_NOTIFICATIONS_URL || 'http://127.0.0.1:5001').replace(/\/+$/, '');
