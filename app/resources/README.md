# Resources

Icons currently come from Qt's built-in `QStyle.StandardPixmap` set so the
application ships with zero external icon-asset dependencies. Drop custom
SVG/PNG icons into `icons/` and reference them from `app/ui` if you want to
replace them with a branded icon set.

`styles/` is reserved for QSS files if you want to externalize the
dark/light stylesheets currently defined inline in `app/ui/theme.py`.
