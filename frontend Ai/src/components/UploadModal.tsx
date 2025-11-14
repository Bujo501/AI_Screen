
// ===========================================
// filepath: src/components/UploadModal.tsx
// ===========================================
import React from "react";

type Props = { open: boolean; onClose: () => void; children: React.ReactNode };

export default function UploadModal({ open, onClose, children }: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-xl p-5 relative">
        <button className="absolute right-3 top-3 px-2 py-1 rounded border" onClick={onClose}>Close</button>
        {children}
      </div>
    </div>
  );
}
