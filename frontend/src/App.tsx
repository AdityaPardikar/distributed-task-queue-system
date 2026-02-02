import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import ErrorBoundary from "./components/ErrorBoundary";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import TasksPage from "./pages/TasksPage";
import { CampaignListPage } from "./pages/CampaignListPage";
import { CreateCampaignPage } from "./pages/CreateCampaignPage";
import { CampaignDetailPage } from "./pages/CampaignDetailPage";
import { TemplateListPage } from "./pages/TemplateListPage";
import { CreateTemplatePage } from "./pages/CreateTemplatePage";
import "./index.css";

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />

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

              {/* Campaign Routes */}
              <Route path="campaigns" element={<CampaignListPage />} />
              <Route path="campaigns/new" element={<CreateCampaignPage />} />
              <Route path="campaigns/:id" element={<CampaignDetailPage />} />

              {/* Template Routes */}
              <Route path="templates" element={<TemplateListPage />} />
              <Route path="templates/new" element={<CreateTemplatePage />} />
              <Route path="templates/:id" element={<CreateTemplatePage />} />

              <Route
                path="workers"
                element={
                  <div className="text-2xl">Workers Page - Coming Soon</div>
                }
              />
              <Route
                path="monitoring"
                element={
                  <div className="text-2xl">Monitoring Page - Coming Soon</div>
                }
              />
              <Route path="" element={<Navigate to="/dashboard" replace />} />
            </Route>

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
