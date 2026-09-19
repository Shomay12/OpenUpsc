'use client';

import React, { useState, useEffect } from 'react';
import { Download, X, Smartphone, Monitor, CheckCircle2, Chrome, Sparkles } from 'lucide-react';

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

export default function InstallAppPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstallable, setIsInstallable] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [showBanner, setShowBanner] = useState(false);
  const [showGuideModal, setShowGuideModal] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Check if already running in standalone mode (installed)
    const isApp = window.matchMedia('(display-mode: standalone)').matches || 
                  (window.navigator as any).standalone === true;
    setIsStandalone(isApp);
    if (isApp) {
      setIsInstalled(true);
      return;
    }

    // Register Service Worker
    if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
      navigator.serviceWorker.register('/sw.js').catch((err) => {
        console.log('SW registration skipped:', err);
      });
    }

    // Detect iOS
    const userAgent = window.navigator.userAgent.toLowerCase();
    const isAppleDevice = /iphone|ipad|ipod/.test(userAgent);
    setIsIOS(isAppleDevice);

    // Listen for Chrome's beforeinstallprompt
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      setIsInstallable(true);
      
      // Auto show banner after 3 seconds if not dismissed previously
      const dismissed = localStorage.getItem('upsc_hub_pwa_dismissed');
      if (!dismissed) {
        const timer = setTimeout(() => setShowBanner(true), 2500);
        return () => clearTimeout(timer);
      }
    };

    const handleAppInstalled = () => {
      setIsInstalled(true);
      setIsInstallable(false);
      setShowBanner(false);
      setShowGuideModal(false);
      setDeferredPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const handleInstallClick = async () => {
    if (deferredPrompt) {
      // Trigger Chrome prompt
      deferredPrompt.prompt();
      const choiceResult = await deferredPrompt.userChoice;
      if (choiceResult.outcome === 'accepted') {
        setIsInstalled(true);
        setShowBanner(false);
      }
      setDeferredPrompt(null);
    } else {
      // Open guided modal for Chrome desktop / Safari iOS
      setShowGuideModal(true);
    }
  };

  const handleDismissBanner = () => {
    setShowBanner(false);
    localStorage.setItem('upsc_hub_pwa_dismissed', 'true');
  };

  if (isStandalone) {
    return null; // Already inside installed PWA
  }

  return (
    <>
      {/* Floating Bottom / Banner Prompt */}
      {showBanner && !isInstalled && (
        <div className="fixed bottom-20 sm:bottom-6 left-4 right-4 sm:left-auto sm:right-6 sm:max-w-sm z-50 animate-in fade-in slide-in-from-bottom-5 duration-300">
          <div className="bg-slate-900/95 backdrop-blur-xl text-white p-4 sm:p-4.5 rounded-3xl border border-white/10 shadow-2xl space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-white/10 flex items-center justify-center text-amber-300 shrink-0">
                  <Chrome className="w-5 h-5 text-sky-400" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-white tracking-tight flex items-center gap-1.5">
                    <span>Install OpenUPSC App</span>
                    <span className="px-1.5 py-0.5 rounded-md bg-sky-500/20 text-sky-300 text-[10px] font-mono">Chrome App</span>
                  </h4>
                  <p className="text-[11px] text-slate-300 line-clamp-1">
                    Instant 1-click access & offline focus timer.
                  </p>
                </div>
              </div>
              <button
                onClick={handleDismissBanner}
                className="text-slate-400 hover:text-white p-1 rounded-full hover:bg-white/10 transition-smooth"
                aria-label="Dismiss banner"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <button
                onClick={handleInstallClick}
                className="flex-1 py-2 px-3.5 rounded-full bg-white text-slate-900 hover:bg-slate-100 text-xs font-semibold flex items-center justify-center gap-1.5 shadow-sm transition-smooth"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Install on Chrome</span>
              </button>
              <button
                onClick={handleDismissBanner}
                className="py-2 px-3 rounded-full bg-white/5 hover:bg-white/10 text-[11px] text-slate-300 font-medium transition-smooth"
              >
                Maybe later
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Guide Modal for Manual or Alternate Browser Install */}
      {showGuideModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 sm:p-7 shadow-2xl border border-slate-200/80 space-y-6 relative">
            <button
              onClick={() => setShowGuideModal(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-slate-700 p-1.5 rounded-full hover:bg-slate-100"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center shrink-0">
                <Download className="w-5 h-5 text-sky-400" />
              </div>
              <div>
                <h3 className="font-display font-bold text-base text-slate-900">
                  Install OpenUPSC
                </h3>
                <p className="text-xs text-slate-500">
                  Use it like a native app on your desktop or phone
                </p>
              </div>
            </div>

            <div className="space-y-3.5 text-xs text-slate-600 font-sans">
              <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/60 space-y-2">
                <div className="flex items-center gap-2 font-semibold text-slate-800">
                  <Chrome className="w-4 h-4 text-sky-500" />
                  <span>Google Chrome (Desktop / Mac / Windows)</span>
                </div>
                <p className="text-slate-500 text-[11px] leading-relaxed">
                  Look at the right side of the address bar at the top of Chrome and click the <strong className="text-slate-800">“Install app”</strong> icon (or menu ⋮ → <em>Save and share</em> → <em>Install page as app</em>).
                </p>
              </div>

              {isIOS ? (
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/60 space-y-2">
                  <div className="flex items-center gap-2 font-semibold text-slate-800">
                    <Smartphone className="w-4 h-4 text-slate-700" />
                    <span>iPhone & iPad (Safari)</span>
                  </div>
                  <p className="text-slate-500 text-[11px] leading-relaxed">
                    Tap the <strong>Share</strong> button (box with upward arrow) at the bottom, scroll down, and tap <strong className="text-slate-800">“Add to Home Screen”</strong>.
                  </p>
                </div>
              ) : (
                <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/60 space-y-2">
                  <div className="flex items-center gap-2 font-semibold text-slate-800">
                    <Smartphone className="w-4 h-4 text-emerald-600" />
                    <span>Android (Chrome)</span>
                  </div>
                  <p className="text-slate-500 text-[11px] leading-relaxed">
                    Tap the <strong>three dots (⋮)</strong> menu in the top right of Chrome, and select <strong className="text-slate-800">“Install app”</strong> or <strong>“Add to Home screen”</strong>.
                  </p>
                </div>
              )}
            </div>

            <div className="pt-2">
              <button
                onClick={() => setShowGuideModal(false)}
                className="w-full py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-subtle transition-smooth"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export function InstallAppButton({ className = '' }: { className?: string }) {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
    };
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    return () => window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
  }, []);

  const handleClick = async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      setDeferredPrompt(null);
    } else {
      setShowModal(true);
    }
  };

  return (
    <>
      <button
        onClick={handleClick}
        className={className || "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-medium transition-smooth"}
        title="Download / Install Chrome App"
      >
        <Chrome className="w-3.5 h-3.5 text-sky-600" />
        <span>Install App</span>
      </button>

      {showModal && (
        <InstallAppPrompt />
      )}
    </>
  );
}
