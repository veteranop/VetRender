"""
Modern Dark Theme for Cellfire RF Studio
=========================================
Provides a modern, professional dark theme that replaces the Windows 95 look.
"""

import tkinter as tk
from tkinter import ttk


class CellfireTheme:
    """Modern dark theme configuration for Cellfire RF Studio"""

    # Color palette - Modern dark theme with blue accents
    COLORS = {
        # Base colors
        'bg_dark': '#1e1e1e',          # Main background
        'bg_medium': '#252526',         # Secondary background
        'bg_light': '#2d2d30',          # Elevated surfaces
        'bg_hover': '#3e3e42',          # Hover state
        'bg_selected': '#094771',       # Selected state

        # Text colors
        'fg_primary': '#cccccc',        # Primary text
        'fg_secondary': '#858585',      # Secondary text
        'fg_disabled': '#5a5a5a',       # Disabled text
        'fg_bright': '#ffffff',         # Bright/highlight text

        # Accent colors
        'accent': '#0078d4',            # Primary accent (blue)
        'accent_hover': '#1084d8',      # Accent hover
        'accent_pressed': '#006cbd',    # Accent pressed
        'accent_light': '#4fc3f7',      # Light accent

        # Semantic colors
        'success': '#4caf50',           # Success/good signal
        'warning': '#ff9800',           # Warning
        'error': '#f44336',             # Error/danger
        'info': '#2196f3',              # Information

        # Border colors
        'border': '#3f3f46',            # Normal border
        'border_light': '#505050',      # Light border
        'border_focus': '#0078d4',      # Focused border

        # Special
        'input_bg': '#3c3c3c',          # Input field background
        'scrollbar': '#424242',         # Scrollbar track
        'scrollbar_thumb': '#686868',   # Scrollbar thumb
    }

    @classmethod
    def apply(cls, root):
        """Apply the modern dark theme to the application

        Args:
            root: Tkinter root window
        """
        style = ttk.Style(root)

        # Try to use clam as base (most customizable)
        try:
            style.theme_use('clam')
        except:
            pass

        # Configure root window
        root.configure(bg=cls.COLORS['bg_dark'])
        root.option_add('*Background', cls.COLORS['bg_dark'])
        root.option_add('*Foreground', cls.COLORS['fg_primary'])
        root.option_add('*Font', ('Segoe UI', 9))

        # =====================================================================
        # Frame styles
        # =====================================================================
        style.configure('TFrame',
            background=cls.COLORS['bg_dark']
        )

        style.configure('Card.TFrame',
            background=cls.COLORS['bg_medium'],
            relief='flat'
        )

        # =====================================================================
        # Label styles
        # =====================================================================
        style.configure('TLabel',
            background=cls.COLORS['bg_dark'],
            foreground=cls.COLORS['fg_primary'],
            font=('Segoe UI', 9)
        )

        style.configure('Title.TLabel',
            background=cls.COLORS['bg_dark'],
            foreground=cls.COLORS['fg_bright'],
            font=('Segoe UI', 14, 'bold')
        )

        style.configure('Subtitle.TLabel',
            background=cls.COLORS['bg_dark'],
            foreground=cls.COLORS['accent_light'],
            font=('Segoe UI', 11, 'bold')
        )

        style.configure('Header.TLabel',
            background=cls.COLORS['bg_medium'],
            foreground=cls.COLORS['fg_bright'],
            font=('Segoe UI', 12, 'bold')
        )

        style.configure('Status.TLabel',
            background=cls.COLORS['bg_dark'],
            foreground=cls.COLORS['fg_secondary'],
            font=('Segoe UI', 9)
        )

        # =====================================================================
        # Button styles
        # =====================================================================
        style.configure('TButton',
            background=cls.COLORS['bg_light'],
            foreground=cls.COLORS['fg_primary'],
            borderwidth=0,
            focuscolor=cls.COLORS['accent'],
            padding=(12, 6),
            font=('Segoe UI', 9)
        )
        style.map('TButton',
            background=[
                ('pressed', cls.COLORS['bg_hover']),
                ('active', cls.COLORS['bg_hover']),
                ('disabled', cls.COLORS['bg_dark'])
            ],
            foreground=[
                ('disabled', cls.COLORS['fg_disabled'])
            ]
        )

        # Accent button (primary action)
        style.configure('Accent.TButton',
            background=cls.COLORS['accent'],
            foreground=cls.COLORS['fg_bright'],
            borderwidth=0,
            padding=(12, 6),
            font=('Segoe UI', 9, 'bold')
        )
        style.map('Accent.TButton',
            background=[
                ('pressed', cls.COLORS['accent_pressed']),
                ('active', cls.COLORS['accent_hover']),
                ('disabled', cls.COLORS['bg_light'])
            ],
            foreground=[
                ('disabled', cls.COLORS['fg_disabled'])
            ]
        )

        # =====================================================================
        # Entry styles
        # =====================================================================
        style.configure('TEntry',
            fieldbackground=cls.COLORS['input_bg'],
            foreground=cls.COLORS['fg_primary'],
            insertcolor=cls.COLORS['fg_primary'],
            borderwidth=1,
            padding=5
        )
        style.map('TEntry',
            fieldbackground=[
                ('focus', cls.COLORS['bg_light']),
                ('disabled', cls.COLORS['bg_dark'])
            ],
            bordercolor=[
                ('focus', cls.COLORS['border_focus'])
            ]
        )

        # =====================================================================
        # Combobox styles
        # =====================================================================
        style.configure('TCombobox',
            fieldbackground=cls.COLORS['input_bg'],
            background=cls.COLORS['input_bg'],
            foreground=cls.COLORS['fg_primary'],
            arrowcolor=cls.COLORS['fg_primary'],
            borderwidth=1,
            padding=5
        )
        style.map('TCombobox',
            fieldbackground=[
                ('readonly', cls.COLORS['input_bg']),
                ('disabled', cls.COLORS['bg_dark'])
            ],
            foreground=[
                ('disabled', cls.COLORS['fg_disabled'])
            ],
            arrowcolor=[
                ('disabled', cls.COLORS['fg_disabled'])
            ]
        )

        # Style the dropdown listbox
        root.option_add('*TCombobox*Listbox.background', cls.COLORS['bg_light'])
        root.option_add('*TCombobox*Listbox.foreground', cls.COLORS['fg_primary'])
        root.option_add('*TCombobox*Listbox.selectBackground', cls.COLORS['accent'])
        root.option_add('*TCombobox*Listbox.selectForeground', cls.COLORS['fg_bright'])

        # =====================================================================
        # Checkbutton styles
        # =====================================================================
        style.configure('TCheckbutton',
            background=cls.COLORS['bg_dark'],
            foreground=cls.COLORS['fg_primary'],
            focuscolor=cls.COLORS['accent'],
            font=('Segoe UI', 9)
        )
        style.map('TCheckbutton',
            background=[
                ('active', cls.COLORS['bg_dark'])
            ],
            foreground=[
                ('disabled', cls.COLORS['fg_disabled'])
            ]
        )

        # =====================================================================
        # Radiobutton styles
        # =====================================================================
        style.configure('TRadiobutton',
            background=cls.COLORS['bg_dark'],
            foreground=cls.COLORS['fg_primary'],
            focuscolor=cls.COLORS['accent'],
            font=('Segoe UI', 9)
        )
        style.map('TRadiobutton',
            background=[
                ('active', cls.COLORS['bg_dark'])
            ],
            foreground=[
                ('disabled', cls.COLORS['fg_disabled'])
            ]
        )

        # =====================================================================
        # Scale (slider) styles
        # =====================================================================
        style.configure('TScale',
            background=cls.COLORS['bg_dark'],
            troughcolor=cls.COLORS['bg_light'],
            sliderrelief='flat'
        )
        style.configure('Horizontal.TScale',
            background=cls.COLORS['bg_dark'],
            troughcolor=cls.COLORS['bg_light']
        )

        # =====================================================================
        # Progressbar styles
        # =====================================================================
        style.configure('TProgressbar',
            background=cls.COLORS['accent'],
            troughcolor=cls.COLORS['bg_light'],
            borderwidth=0
        )

        # =====================================================================
        # Notebook (tabs) styles
        # =====================================================================
        style.configure('TNotebook',
            background=cls.COLORS['bg_dark'],
            borderwidth=0
        )
        style.configure('TNotebook.Tab',
            background=cls.COLORS['bg_medium'],
            foreground=cls.COLORS['fg_secondary'],
            padding=(16, 8),
            font=('Segoe UI', 9)
        )
        style.map('TNotebook.Tab',
            background=[
                ('selected', cls.COLORS['bg_dark']),
                ('active', cls.COLORS['bg_light'])
            ],
            foreground=[
                ('selected', cls.COLORS['fg_bright']),
                ('active', cls.COLORS['fg_primary'])
            ],
            expand=[
                ('selected', (0, 0, 0, 2))
            ]
        )

        # =====================================================================
        # Treeview styles
        # =====================================================================
        style.configure('Treeview',
            background=cls.COLORS['bg_medium'],
            foreground=cls.COLORS['fg_primary'],
            fieldbackground=cls.COLORS['bg_medium'],
            borderwidth=1,
            relief='solid',
            rowheight=24,
            font=('Segoe UI', 9)
        )
        style.configure('Treeview.Heading',
            background=cls.COLORS['bg_light'],
            foreground=cls.COLORS['fg_primary'],
            borderwidth=1,
            relief='raised',
            font=('Segoe UI', 9, 'bold')
        )
        style.map('Treeview',
            background=[
                ('selected', cls.COLORS['bg_selected'])
            ],
            foreground=[
                ('selected', cls.COLORS['fg_bright'])
            ]
        )
        style.map('Treeview.Heading',
            background=[
                ('active', cls.COLORS['bg_hover'])
            ]
        )

        # Define tag colors for alternating rows (used by station_builder)
        # These are applied via tree.tag_configure() in the widget code

        # =====================================================================
        # Scrollbar styles
        # =====================================================================
        style.configure('TScrollbar',
            background=cls.COLORS['scrollbar'],
            troughcolor=cls.COLORS['bg_dark'],
            borderwidth=0,
            arrowcolor=cls.COLORS['fg_secondary']
        )
        style.map('TScrollbar',
            background=[
                ('active', cls.COLORS['scrollbar_thumb']),
                ('pressed', cls.COLORS['scrollbar_thumb'])
            ]
        )

        # =====================================================================
        # Separator styles
        # =====================================================================
        style.configure('TSeparator',
            background=cls.COLORS['border']
        )

        # =====================================================================
        # LabelFrame styles
        # =====================================================================
        style.configure('TLabelframe',
            background=cls.COLORS['bg_dark'],
            bordercolor=cls.COLORS['border'],
            borderwidth=1,
            relief='solid'
        )
        style.configure('TLabelframe.Label',
            background=cls.COLORS['bg_dark'],
            foreground=cls.COLORS['accent_light'],
            font=('Segoe UI', 10, 'bold')
        )

        # =====================================================================
        # PanedWindow styles
        # =====================================================================
        style.configure('TPanedwindow',
            background=cls.COLORS['bg_dark']
        )

        # =====================================================================
        # Menu styles (standard tk, not ttk)
        # =====================================================================
        root.option_add('*Menu.background', cls.COLORS['bg_medium'])
        root.option_add('*Menu.foreground', cls.COLORS['fg_primary'])
        root.option_add('*Menu.activeBackground', cls.COLORS['accent'])
        root.option_add('*Menu.activeForeground', cls.COLORS['fg_bright'])
        root.option_add('*Menu.selectColor', cls.COLORS['accent'])
        root.option_add('*Menu.disabledForeground', cls.COLORS['fg_disabled'])
        root.option_add('*Menu.relief', 'flat')
        root.option_add('*Menu.borderWidth', 0)

        # =====================================================================
        # Text widget styles (standard tk)
        # =====================================================================
        root.option_add('*Text.background', cls.COLORS['bg_medium'])
        root.option_add('*Text.foreground', cls.COLORS['fg_primary'])
        root.option_add('*Text.insertBackground', cls.COLORS['fg_primary'])
        root.option_add('*Text.selectBackground', cls.COLORS['accent'])
        root.option_add('*Text.selectForeground', cls.COLORS['fg_bright'])
        root.option_add('*Text.font', ('Consolas', 10))

        # =====================================================================
        # Listbox styles (standard tk)
        # =====================================================================
        root.option_add('*Listbox.background', cls.COLORS['bg_medium'])
        root.option_add('*Listbox.foreground', cls.COLORS['fg_primary'])
        root.option_add('*Listbox.selectBackground', cls.COLORS['accent'])
        root.option_add('*Listbox.selectForeground', cls.COLORS['fg_bright'])

        # =====================================================================
        # Spinbox styles
        # =====================================================================
        style.configure('TSpinbox',
            fieldbackground=cls.COLORS['input_bg'],
            background=cls.COLORS['input_bg'],
            foreground=cls.COLORS['fg_primary'],
            arrowcolor=cls.COLORS['fg_primary'],
            borderwidth=1
        )

        return style

    @classmethod
    def get_text_colors(cls):
        """Get colors for configuring Text widgets

        Returns:
            dict: Dictionary of color configurations
        """
        return {
            'bg': cls.COLORS['bg_medium'],
            'fg': cls.COLORS['fg_primary'],
            'insertbackground': cls.COLORS['fg_primary'],
            'selectbackground': cls.COLORS['accent'],
            'selectforeground': cls.COLORS['fg_bright']
        }

    @classmethod
    def get_canvas_colors(cls):
        """Get colors for matplotlib and canvas elements

        Returns:
            dict: Dictionary of color configurations
        """
        return {
            'figure_facecolor': cls.COLORS['bg_dark'],
            'axes_facecolor': cls.COLORS['bg_medium'],
            'text_color': cls.COLORS['fg_primary'],
            'grid_color': cls.COLORS['border'],
            'accent': cls.COLORS['accent']
        }


def apply_theme(root):
    """Convenience function to apply the theme

    Args:
        root: Tkinter root window

    Returns:
        ttk.Style: The configured style object
    """
    return CellfireTheme.apply(root)
