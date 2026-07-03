"use client";

// Componente do Design System Gov.br — ver interface.md §6.1 "Modal de Detalhamento".

type ModalProps = {
  titulo: string;
  subtitulo?: string;
  onFechar: () => void;
  children: React.ReactNode;
};

export function Modal({ titulo, subtitulo, onFechar, children }: ModalProps) {
  return (
    <div
      className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/50 p-4"
      onClick={onFechar}
    >
      <div
        className="max-h-[82vh] w-full max-w-lg overflow-y-auto rounded bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between rounded-t bg-gov-blue-dark px-5 py-4">
          <div>
            <div className="text-[15px] font-bold text-white">{titulo}</div>
            {subtitulo && <div className="mt-0.5 text-[11px] text-white/55">{subtitulo}</div>}
          </div>
          <button onClick={onFechar} className="text-xl leading-none text-white/65 hover:text-white">
            ✕
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}
