import { Link, useLocation } from "wouter";
import { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";

interface NavItem {
  icon: LucideIcon;
  label: string;
  href: string;
}

interface SidebarProps {
  expanded: boolean;
  onHover: (expanded: boolean) => void;
  navItems: NavItem[];
}

export default function Sidebar({
  expanded,
  onHover,
  navItems,
}: SidebarProps) {
  const [location] = useLocation();
  const [isHovering, setIsHovering] = useState(false);

  const handleMouseEnter = () => {
    setIsHovering(true);
    onHover(true);
  };

  const handleMouseLeave = () => {
    setIsHovering(false);
    onHover(false);
  };

  return (
    <motion.div
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      animate={{ width: expanded ? 220 : 60 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className="bg-sidebar border-r border-sidebar-border flex flex-col h-screen overflow-hidden"
    >
      {/* Logo / Spider Icon */}
      <div className="h-16 flex items-center justify-center border-b border-sidebar-border">
        <motion.div
          animate={{ rotate: expanded ? 0 : 0 }}
          transition={{ duration: 0.3 }}
          className="relative"
        >
          <svg
            width={expanded ? 32 : 24}
            height={expanded ? 32 : 24}
            viewBox="0 0 32 32"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="text-sidebar-primary"
          >
            {/* Geometric Spider/Web Icon */}
            <circle cx="16" cy="16" r="4" fill="currentColor" />
            {/* Web lines */}
            <line
              x1="16"
              y1="16"
              x2="8"
              y2="8"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <line
              x1="16"
              y1="16"
              x2="24"
              y2="8"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <line
              x1="16"
              y1="16"
              x2="24"
              y2="24"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <line
              x1="16"
              y1="16"
              x2="8"
              y2="24"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <line
              x1="16"
              y1="16"
              x2="16"
              y2="4"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <line
              x1="16"
              y1="16"
              x2="28"
              y2="16"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <line
              x1="16"
              y1="16"
              x2="16"
              y2="28"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <line
              x1="16"
              y1="16"
              x2="4"
              y2="16"
              stroke="currentColor"
              strokeWidth="1.5"
            />
          </svg>
        </motion.div>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 flex flex-col gap-2 p-3 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = location === item.href;
          const Icon = item.icon;

          return (
            <Link key={item.href} href={item.href}>
              <motion.a
                className={`flex items-center gap-3 px-3 py-2 rounded-sm transition-all duration-200 ${
                  isActive
                    ? "bg-sidebar-primary text-sidebar-primary-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/20"
                }`}
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {expanded && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="text-sm font-mono font-500 whitespace-nowrap"
                  >
                    {item.label}
                  </motion.span>
                )}
              </motion.a>
            </Link>
          );
        })}
      </nav>

      {/* Footer Info */}
      {expanded && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="p-3 border-t border-sidebar-border text-xs text-sidebar-foreground/60 font-mono"
        >
          <div>v1.0.0</div>
          <div className="mt-1">Terminal Ready</div>
        </motion.div>
      )}
    </motion.div>
  );
}
