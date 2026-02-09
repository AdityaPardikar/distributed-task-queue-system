import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { NotificationProvider } from "./context/NotificationContext";
import ProtectedRoute from "./components/ProtectedRoute";
import ErrorBoundary from "./components/ErrorBoundary";
import Layout from "./components/Layout";
import ToastContainer from "./components/ToastContainer";
import LoadingFallback from "./components/LoadingFallback";
import "./index.css";

// Lazy-loaded pages for code splitting and better performance
const LoginPage = lazy(() => import("./pages/LoginPage"));
const RegisterPage = lazy(() => import("./pages/RegisterPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const TasksPage = lazy(() => import("./pages/TasksPage"));
const AnalyticsDashboard = lazy(() => import("./pages/AnalyticsDashboard"));

// Campaign pages - lazy loaded
const CampaignListPage = lazy(() =>
  import("./pages/CampaignListPage").then((module) => ({
    default: module.CampaignListPage,
  })),
);
const CreateCampaignPage = lazy(() =>
  import("./pages/CreateCampaignPage").then((module) => ({
    default: module.CreateCampaignPage,
  })),
);
const CampaignDetailPage = lazy(() =>
  import("./pages/CampaignDetailPage").then((module) => ({
    default: module.CampaignDetailPage,
  })),
);

// Template pages - lazy loaded
const TemplateListPage = lazy(() =>
  import("./pages/TemplateListPage").then((module) => ({
    default: module.TemplateListPage,
  })),
);
const CreateTemplatePage = lazy(() =>
  import("./pages/CreateTemplatePage").then((module) => ({
    default: module.CreateTemplatePage,
  })),
);

function App() {
  return (
    <ErrorBoundary>
      <NotificationProvider>
        <AuthProvider>
          <BrowserRouter>
            <Suspense fallback={<LoadingFallback message="Loading..." />}>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />

                <Route
                  path="/*"
                  element={
                    <ProtectedRoute>
                      <Layout />
                    </ProtectedRoute>
                  }
                >
                  <Route path="dashboard" element={<DashboardPage />} />
                  <Route path="tasks" element={<TasksPage />} />
                  <Route path="analytics" element={<AnalyticsDashboard />} />

                  {/* Campaign Routes */}
                  <Route path="campaigns" element={<CampaignListPage />} />
                  <Route
                    path="campaigns/new"
                    element={<CreateCampaignPage />}
                  />
                  <Route
                    path="campaigns/:id"
                    element={<CampaignDetailPage />}
                  />

                  {/* Template Routes */}
                  <Route path="templates" element={<TemplateListPage />} />
                  <Route
                    path="templates/new"
                    element={<CreateTemplatePage />}
                  />
                  <Route
                    path="templates/:id"
                    element={<CreateTemplatePage />}
                  />

                  <Route
                    path="workers"
                    element={
                      <div className="text-2xl">Workers Page - Coming Soon</div>
                    }
                  />
                  <Route
                    path="monitoring"
                    element={
                      <div className="text-2xl">
                        Monitoring Page - Coming Soon
                      </div>
                    }
                  />
                  <Route
                    path=""
                    element={<Navigate to="/dashboard" replace />}
                  />
                </Route>

                <Route
                  path="*"
                  element={<Navigate to="/dashboard" replace />}
                />
              </Routes>
            </Suspense>
          </BrowserRouter>
          <ToastContainer />
        </AuthProvider>
      </NotificationProvider>
    </ErrorBoundary>
  );
}

export default App;
