import { FC, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    HomeIcon,
    CurrencyDollarIcon,
    ChartBarIcon,
    Cog6ToothIcon,
    Bars3Icon,
    XMarkIcon,
    BeakerIcon,
    ArrowRightStartOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';

const navItems = [
    { path: '/', label: '대시보드', icon: HomeIcon },
    { path: '/orders', label: '주문 내역', icon: CurrencyDollarIcon },
    { path: '/signals', label: 'AI 신호', icon: ChartBarIcon },
    { path: '/backtest', label: '백테스트', icon: BeakerIcon },
    { path: '/settings', label: '설정', icon: Cog6ToothIcon },
];

/**
 * 사용자 이름에서 아바타 이니셜을 생성
 * - 이름이 공백으로 구분된 경우: 각 단어의 첫 글자 (최대 2글자)
 * - 단일 단어인 경우: 첫 글자
 * - 이름이 없는 경우: "?"
 */
function getInitials(name: string | undefined | null): string {
    if (!name?.trim()) return '?';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) {
        return parts[0].charAt(0).toUpperCase();
    }
    return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

export const Sidebar: FC = () => {
    const location = useLocation();
    const [isOpen, setIsOpen] = useState(false);
    const { user, logout } = useAuth();

    const handleLogout = async () => {
        setIsOpen(false);
        await logout();
    };

    return (
        <>
            {/* Mobile Header */}
            <div className="lg:hidden fixed top-0 left-0 right-0 h-[60px] z-30 bg-dark-bg/80 backdrop-blur-xl border-b border-dark-border px-4 flex items-center justify-between transition-all duration-300">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-banana-400 to-orange-500 flex items-center justify-center shadow-lg shadow-banana-500/20">
                        <span className="text-white font-bold text-lg">A</span>
                    </div>
                    <span className="text-xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                        AutoBitcoin
                    </span>
                </div>
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="p-2 -mr-2 text-dark-text-secondary hover:text-white active:scale-95 transition-all"
                    aria-label="Menu"
                >
                    {isOpen ? <XMarkIcon className="w-6 h-6" /> : <Bars3Icon className="w-6 h-6" />}
                </button>
            </div>

            {/* Sidebar Drawer */}
            <aside className={`
                fixed inset-y-0 left-0 z-40 w-[280px] bg-dark-surface/95 backdrop-blur-2xl border-r border-dark-border 
                transform transition-all duration-300 ease-[cubic-bezier(0.33,1,0.68,1)]
                lg:translate-x-0 lg:static lg:inset-0 lg:w-64 lg:bg-dark-surface lg:backdrop-blur-none
                ${isOpen ? 'translate-x-0 shadow-2xl shadow-black/50' : '-translate-x-full'}
            `}>
                <div className="h-full flex flex-col">
                    {/* Logo Section (Desktop) */}
                    <div className="hidden lg:flex h-20 items-center px-6">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-banana-400 to-orange-500 flex items-center justify-center shadow-lg shadow-banana-500/20">
                                <span className="text-white font-bold text-lg">A</span>
                            </div>
                            <span className="text-xl font-bold tracking-tight text-white/90">
                                AutoBitcoin
                            </span>
                        </div>
                    </div>

                    {/* Mobile Menu Header */}
                    <div className="lg:hidden h-[60px] flex items-center px-6 border-b border-dark-border/50">
                        <span className="text-sm font-medium text-dark-text-muted">MENU</span>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-3 py-6 space-y-1 overflow-y-auto">
                        {navItems.map((item) => {
                            const isActive = location.pathname === item.path;
                            const Icon = item.icon;
                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    onClick={() => setIsOpen(false)}
                                    className={`
                                        group flex items-center gap-3 px-3 py-3 text-sm font-medium rounded-xl transition-all duration-200
                                        ${isActive
                                            ? 'bg-gradient-to-r from-banana-500/10 to-transparent text-banana-400 border-l-2 border-banana-400'
                                            : 'text-dark-text-secondary hover:text-white hover:bg-white/5 border-l-2 border-transparent'
                                        }
                                    `}
                                >
                                    <Icon className={`w-5 h-5 transition-colors ${isActive ? 'text-banana-400' : 'text-slate-500 group-hover:text-white'}`} />
                                    {item.label}
                                </Link>
                            );
                        })}
                    </nav>

                    {/* User Profile */}
                    <div className="p-4 border-t border-dark-border/50">
                        <div className="flex items-center gap-3 px-3 py-3 rounded-xl bg-gradient-to-br from-white/5 to-white/0 hover:from-white/10 hover:to-white/5 border border-white/5 hover:border-white/10 transition-all cursor-pointer group mb-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-sm shadow-inner ring-2 ring-black/50 group-hover:ring-white/20 transition-all">
                                {getInitials(user?.name)}
                            </div>
                            <div className="flex flex-col flex-1 min-w-0">
                                <span className="text-sm font-semibold text-white truncate">{user?.name ?? '사용자'}</span>
                                <span className="text-xs text-dark-text-secondary group-hover:text-emerald-400 transition-colors font-medium truncate">{user?.email ?? ''}</span>
                            </div>
                            <Cog6ToothIcon className="w-5 h-5 text-dark-text-muted group-hover:text-white transition-colors" />
                        </div>

                        {/* Logout Button */}
                        <button
                            onClick={handleLogout}
                            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-xs font-medium text-dark-text-secondary hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all duration-200 group"
                        >
                            <ArrowRightStartOnRectangleIcon className="w-4 h-4 text-dark-text-muted group-hover:text-red-400 transition-colors" />
                            <span>로그아웃</span>
                        </button>
                    </div>
                </div>
            </aside>

            {/* Overlay for mobile */}
            <div
                className={`
                    fixed inset-0 bg-black/60 backdrop-blur-sm z-30 lg:hidden transition-opacity duration-300
                    ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}
                `}
                onClick={() => setIsOpen(false)}
                aria-hidden="true"
            />
        </>
    );
};
