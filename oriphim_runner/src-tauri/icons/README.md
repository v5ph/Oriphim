# Oriphim Runner Icons

This directory contains the application icons for the Oriphim Runner desktop application.

## Required Icons

For proper Tauri bundling, the following icon files are needed:

- `32x32.png` - Small icon for taskbar
- `128x128.png` - Medium icon for window
- `128x128@2x.png` - High-DPI medium icon
- `icon.icns` - macOS bundle icon
- `icon.ico` - Windows executable icon
- `icon.png` - System tray icon (should be the oriphim_legend.png)

## Icon Generation

To generate all required sizes from a source image:

1. Start with a high-resolution PNG (512x512 or higher)
2. Use online tools like:
   - [RealFaviconGenerator](https://realfavicongenerator.net/)
   - [IconGenerator](https://icon.wurmframework.org/)
   - [Tauri Icon Generator](https://github.com/tauri-apps/tauri-icon)

3. Or use the Tauri CLI:
   ```bash
   cargo tauri icon path/to/source-icon.png
   ```

## Current Status

Currently using placeholder icons. The actual Oriphim brand icons should be:
- Based on the Oriphim legend/logo
- Consistent with the brand guidelines
- Optimized for desktop display at various sizes

## Brand Guidelines

- Primary colors: Blue (#0066cc), White (#ffffff)
- Secondary colors: Gray tones for backgrounds
- Style: Clean, modern, professional
- Should work well on both light and dark system themes