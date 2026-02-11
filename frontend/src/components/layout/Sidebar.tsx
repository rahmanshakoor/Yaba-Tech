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
    <aside className="fixed left-0 top-0 h-screen w-56 bg-brand-black text-brand-white flex flex-col border-r border-brand-charcoal">
      <div className="px-6 py-6 border-b border-brand-charcoal">
        <img src="/logo-en.svg" alt="Yaba Tech" className="h-8 w-auto mb-1" />
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-bold transition-colors ${isActive
                ? 'bg-brand-yellow text-brand-black'
                : 'text-brand-white hover:bg-brand-charcoal hover:text-brand-yellow'
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
