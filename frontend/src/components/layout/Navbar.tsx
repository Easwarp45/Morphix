/* =============================================================================
   Navbar Component — Top navigation bar
   ============================================================================= */

import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Moon, Sun, Menu, X, LogOut, Zap } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/stores/auth-context';
import { useTheme } from '@/stores/theme-context';

export function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const { isDark, setTheme } = useTheme();
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="fixed top-0 left-0 right-0 z-50 glass"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center shadow-lg shadow-primary-500/25 group-hover:shadow-primary-500/40 transition-shadow">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">
              Cloud<span className="gradient-text">Convert</span>
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center space-x-1">
            {!isAuthenticated ? (
              <>
                <NavLink to="/" label="Home" />
                <button
                  onClick={() => setTheme(isDark ? 'light' : 'dark')}
                  className="p-2 rounded-lg hover:bg-[hsl(var(--accent))] transition-colors mx-2"
                  id="theme-toggle"
                >
                  {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>
                <Link
                  to="/login"
                  className="px-4 py-2 rounded-lg text-sm font-medium hover:bg-[hsl(var(--accent))] transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 rounded-xl text-sm font-medium bg-gradient-to-r from-primary-500 to-purple-600 text-white hover:opacity-90 transition-opacity shadow-lg shadow-primary-500/25"
                >
                  Get Started
                </Link>
              </>
            ) : (
              <>
                <NavLink to="/dashboard" label="Dashboard" />
                <NavLink to="/convert" label="Convert" />
                <NavLink to="/history" label="History" />
                <button
                  onClick={() => setTheme(isDark ? 'light' : 'dark')}
                  className="p-2 rounded-lg hover:bg-[hsl(var(--accent))] transition-colors mx-2"
                  id="theme-toggle-auth"
                >
                  {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>
                <Link
                  to="/profile"
                  className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-[hsl(var(--accent))] transition-colors"
                >
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-xs text-white font-bold">
                    {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase() || 'U'}
                  </div>
                </Link>
                <button
                  onClick={handleLogout}
                  className="p-2 rounded-lg hover:bg-red-500/10 hover:text-red-500 transition-colors"
                  id="logout-btn"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden p-2 rounded-lg hover:bg-[hsl(var(--accent))]"
            onClick={() => setMobileOpen(!mobileOpen)}
            id="mobile-menu-toggle"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="md:hidden glass border-t border-[hsl(var(--border))]"
        >
          <div className="px-4 py-3 space-y-2">
            {!isAuthenticated ? (
              <>
                <MobileLink to="/" label="Home" onClick={() => setMobileOpen(false)} />
                <MobileLink to="/login" label="Sign In" onClick={() => setMobileOpen(false)} />
                <MobileLink to="/register" label="Get Started" onClick={() => setMobileOpen(false)} />
              </>
            ) : (
              <>
                <MobileLink to="/dashboard" label="Dashboard" onClick={() => setMobileOpen(false)} />
                <MobileLink to="/convert" label="Convert" onClick={() => setMobileOpen(false)} />
                <MobileLink to="/history" label="History" onClick={() => setMobileOpen(false)} />
                <MobileLink to="/profile" label="Profile" onClick={() => setMobileOpen(false)} />
                <button onClick={handleLogout} className="w-full text-left px-3 py-2 rounded-lg text-red-500 hover:bg-red-500/10 transition-colors">
                  Logout
                </button>
              </>
            )}
          </div>
        </motion.div>
      )}
    </motion.nav>
  );
}

function NavLink({ to, label }: { to: string; label: string }) {
  return (
    <Link
      to={to}
      className="px-3 py-2 rounded-lg text-sm font-medium text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--accent))] transition-colors"
    >
      {label}
    </Link>
  );
}

function MobileLink({ to, label, onClick }: { to: string; label: string; onClick: () => void }) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className="block px-3 py-2 rounded-lg text-sm font-medium hover:bg-[hsl(var(--accent))] transition-colors"
    >
      {label}
    </Link>
  );
}
