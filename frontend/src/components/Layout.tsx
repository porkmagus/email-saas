import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import KeyboardShortcuts from "./KeyboardShortcuts";
import SearchBar from "./SearchBar";

export default function Layout() {
  return (
    <div className="min-h-screen flex">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-border bg-surface flex items-center px-4 pl-14 lg:pl-6 gap-4 z-40">
          <span className="font-semibold text-sm hidden lg:inline">Email SaaS</span>
          <SearchBar />
        </header>
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
      <KeyboardShortcuts />
    </div>
  );
}
