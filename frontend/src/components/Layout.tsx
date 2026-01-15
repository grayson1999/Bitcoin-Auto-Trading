import { FC, ReactNode } from 'react';
import { Sidebar } from './Sidebar';

interface LayoutProps {
    children: ReactNode;
    title?: string;
}

export const Layout: FC<LayoutProps> = ({ children }) => {
    return (
        <div className="min-h-screen flex bg-dark-bg text-dark-text-primary selection:bg-banana-400/30 selection:text-banana-400">
            <Sidebar />
            <main className="flex-1 flex flex-col min-w-0 overflow-hidden pt-16 lg:pt-0 transition-all duration-300">
                <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
                    <div className="max-w-7xl mx-auto space-y-6">
                        {children}
                    </div>
                </div>
            </main>
        </div>
    );
};
