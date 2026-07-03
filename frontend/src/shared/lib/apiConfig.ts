// URL base do backend FastAPI (ver backend/app/main.py). Configurável via .env.local em produção.
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
