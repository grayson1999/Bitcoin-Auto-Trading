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
} from '@heroicons/react/24/outline';

const navItems = [
    { path: '/', label: '대시보드', icon: HomeIcon },
    { path: '/orders', label: '주문 내역', icon: CurrencyDollarIcon },
    { path: '/signals', label: 'AI 신호', icon: ChartBarIcon },
    { path: '/backtest', label: '백테스트', icon: BeakerIcon },
    { path: '/settings', label: '설정', icon: Cog6ToothIcon },
];

export const Sidebar: FC = () => {
    const location = useLocation();
    const [isOpen, setIsOpen] = useState(false);

    return (
        <>
            <div className="lg:hidden fixed top-0 left-0 w-full z-20 bg-dark-surface/80 backdrop-blur-md border-b border-dark-border px-4 py-3 flex items-center justify-between">
                <div className="text-xl font-bold bg-gradient-to-r from-banana-400 to-banana-600 bg-clip-text text-transparent text-glow">
                    NanoBit
                </div>
                <button onClick={() => setIsOpen(!isOpen)} className="p-2 text-dark-text-secondary hover:text-white hover:bg-white/5 rounded-md transition-colors">
                    {isOpen ? <XMarkIcon className="w-6 h-6" /> : <Bars3Icon className="w-6 h-6" />}
                </button>
            </div>

            <aside className={`
        fixed inset-y-0 left-0 z-10 w-64 bg-dark-surface border-r border-dark-border transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
                <div className="h-full flex flex-col">
                    <div className="flex h-16 items-center px-6 mt-16 lg:mt-0">
                        <span className="text-2xl font-bold tracking-tight bg-gradient-to-r from-banana-400 to-banana-600 bg-clip-text text-transparent text-glow">
                            NanoBit
                        </span>
                    </div>

                    <nav className="flex-1 px-4 space-y-2 py-4">
                        {navItems.map((item) => {
                            const isActive = location.pathname === item.path;
                            const Icon = item.icon;
                            return (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    onClick={() => setIsOpen(false)}
                                    className={`flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${isActive
                                        ? 'bg-banana-500/10 text-banana-400 shadow-[0_0_15px_rgba(250,204,21,0.3)] border border-banana-500/20'
                                        : 'text-dark-text-secondary hover:text-white hover:bg-white/5'
                                        }`}
                                >
                                    <Icon className={`w-5 h-5 ${isActive ? 'text-banana-400' : 'text-slate-500 group-hover:text-white'}`} />
                                    {item.label}
                                </Link>
                            );
                        })}
                    </nav>

                    <div className="p-4 border-t border-dark-border">
                        <div className="flex items-center gap-3 px-4 py-2 bg-white/5 rounded-xl border border-white/5">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-banana-500 to-orange-500 flex items-center justify-center text-white font-bold text-xs shadow-lg">
                                G
                            </div>
                            <div className="flex flex-col">
                                <span className="text-sm font-medium text-white">Grayson</span>
                                <span className="text-xs text-banana-400">프로 플랜</span>
                            </div>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Overlay for mobile */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-0 lg:hidden"
                    onClick={() => setIsOpen(false)}
                />
            )}
        </>
    );
};
