import { FC, ReactNode } from 'react';
import { Sidebar } from './Sidebar';

interface LayoutProps {
    children: ReactNode;
    title?: string;
}

export const Layout: FC<LayoutProps> = ({ children }) => {
    return (
        <div className="relative min-h-[100dvh] flex flex-col lg:flex-row bg-dark-bg text-dark-text-primary selection:bg-banana-400/30 selection:text-banana-400">
            {/* Fixed Background Layer */}
            <div
                className="fixed inset-0 z-0 pointer-events-none"
                style={{
                    backgroundImage: "url('/market-bg.png')",
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                    backgroundBlendMode: 'overlay',
                    opacity: 0.5
                }}
            />

            <Sidebar />

            <main className="relative z-10 flex-1 flex flex-col min-w-0 overflow-hidden pt-[60px] lg:pt-0 transition-all duration-300">
                <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-6 lg:p-8 scroll-smooth">
                    <div className="max-w-7xl mx-auto space-y-6 pb-20 lg:pb-0">
                        {children}

                        <footer className="mt-12 py-6 text-center border-t border-dark-border/30">
                            <p className="text-xs text-dark-text-muted">
                                Copyright © 2026 <span className="font-semibold text-dark-text-secondary">comgongStone - Grayson</span>. All rights reserved.
                            </p>
                        </footer>
                    </div>
                </div>
            </main>
        </div>
    );
};
