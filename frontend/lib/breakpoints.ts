// Single JS-side source of truth for breakpoint numbers used with
// useMediaQuery. CSS @media conditions cannot reference CSS custom
// properties (only literal values are valid), so app/globals.css keeps
// its own literal numbers in sync with these by hand — see the comment
// block at the top of globals.css for the canonical breakpoint list.
export const BP_SHELL_MAX = 899; // sidebar: drawer (<=899) vs inline (>=900)
export const BP_CONTENT_MAX = 640; // content reflow: grids, login stacking
