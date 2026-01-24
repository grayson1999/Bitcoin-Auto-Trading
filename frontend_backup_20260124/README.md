# Frontend

![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-6.0-646CFF?logo=vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind-3.4-06B6D4?logo=tailwindcss&logoColor=white)

> Bitcoin Auto-Trading 대시보드 프론트엔드

## Tech Stack

| 기술 | 버전 | 용도 |
|------|------|------|
| React | 18.3 | UI 프레임워크 |
| TypeScript | 5.6 | 타입 안전성 |
| Vite | 6.0 | 빌드 도구 |
| TanStack Query | 5.62 | 서버 상태 관리 |
| React Router | 6.28 | 라우팅 |
| Axios | 1.7 | HTTP 클라이언트 |
| Tailwind CSS | 3.4 | 스타일링 |
| Recharts | 2.14 | 차트 시각화 |

## Setup

```bash
# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env
```

## Development

```bash
# 개발 서버 실행
npm run dev
```

http://localhost:5173 에서 실행됩니다.

## Environment Variables

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `VITE_API_URL` | 백엔드 API URL | `http://localhost:8000` |
| `VITE_AUTH_API_URL` | 인증 서버 URL | `http://localhost:8001` |

## Build

```bash
# 프로덕션 빌드
npm run build

# 빌드 미리보기
npm run preview
```

빌드 결과물: `dist/`

## Scripts

| 명령어 | 설명 |
|--------|------|
| `npm run dev` | 개발 서버 (HMR) |
| `npm run build` | 프로덕션 빌드 |
| `npm run preview` | 빌드 미리보기 |
| `npm run lint` | ESLint 검사 |
| `npm test` | Vitest 테스트 |
