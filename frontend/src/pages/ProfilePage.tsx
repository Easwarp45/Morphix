/* =============================================================================
   Profile Page — User settings and account management
   ============================================================================= */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Lock, HardDrive, Shield, Save, Sparkles } from 'lucide-react';
import { useAuth } from '@/stores/auth-context';
import { authService } from '@/services/auth';
import { toast } from 'sonner';

export function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [firstName, setFirstName] = useState(user?.first_name || '');
  const [lastName, setLastName] = useState(user?.last_name || '');
  const [isSaving, setIsSaving] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await authService.updateProfile({ first_name: firstName, last_name: lastName } as Partial<typeof user> & { first_name: string; last_name: string });
      await refreshUser();
      toast.success('Profile updated!');
    } catch {
      toast.error('Failed to update profile.');
    } finally {
      setIsSaving(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      toast.error('New password must be at least 8 characters.');
      return;
    }
    setIsChangingPassword(true);
    try {
      await authService.changePassword(oldPassword, newPassword);
      setOldPassword('');
      setNewPassword('');
      toast.success('Password changed successfully!');
    } catch {
      toast.error('Failed to change password. Check your current password.');
    } finally {
      setIsChangingPassword(false);
    }
  };

  if (!user) return null;

  if (user.is_guest) {
    return (
      <div className="max-w-2xl">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-3xl font-bold mb-1">Guest Session</h1>
          <p className="text-[hsl(var(--muted-foreground))] mb-8">You are currently using a temporary guest session.</p>
        </motion.div>

        {/* Guest Warning Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="p-8 rounded-3xl bg-gradient-to-br from-primary-600/20 via-purple-600/20 to-pink-600/20 border border-primary-500/20 mb-6 text-center"
        >
          <div className="w-12 h-12 rounded-2xl bg-primary-500/10 flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-6 h-6 text-primary-400" />
          </div>
          <h2 className="text-xl font-bold mb-2">Upgrade to a Free Account</h2>
          <p className="text-sm text-[hsl(var(--muted-foreground))] mb-6 max-w-md mx-auto">
            Guest conversion is fully functional but restricted to a 10MB file limit and 1-hour file retention.
            Sign up for a free permanent account to increase your limits to 100MB per file and 24-hour file retention.
          </p>
          <Link
            to="/register"
            className="inline-flex items-center px-6 py-3 rounded-xl font-semibold bg-gradient-to-r from-primary-500 to-purple-600 text-white hover:opacity-90 transition-opacity shadow-lg shadow-primary-500/25"
          >
            Create Free Account
          </Link>
        </motion.div>

        {/* Storage */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="p-6 rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]"
        >
          <h3 className="font-semibold mb-4 flex items-center">
            <HardDrive className="w-5 h-5 mr-2 text-primary-500" /> Storage
          </h3>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm">{(user.storage_used / (1024 * 1024)).toFixed(1)} MB used</span>
            <span className="text-sm text-[hsl(var(--muted-foreground))]">{(user.storage_limit / (1024 * 1024)).toFixed(0)} MB limit</span>
          </div>
          <div className="w-full h-3 rounded-full bg-[hsl(var(--muted))] overflow-hidden">
            <div className="h-full rounded-full bg-gradient-to-r from-primary-500 to-purple-500" style={{ width: `${Math.min(user.storage_usage_percent, 100)}%` }} />
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold mb-1">Profile Settings</h1>
        <p className="text-[hsl(var(--muted-foreground))] mb-8">Manage your account and preferences</p>
      </motion.div>

      {/* Avatar & Info */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="p-6 rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] mb-6">
        <div className="flex items-center space-x-4 mb-6">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-2xl text-white font-bold">
            {user.first_name?.[0] || user.email[0].toUpperCase()}
          </div>
          <div>
            <h2 className="text-lg font-semibold">{user.full_name || user.email}</h2>
            <p className="text-sm text-[hsl(var(--muted-foreground))]">{user.email}</p>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-500/10 text-primary-500 mt-1">
              <Shield className="w-3 h-3 mr-1" />
              {user.auth_provider === 'google' ? 'Google Account' : 'Email Account'}
            </span>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1.5">First Name</label>
            <input type="text" value={firstName} onChange={e => setFirstName(e.target.value)} className="w-full px-4 py-2.5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--background))] focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors" id="profile-first-name" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Last Name</label>
            <input type="text" value={lastName} onChange={e => setLastName(e.target.value)} className="w-full px-4 py-2.5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--background))] focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors" id="profile-last-name" />
          </div>
        </div>

        <button onClick={handleSave} disabled={isSaving} className="mt-4 px-5 py-2.5 rounded-xl font-medium bg-gradient-to-r from-primary-500 to-purple-600 text-white hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center" id="profile-save">
          <Save className="w-4 h-4 mr-2" />
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
      </motion.div>

      {/* Storage */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="p-6 rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] mb-6">
        <h3 className="font-semibold mb-4 flex items-center">
          <HardDrive className="w-5 h-5 mr-2 text-primary-500" /> Storage
        </h3>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm">{(user.storage_used / (1024 * 1024)).toFixed(1)} MB used</span>
          <span className="text-sm text-[hsl(var(--muted-foreground))]">{(user.storage_limit / (1024 * 1024)).toFixed(0)} MB limit</span>
        </div>
        <div className="w-full h-3 rounded-full bg-[hsl(var(--muted))] overflow-hidden">
          <div className="h-full rounded-full bg-gradient-to-r from-primary-500 to-purple-500" style={{ width: `${Math.min(user.storage_usage_percent, 100)}%` }} />
        </div>
      </motion.div>

      {/* Change Password */}
      {user.auth_provider === 'email' && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="p-6 rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))]">
          <h3 className="font-semibold mb-4 flex items-center">
            <Lock className="w-5 h-5 mr-2 text-primary-500" /> Change Password
          </h3>
          <form onSubmit={handlePasswordChange} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">Current Password</label>
              <input type="password" value={oldPassword} onChange={e => setOldPassword(e.target.value)} className="w-full px-4 py-2.5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--background))] focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors" required id="current-password" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">New Password</label>
              <input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} className="w-full px-4 py-2.5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--background))] focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors" required id="new-password" />
            </div>
            <button type="submit" disabled={isChangingPassword} className="px-5 py-2.5 rounded-xl font-medium border border-[hsl(var(--border))] hover:bg-[hsl(var(--accent))] transition-colors disabled:opacity-50" id="change-password-btn">
              {isChangingPassword ? 'Changing...' : 'Change Password'}
            </button>
          </form>
        </motion.div>
      )}
    </div>
  );
}
