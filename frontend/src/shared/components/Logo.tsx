// Ícone da marca "Escola Sem Barreiras" — mesmo desenho do protótipo de referência: quadrado
// arredondado teal, arco branco (abrigo/inclusão) e uma silhueta de pessoa em laranja-coral.
export function Logo({ size = 42 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 44 44"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Escola Sem Barreiras"
      className="flex-none"
    >
      <rect width="44" height="44" rx="13" fill="#0e7c6b" />
      <path
        d="M11 36 L11 19 A11 11 0 0 1 33 19 L33 36"
        stroke="#ffffff"
        strokeWidth="4.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <circle cx="22" cy="19.5" r="3.3" fill="#e5533c" />
      <rect x="18.4" y="23.8" width="7.2" height="12.2" rx="3.6" fill="#e5533c" />
    </svg>
  );
}
