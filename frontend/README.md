# TaskFlow Frontend

React + TypeScript frontend dashboard for the Distributed Task Queue System.

## 🚀 Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Router** - Navigation
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **JWT** - Authentication

## 📦 Setup

1. **Install dependencies:**

   ```bash
   npm install
   ```

2. **Configure environment:**

   ```bash
   cp .env.example .env
   ```

3. **Start development server:**

   ```bash
   npm run dev
   ```

4. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000

## 🔑 Default Login Credentials

```
Username: admin
Password: admin123
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── Layout.tsx
│   │   ├── ProtectedRoute.tsx
│   │   └── ErrorBoundary.tsx
│   ├── pages/           # Page components
│   │   ├── LoginPage.tsx
│   │   └── DashboardPage.tsx
│   ├── context/         # React contexts
│   │   └── AuthContext.tsx
│   ├── services/        # API clients
│   │   └── api.ts
│   ├── types/           # TypeScript types
│   │   └── index.ts
│   ├── hooks/           # Custom React hooks
│   ├── utils/           # Utility functions
│   ├── App.tsx          # Root component
│   └── main.tsx         # Entry point
├── public/              # Static assets
├── .env.example         # Environment variables template
├── package.json
├── vite.config.ts       # Vite configuration
├── tailwind.config.js   # Tailwind configuration
└── tsconfig.json        # TypeScript configuration
```

## 🔧 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Lint code

## 🎨 Features

- ✅ JWT-based authentication
- ✅ Protected routes
- ✅ Responsive layout with sidebar navigation
- ✅ API integration with axios interceptors
- ✅ Error boundary for error handling
- ✅ Loading states
- ✅ Tailwind CSS styling

## 🔗 API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`. API calls are configured in `src/services/api.ts` with:

- Automatic JWT token injection
- Request/response interceptors
- Error handling
- 401 redirect to login

## 📱 Pages

- `/login` - Login page
- `/dashboard` - Main dashboard with metrics
- `/tasks` - Task management (coming soon)
- `/campaigns` - Email campaigns (coming soon)
- `/templates` - Email templates (coming soon)
- `/workers` - Worker management (coming soon)
- `/monitoring` - System monitoring (coming soon)
