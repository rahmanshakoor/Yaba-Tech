import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BookOpen,
  Package,

  Factory,
  FileText,
} from 'lucide-react';

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/definitions', label: 'Definitions', icon: BookOpen },
  { to: '/inventory', label: 'Inventory', icon: Package },
  //  { to: '/recipes', label: 'Recipes', icon: ChefHat },
  { to: '/production', label: 'Production', icon: Factory },
  { to: '/invoices', label: 'Invoices', icon: FileText },
];

export default function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-screen w-56 bg-gray-900 text-gray-300 flex flex-col">
      <div className="px-6 py-5 border-b border-gray-700">
        <h1 className="text-xl font-bold text-white tracking-wide">YABA</h1>
        <p className="text-xs text-gray-500 mt-0.5">Kitchen Management</p>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${isActive
                ? 'bg-indigo-600 text-white'
                : 'hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
