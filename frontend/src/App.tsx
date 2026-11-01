import { lazy, Suspense } from 'react';
import type { ReactNode } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import AppLayout from './components/layout/AppLayout';
import { ThemeProvider } from './theme/ThemeContext';

const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const LiveAICTEData = lazy(() => import('./pages/LiveAICTEData'));
const ApplicationsList = lazy(() => import('./pages/ApplicationsList'));
const ApplicationDetail = lazy(() => import('./pages/ApplicationDetail'));
const NewApplication = lazy(() => import('./pages/NewApplication'));
const Documents = lazy(() => import('./pages/Documents'));
const EVCScheduling = lazy(() => import('./pages/EVCScheduling'));
const Compliance = lazy(() => import('./pages/Compliance'));
const LeaseExpiry = lazy(() => import('./pages/LeaseExpiry'));
const Notifications = lazy(() => import('./pages/Notifications'));
const Reports = lazy(() => import('./pages/Reports'));
const UserManagement = lazy(() => import('./pages/UserManagement'));
const WorkflowConfig = lazy(() => import('./pages/WorkflowConfig'));
const AuditLogs = lazy(() => import('./pages/AuditLogs'));
const Help = lazy(() => import('./pages/Help'));

function Page({ children }: { children: ReactNode }) {
  return <Suspense fallback={<div className="rounded-xl bg-white p-8 text-center text-slate-500">Loading page…</div>}>{children}</Suspense>;
}

function Protected({ children, roles }: { children: ReactNode; roles?: string[] }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-10 text-center text-slate-500">Loading NEXORA…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Page><Login /></Page>} />
      <Route path="/register" element={<Page><Register /></Page>} />
      <Route path="/" element={<Protected><AppLayout /></Protected>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Page><Dashboard /></Page>} />
        <Route path="aicte-data" element={<Page><LiveAICTEData /></Page>} />
        <Route path="applications" element={<Page><ApplicationsList /></Page>} />
        <Route path="applications/new" element={<Protected roles={['institution']}><Page><NewApplication /></Page></Protected>} />
        <Route path="applications/:id" element={<Page><ApplicationDetail /></Page>} />
        <Route path="documents" element={<Page><Documents /></Page>} />
        <Route path="evc" element={<Protected roles={['admin', 'regional_officer', 'bureau_officer', 'evc_committee']}><Page><EVCScheduling /></Page></Protected>} />
        <Route path="compliance" element={<Page><Compliance /></Page>} />
        <Route path="lease" element={<Page><LeaseExpiry /></Page>} />
        <Route path="notifications" element={<Page><Notifications /></Page>} />
        <Route path="reports" element={<Page><Reports /></Page>} />
        <Route path="users" element={<Protected roles={['admin']}><Page><UserManagement /></Page></Protected>} />
        <Route path="workflow" element={<Protected roles={['admin']}><Page><WorkflowConfig /></Page></Protected>} />
        <Route path="audit" element={<Protected roles={['admin', 'bureau_officer']}><Page><AuditLogs /></Page></Protected>} />
        <Route path="help" element={<Page><Help /></Page>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return <ThemeProvider><AuthProvider><AppRoutes /></AuthProvider></ThemeProvider>;
}
