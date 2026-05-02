import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { PermissionResource, PermissionAction, PermissionScope } from '../types/domain';
import { Lock } from 'lucide-react';
import { motion } from 'motion/react';

interface PermissionGuardProps {
  children: React.ReactNode;
  resource: PermissionResource;
  action: PermissionAction;
  scope?: PermissionScope;
  fallback?: React.ReactNode;
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({ 
  children, 
  resource, 
  action, 
  scope,
  fallback 
}) => {
  const { profile } = useAuth();

  // Basic RBAC mapping for the frontend
  const hasAccess = () => {
    if (!profile) return false;
    if (profile.role === 'master_admin') return true;

    // Custom logic per role (This would ideally be synced from a central policy engine)
    const rolePermissions: Record<string, string[]> = {
      'ministry_admin': ['patient:read:global', 'lab_result:read:global', 'audit_log:read:global'],
      'ministry_analyst': ['lab_result:read:global', 'research:read:global'],
      'pathologist': ['lab_result:validate:entity', 'lab_result:read:entity'],
      'technician': ['lab_test:update:assigned', 'sample:process:entity'],
      'physician': ['patient:read:assigned', 'lab_result:read:assigned'],
      'citizen': ['patient:read:own', 'consent:manage:own']
    };

    const userPerms = rolePermissions[profile.role] || [];
    
    // Check if any of the user's permissions match the requested resource/action
    // Format: resource:action:scope
    const match = userPerms.some(p => {
      const [r, a, s] = p.split(':');
      return r === resource && a === action && (!scope || s === scope || s === 'global');
    });

    return match;
  };

  if (!hasAccess()) {
    return fallback || (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="p-8 rounded-3xl bg-slate-50 border border-dashed border-slate-200 text-center space-y-4"
      >
        <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center mx-auto shadow-sm border border-slate-100">
           <Lock size={20} className="text-slate-300" />
        </div>
        <div>
           <h3 className="text-sm font-black text-slate-900 uppercase tracking-widest">Access Restricted</h3>
           <p className="text-[10px] text-slate-400 font-medium mt-1">Your current credentials lack the clearance for this node.</p>
        </div>
      </motion.div>
    );
  }

  return <>{children}</>;
};
