import { useEffect, useState } from "react";

const KEY = "mvrbac_theme"; // "light" | "dark" | "system"

function systemPrefersDark() {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

function apply(mode) {
  const dark = mode === "dark" || (mode === "system" && systemPrefersDark());
  document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
}

function readStored() {
  try {
    return localStorage.getItem(KEY) || "system";
  } catch {
    return "system";
  }
}

/** Setzt das Theme schon vor dem ersten Render, damit es nicht aufblitzt. */
export function initTheme() {
  apply(readStored());
}

export function useTheme() {
  const [mode, setMode] = useState(readStored);

  useEffect(() => {
    apply(mode);
    try {
      localStorage.setItem(KEY, mode);
    } catch {
      // Storage gesperrt (z.B. Private Mode) - Theme gilt dann nur fuer diese Sitzung
    }
    if (mode !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => apply("system");
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [mode]);

  return { mode, setMode };
}
