(function () {
  try {
    var stored = localStorage.getItem('theme')
    var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    var toSet = 'dark'

    if (stored === 'light') toSet = 'light'
    else if (stored === 'auto') toSet = prefersDark ? 'dark' : 'light'
    else if (stored === 'dark') toSet = 'dark'

    if (toSet === 'dark') document.documentElement.classList.add('dark')
    else document.documentElement.classList.remove('dark')
  } catch (e) {
    document.documentElement.classList.add('dark')
  }
})()
