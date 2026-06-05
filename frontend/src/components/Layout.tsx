import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import KeyboardShortcuts from "./KeyboardShortcuts";
import SearchBar from "./SearchBar";

export default function Layout() {
  return (
    <div className="min-h-screen flex bg-[#0a0f1e] text-white">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-white/5 bg-[#0f172a] flex items-center px-4 pl-14 lg:pl-6 gap-4 z-40">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xs">N</span>
            </div>
            <span className="font-semibold text-sm hidden lg:inline">NexusMail</span>
          </div>
          <SearchBar />
        </header>
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-[#0a0f1e]">
          <Outlet />
        </main>
      </div>
      <KeyboardShortcuts />
    </div>
  );
}
