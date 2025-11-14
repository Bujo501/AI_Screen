// filepath: tailwind.config.js  <-- keep/replace with this (root)
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: { primary: { DEFAULT: "#2563eb" } },
      boxShadow: { soft: "0 1px 2px rgba(0,0,0,.04),0 8px 24px rgba(0,0,0,.08)" },
      borderRadius: { xl2: "1rem" },
    },
  },
  plugins: [],
};
