import {
  Activity, Bell, BookOpen, Building2, ChevronDown, ChevronLeft, ChevronRight,
  ClipboardList, Command, FileBarChart2, FileCheck2, Gauge, HelpCircle, Globe2,
  Landmark, LogOut, Menu, Moon, Search, Settings2, ShieldCheck, Sun, Users, X,
} from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { apiGet } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { useTheme } from '../../theme/ThemeContext';

const groups = [
  { label: 'OVERVIEW', links: [
    { to: '/dashboard', label: 'Dashboard', icon: Gauge, roles: null },
    { to: '/aicte-data', label: 'AICTE public data', icon: Globe2, roles: null },
  ] },
  { label: 'APPLICATION MANAGEMENT', links: [
    { to: '/applications', label: 'All applications', icon: ClipboardList, roles: null },
    { to: '/applications/new', label: 'New application', icon: Building2, roles: ['institution'] },
    { to: '/documents', label: 'Document review', icon: FileCheck2, roles: null },
  ] },
  { label: 'COMPLIANCE', links: [
    { to: '/compliance', label: 'Compliance monitoring', icon: ShieldCheck, roles: null },
    { to: '/lease', label: 'Lease management', icon: Landmark, roles: null },
  ] },
  { label: 'OPERATIONS', links: [
    { to: '/evc', label: 'EVC scheduling', icon: Building2, roles: ['admin', 'regional_officer', 'bureau_officer', 'evc_committee'] },
    { to: '/notifications', label: 'Notifications', icon: Bell, roles: null },
  ] },
  { label: 'ANALYTICS', links: [
    { to: '/reports', label: 'Reports & analytics', icon: FileBarChart2, roles: null },
  ] },
  { label: 'SYSTEM', links: [
    { to: '/users', label: 'User management', icon: Users, roles: ['admin'] },
    { to: '/workflow', label: 'Workflow configuration', icon: Settings2, roles: ['admin'] },
    { to: '/audit', label: 'Audit logs', icon: Activity, roles: ['admin', 'bureau_officer'] },
    { to: '/help', label: 'Help & system info', icon: HelpCircle, roles: null },
  ] },
];

