import { useState, useEffect, useCallback } from 'react'

type Theme = 'light' | 'dark'

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'dark'
    const stored = localStorage.getItem('gula_radiology_theme')
    if (stored === 'light' || stored === 'dark') return stored
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  const [dir, setDir] = useState<'rtl' | 'ltr'>('rtl')

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t)
    localStorage.setItem('gula_radiology_theme', t)
    document.documentElement.setAttribute('data-theme', t)
  }, [])

  const toggleTheme = useCallback(() => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }, [theme, setTheme])

  const toggleDir = useCallback(() => {
    const newDir = dir === 'rtl' ? 'ltr' : 'rtl'
    setDir(newDir)
    document.documentElement.dir = newDir
    localStorage.setItem('gula_radiology_dir', newDir)
  }, [dir])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    document.documentElement.dir = dir

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem('gula_radiology_theme')) {
        setTheme(e.matches ? 'dark' : 'light')
      }
    }
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [theme, dir, setTheme])

  return { theme, dir, setTheme, toggleTheme, toggleDir, isDark: theme === 'dark' }
}
