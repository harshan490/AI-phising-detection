import React from 'react';
import { Outlet } from 'react-router-dom';
import Topbar from './Topbar';

const Layout = () => {
  return (
    <div className="flex flex-col h-screen w-full bg-transparent overflow-hidden relative z-10">
      <Topbar />
      
      <main className="flex-1 overflow-y-auto p-8 scrollbar-hide relative z-10">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