function roleTitle(role = '') {
  return role.split('_').map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(' ');
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const [unread, setUnread] = useState(0);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [search, setSearch] = useState('');
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const profileRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const refresh = () => apiGet<{ count: number }>('/notifications/unread-count')
      .then((value) => setUnread(value.count))
      .catch(() => setUnread(0));
    const updateListener = () => { void refresh(); };
    void refresh();
    window.addEventListener('nexora-notifications-updated', updateListener);
    return () => window.removeEventListener('nexora-notifications-updated', updateListener);
  }, [location.pathname]);

  useEffect(() => {
    setMobileNavOpen(false);
    setProfileOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) setProfileOpen(false);
    };
    document.addEventListener('mousedown', closeOnOutsideClick);
    return () => document.removeEventListener('mousedown', closeOnOutsideClick);
  }, []);

  useEffect(() => {
    const focusSearch = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        searchRef.current?.focus();
      }
    };
    document.addEventListener('keydown', focusSearch);
    return () => document.removeEventListener('keydown', focusSearch);
  }, []);

  const allowedGroups = useMemo(() => groups.map((group) => ({
    ...group,
    links: group.links.filter((item) => !item.roles || (user && item.roles.includes(user.role))),
  })).filter((group) => group.links.length > 0), [user]);
  const currentLabel = groups.flatMap((group) => group.links)
    .find((item) => location.pathname === item.to || location.pathname.startsWith(`${item.to}/`))?.label ?? 'Workspace';

  function submitSearch(event: React.FormEvent) {
    event.preventDefault();
    const value = search.trim();
    navigate(value ? `/applications?search=${encodeURIComponent(value)}` : '/applications');
  }

  function renderNavigation(mobile = false) {
    return allowedGroups.map((group) => (
      <section key={group.label} className="mb-5">
        {!collapsed || mobile ? <h2 className="mb-2 px-3 text-[10px] font-bold tracking-[.13em] text-slate-400">{group.label}</h2> : <div className="mx-3 mb-2 border-t border-slate-100" />}
        <div className="space-y-0.5">
          {group.links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              title={collapsed && !mobile ? label : undefined}
              onClick={() => setMobileNavOpen(false)}
              className={({ isActive }) => `workspace-nav-link group flex min-h-10 items-center gap-3 rounded-xl px-3 text-[13px] font-medium transition-colors ${collapsed && !mobile ? 'justify-center px-2' : ''} ${isActive ? 'is-active' : ''}`}
            >
              <span className="relative flex h-5 w-5 shrink-0 items-center justify-center">
                <Icon size={17} strokeWidth={1.8} />
              </span>
              {(!collapsed || mobile) && <span className="truncate">{label}</span>}
            </NavLink>
          ))}
        </div>
      </section>
    ));
  }

  return (
    <div className="workspace-frame min-h-screen text-slate-800">
      <aside className={`workspace-sidebar fixed inset-y-0 left-0 z-30 hidden flex-col transition-[width] duration-200 md:flex ${collapsed ? 'w-[76px]' : 'w-[256px]'}`}>
        <Link to="/dashboard" className={`workspace-brand flex h-[82px] items-center ${collapsed ? 'justify-center px-3' : 'gap-3 px-5'}`}>
          <span className="workspace-mark flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-white shadow-sm">
            <Landmark size={21} strokeWidth={1.8} />
          </span>
          {!collapsed && <span className="min-w-0"><span className="workspace-brand-title block text-[15px] font-bold tracking-tight">NEXORA <span className="font-medium">AICTE</span></span><span className="workspace-brand-subtitle mt-0.5 block text-[10px] font-medium">Approval &amp; Compliance Intelligence</span></span>}
        </Link>
        <div className="flex-1 overflow-y-auto px-3 py-5">{renderNavigation()}</div>
        <div className="workspace-profile-wrap p-3">
          <div className={`workspace-profile mb-3 flex items-center rounded-xl p-2 ${collapsed ? 'justify-center' : 'gap-3'}`}>
            <span className="workspace-avatar flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold">{user?.full_name.split(' ').map((part) => part[0]).slice(0, 2).join('')}</span>
            {!collapsed && <span className="min-w-0"><span className="workspace-profile-name block truncate text-xs font-semibold">{user?.full_name}</span><span className="workspace-profile-role block truncate text-[10px]">{roleTitle(user?.role)}</span></span>}
          </div>
          <button onClick={() => setCollapsed((value) => !value)} className="workspace-collapse flex h-9 w-full items-center justify-center rounded-lg transition" aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
            {collapsed ? <ChevronRight size={17} /> : <span className="flex items-center gap-2 text-xs"><ChevronLeft size={16} />Collapse sidebar</span>}
          </button>
        </div>
      </aside>

      <div className={`min-h-screen transition-[padding] duration-200 ${collapsed ? 'md:pl-[76px]' : 'md:pl-[256px]'}`}>
        <header className="workspace-topbar sticky top-0 z-20 flex h-[68px] items-center justify-between px-4 backdrop-blur md:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <button onClick={() => setMobileNavOpen(true)} className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 md:hidden" aria-label="Open navigation"><Menu size={20} /></button>
            <Link to="/dashboard" className="flex items-center gap-2 md:hidden">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-navy text-white"><Landmark size={17} /></span>
              <span className="text-sm font-bold text-brand-navy">NEXORA <span className="font-medium">AICTE</span></span>
            </Link>
            <div className="hidden items-center gap-2 text-xs sm:flex">
              <span className="workspace-breadcrumb-muted">Workspace</span><span className="workspace-breadcrumb-separator">/</span><span className="workspace-breadcrumb-current font-semibold">{currentLabel}</span>
            </div>
          </div>
          <div className="flex items-center gap-1.5 sm:gap-3">
            <form onSubmit={submitSearch} className="relative hidden lg:block">
              <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input ref={searchRef} aria-label="Search applications" placeholder="Search applications..." value={search} onChange={(event) => setSearch(event.target.value)} className="h-9 w-56 rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-12 text-xs outline-none transition focus:border-blue-300 focus:bg-white focus:ring-2 focus:ring-blue-100" />
              <span className="absolute right-2 top-1/2 -translate-y-1/2 rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[9px] text-slate-400"><Command size={10} className="inline" /> K</span>
            </form>
            <button
              type="button"
              aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
              aria-pressed={theme === 'dark'}
              title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
              onClick={toggleTheme}
              className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-brand-navy"
            >
              {theme === 'dark' ? <Sun size={18} strokeWidth={1.8} /> : <Moon size={18} strokeWidth={1.8} />}
            </button>
            <Link to="/help" aria-label="Help and support" className="hidden rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-brand-navy sm:inline-flex"><BookOpen size={18} strokeWidth={1.8} /></Link>
            <Link to="/notifications" aria-label="Notifications" className="relative rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-brand-navy">
              <Bell size={18} strokeWidth={1.8} />
              {unread > 0 && <span className="absolute right-1 top-1 h-2 w-2 rounded-full border-2 border-white bg-rose-500" />}
            </Link>
            <div className="relative" ref={profileRef}>
              <button onClick={() => setProfileOpen((open) => !open)} aria-expanded={profileOpen} className="flex items-center gap-2 rounded-lg py-1 pl-1.5 pr-1 text-left transition hover:bg-slate-50">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-[11px] font-bold text-brand-navy">{user?.full_name.split(' ').map((part) => part[0]).slice(0, 2).join('')}</span>
                <span className="hidden max-w-32 sm:block"><span className="block truncate text-xs font-semibold text-slate-800">{user?.full_name}</span><span className="block text-[10px] capitalize text-slate-500">{roleTitle(user?.role)}</span></span>
                <ChevronDown size={14} className="hidden text-slate-400 sm:block" />
              </button>
              {profileOpen && <div className="absolute right-0 top-12 z-30 w-56 rounded-xl border border-slate-200 bg-white p-2 shadow-xl">
                <div className="border-b border-slate-100 px-3 py-2"><p className="truncate text-xs font-semibold">{user?.full_name}</p><p className="truncate text-[11px] text-slate-500">{user?.email}</p></div>
                <Link to="/help" onClick={() => setProfileOpen(false)} className="mt-1 flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-slate-600 hover:bg-slate-50"><HelpCircle size={15} />Help &amp; support</Link>
                {user?.role === 'admin' && <Link to="/users" onClick={() => setProfileOpen(false)} className="flex items-center gap-2 rounded-lg px-3 py-2 text-xs text-slate-600 hover:bg-slate-50"><Settings2 size={15} />Administration</Link>}
                <button onClick={logout} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs text-rose-600 hover:bg-rose-50"><LogOut size={15} />Sign out</button>
              </div>}
            </div>
          </div>
        </header>
        <main className="workspace-content mx-auto max-w-[1680px] px-4 py-6 md:px-8 md:py-8"><Outlet /></main>
      </div>

      {mobileNavOpen && <>
        <button className="fixed inset-0 z-40 bg-slate-950/40 md:hidden" onClick={() => setMobileNavOpen(false)} aria-label="Close navigation" />
        <aside className="workspace-sidebar fixed inset-y-0 left-0 z-50 flex w-[min(84vw,300px)] flex-col shadow-xl md:hidden">
          <div className="workspace-brand flex h-[68px] items-center justify-between px-4">
            <Link to="/dashboard" onClick={() => setMobileNavOpen(false)} className="flex items-center gap-3"><span className="workspace-mark flex h-9 w-9 items-center justify-center rounded-lg text-white"><Landmark size={19} /></span><span><b className="workspace-brand-title block text-sm">NEXORA AICTE</b><span className="workspace-brand-subtitle text-[10px]">Approval &amp; Compliance Intelligence</span></span></Link>
            <button onClick={() => setMobileNavOpen(false)} aria-label="Close navigation" className="workspace-collapse rounded-lg p-2"><X size={18} /></button>
          </div>
          <div className="flex-1 overflow-y-auto px-3 py-5">{renderNavigation(true)}</div>
          <div className="workspace-mobile-footer border-t p-4 text-[10px]">Fictional demo environment · v1.0</div>
        </aside>
      </>}
    </div>
  );
}
