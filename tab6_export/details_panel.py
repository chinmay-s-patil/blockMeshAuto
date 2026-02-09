"""
Formatted details panel for mesh statistics
"""
import tkinter as tk
from tkinter import scrolledtext


class MeshDetailsPanel(tk.Frame):
    """A formatted panel showing detailed mesh statistics"""
    
    def __init__(self, parent, colors_dict):
        super().__init__(parent, bg=colors_dict['secondary'])
        self.colors = colors_dict
        
        # Header
        header = tk.Frame(self, bg=self.colors['secondary'])
        header.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header, text="📊 Detailed Breakdown",
                font=('Segoe UI', 14, 'bold'),
                bg=self.colors['secondary'], fg=self.colors['fg']).pack(side=tk.LEFT)
        
        # Create text widget with custom styling
        text_container = tk.Frame(self, bg=self.colors['border'], bd=1)
        text_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(text_container, bg=self.colors['secondary'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text widget
        self.text = tk.Text(text_container,
                           font=('Consolas', 10),
                           bg=self.colors['text_bg'],
                           fg=self.colors['text_fg'],
                           relief=tk.FLAT,
                           wrap=tk.WORD,
                           yscrollcommand=scrollbar.set,
                           padx=20, pady=15,
                           height=15,
                           spacing1=2,
                           spacing3=2)
        self.text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        scrollbar.config(command=self.text.yview)
        
        # Configure text tags for rich formatting
        self._configure_tags()
        
        # Bind mouse wheel
        self.text.bind("<MouseWheel>", self._on_mousewheel)
        self.text.bind("<Button-4>", self._on_mousewheel_linux)
        self.text.bind("<Button-5>", self._on_mousewheel_linux)
    
    def _configure_tags(self):
        """Configure text tags for styling"""
        # Headers
        self.text.tag_configure("title",
                               foreground=self.colors['accent'],
                               font=('Segoe UI', 14, 'bold'),
                               spacing1=10, spacing3=5)
        
        self.text.tag_configure("section_header",
                               foreground=self.colors['success'],
                               font=('Consolas', 12, 'bold'),
                               spacing1=8, spacing3=4)
        
        self.text.tag_configure("subsection",
                               foreground=self.colors['fg'],
                               font=('Consolas', 11, 'bold'),
                               spacing1=4, spacing3=2)
        
        # Content
        self.text.tag_configure("label",
                               foreground=self.colors['fg'],
                               font=('Consolas', 10))
        
        self.text.tag_configure("value",
                               foreground=self.colors['warning'],
                               font=('Consolas', 10, 'bold'))
        
        self.text.tag_configure("highlight",
                               foreground=self.colors['success'],
                               font=('Consolas', 11, 'bold'))
        
        self.text.tag_configure("dim",
                               foreground='#808080',
                               font=('Consolas', 9, 'italic'))
        
        self.text.tag_configure("warning",
                               foreground=self.colors['error'],
                               font=('Consolas', 10, 'bold'))
        
        # Decorative
        self.text.tag_configure("separator",
                               foreground=self.colors['border'])
        
        self.text.tag_configure("box_top",
                               foreground=self.colors['accent'],
                               font=('Consolas', 10))
        
        self.text.tag_configure("box_content",
                               background=self.colors['secondary'],
                               font=('Consolas', 10))
    
    def clear(self):
        """Clear all content"""
        self.text.config(state=tk.NORMAL)
        self.text.delete('1.0', tk.END)
    
    def insert(self, text, tag=None):
        """Insert text with optional tag"""
        self.text.config(state=tk.NORMAL)
        if tag:
            self.text.insert(tk.END, text, tag)
        else:
            self.text.insert(tk.END, text)
    
    def insert_line(self, text="", tag=None):
        """Insert a line of text"""
        self.insert(text + "\n", tag)
    
    def insert_separator(self, char="─", width=50):
        """Insert a decorative separator"""
        self.insert_line(char * width, "separator")
    
    def insert_box_line(self, content, width=50):
        """Insert a line within a box"""
        padding = width - len(content) - 2
        left_pad = padding // 2
        right_pad = padding - left_pad
        line = "│ " + " " * left_pad + content + " " * right_pad + " │"
        self.insert_line(line, "box_content")
    
    def insert_section_header(self, title, icon=""):
        """Insert a styled section header"""
        self.insert_line()
        if icon:
            self.insert_line(f"{icon} {title}", "section_header")
        else:
            self.insert_line(title, "section_header")
        self.insert_separator("─", 50)
    
    def insert_key_value(self, key, value, indent=0):
        """Insert a key-value pair with formatting"""
        spaces = "  " * indent
        key_text = f"{spaces}{key}:"
        # Pad key to align values
        padding = max(0, 25 - len(key_text))
        self.insert(key_text + " " * padding, "label")
        self.insert_line(str(value), "value")
    
    def finalize(self):
        """Make the text read-only"""
        self.text.config(state=tk.DISABLED)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.text.yview_scroll(int(-1*(event.delta/120)), "units")
        return "break"
    
    def _on_mousewheel_linux(self, event):
        """Handle mouse wheel on Linux"""
        if event.num == 4:
            self.text.yview_scroll(-1, "units")
        elif event.num == 5:
            self.text.yview_scroll(1, "units")
        return "break"


class InfoBox(tk.Frame):
    """A styled info box for displaying grouped information"""
    
    def __init__(self, parent, title, color, colors_dict):
        super().__init__(parent, bg=colors_dict['secondary'])
        self.colors = colors_dict
        self.color = color
        
        # Container with border
        container = tk.Frame(self, bg=color, bd=2)
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        inner = tk.Frame(container, bg=self.colors['card_bg'])
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Title bar
        title_bar = tk.Frame(inner, bg=color, height=35)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        
        tk.Label(title_bar, text=title,
                font=('Segoe UI', 11, 'bold'),
                bg=color, fg='white').pack(side=tk.LEFT, padx=10, pady=5)
        
        # Content area
        self.content_frame = tk.Frame(inner, bg=self.colors['card_bg'])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    def add_row(self, label, value):
        """Add a label-value row to the info box"""
        row = tk.Frame(self.content_frame, bg=self.colors['card_bg'])
        row.pack(fill=tk.X, pady=3)
        
        tk.Label(row, text=label,
                font=('Segoe UI', 10),
                bg=self.colors['card_bg'],
                fg=self.colors['fg'],
                anchor=tk.W).pack(side=tk.LEFT)
        
        tk.Label(row, text=str(value),
                font=('Segoe UI', 10, 'bold'),
                bg=self.colors['card_bg'],
                fg=self.color,
                anchor=tk.E).pack(side=tk.RIGHT)