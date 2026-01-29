import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import ErrorBoundary from "./components/ErrorBoundary";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
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
              <Route
                path="tasks"
                element={
                  <div className="text-2xl">Tasks Page - Coming Soon</div>
                }
              />
              <Route
                path="campaigns"
                element={
                  <div className="text-2xl">Campaigns Page - Coming Soon</div>
                }
              />
              <Route
                path="templates"
                element={
                  <div className="text-2xl">Templates Page - Coming Soon</div>
                }
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
