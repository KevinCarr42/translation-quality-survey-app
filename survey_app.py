import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import csv
import random
import os
from typing import Dict, List, Optional

class TranslationSurveyApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Translation Quality Survey")
        self.root.geometry("1200x800")
        
        # Load data
        self.data = pd.read_csv('merged_translation_data.csv')
        self.all_data = self.data.copy()  # Keep original data
        self.current_language_filter = "Both"  # Default filter
        
        # Apply initial filter and randomize question order
        self.apply_language_filter()
        self.current_position = 0
        
        # Initialize comparison mode variables
        self.comp_current_language_filter = "Both"
        self.comp_current_position = 0
        self.comp_data = self.all_data.copy()
        self.comp_question_indices = list(range(len(self.comp_data)))
        random.shuffle(self.comp_question_indices)
        
        # Initialize zoom level
        self.zoom_level = 1.0
        self.base_font_sizes = {
            'header': 14,
            'source': 11,
            'translation_header': 11,
            'translation_text': 10,
            'filter_label': 12
        }
        
        # Translation columns (excluding source and corpus_type)
        self.translation_columns = [
            'translation_bureau', 'm2m100_418m_base', 'm2m100_418m_finetuned',
            'mbart50_mmt_base', 'mbart50_mmt_finetuned', 'nllb_3b_base_researchonly',
            'opus_mt_base', 'opus_mt_finetuned'
        ]
        
        self.ranking_options = ['', 'good', 'bad', 'best', 'unknown']
        
        self.setup_ui()
        self.load_next_question()
        self.load_next_comparison()
        
        # Bind window resize event
        self.root.bind('<Configure>', self.on_window_resize)
    
    def setup_ui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Create tab frames
        self.rank_all_frame = ttk.Frame(self.notebook)
        self.comparison_frame = ttk.Frame(self.notebook)
        
        # Configure tab styling
        tab_font = ("Arial", 12, "bold")
        style = ttk.Style()
        
        # Try setting the theme first
        try:
            style.theme_use('clam')  # Use clam theme which supports better customization
        except:
            pass  # Fall back to default theme if clam not available
        
        # Dark mode styling
        dark_bg = '#2b2b2b'
        dark_fg = 'white'  # Changed to white for better contrast
        dark_select_bg = '#404040'
        
        # Configure dark theme for various elements
        style.configure('TFrame', background=dark_bg)
        style.configure('TLabel', background=dark_bg, foreground=dark_fg)
        style.configure('TButton', background='#404040', foreground=dark_fg)
        style.map('TButton', background=[('active', '#505050')])
        style.configure('TCombobox', 
                       background='#404040', 
                       foreground=dark_fg, 
                       fieldbackground='#404040',
                       selectbackground='#505050',
                       selectforeground=dark_fg,
                       arrowcolor=dark_fg)
        style.map('TCombobox', 
                  fieldbackground=[('readonly', '#404040')],
                  selectbackground=[('readonly', '#505050')],
                  foreground=[('readonly', dark_fg)])
        style.configure('TLabelFrame', background=dark_bg, foreground=dark_fg)
        style.configure('TLabelFrame.Label', background=dark_bg, foreground=dark_fg)
        style.configure('TSeparator', background='#505050')
        style.configure('TNotebook', background=dark_bg, borderwidth=0)
        
        # Configure tab styling (keep the same tab colors)
        style.configure('TNotebook.Tab', 
                       font=tab_font, 
                       foreground='#666666',  # Mid-grey for unselected
                       background='#f0f0f0',  # Light grey background for unselected
                       padding=[12, 6])       # Default padding (shorter)
        
        style.map('TNotebook.Tab', 
                  background=[('selected', '#ADD8E6'),    # Light blue for selected
                             ('active', '#B0E0E6')],      # Slightly different blue on hover
                  foreground=[('selected', 'black'),      # Black text for selected
                             ('active', 'black')],        # Black text on hover
                  relief=[('selected', 'raised')],        # Raised effect for selected
                  padding=[('selected', [12, 10])]        # Taller padding for selected tab
        )
        
        # Configure root window background
        self.root.configure(bg=dark_bg)
        
        # Add tabs to notebook
        self.notebook.add(self.rank_all_frame, text="Rank All Translations")
        self.notebook.add(self.comparison_frame, text="Which is Better?")
        
        # Setup both tabs
        self.setup_rank_all_tab()
        self.setup_comparison_tab()
    
    def setup_rank_all_tab(self):
        # Main frame for rank all tab
        main_frame = ttk.Frame(self.rank_all_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.rank_all_frame.columnconfigure(0, weight=1)
        self.rank_all_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Source text header with language filter
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 3))
        header_frame.columnconfigure(0, weight=1)
        
        ttk.Label(header_frame, text="Source Text:", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky=tk.W)
        
        filter_frame = ttk.Frame(header_frame)
        filter_frame.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Label(filter_frame, text="Source Language:", font=("Arial", 12)).grid(row=0, column=0, padx=(0, 5))
        
        self.language_var = tk.StringVar(value="Both")
        self.language_combo = ttk.Combobox(filter_frame, textvariable=self.language_var, 
                                          values=["Both", "English", "French"], 
                                          state="readonly", width=10)
        self.language_combo.grid(row=0, column=1)
        self.language_combo.bind('<<ComboboxSelected>>', self.on_language_filter_change)
        
        self.source_label = ttk.Label(main_frame, text="", font=("Arial", 11, "bold"), wraplength=1000, justify=tk.LEFT)
        self.source_label.grid(row=1, column=0, columnspan=2, pady=(0, 5), sticky=(tk.W, tk.E))
        
        # Separator line under source text
        source_separator = ttk.Separator(main_frame, orient='horizontal')
        source_separator.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Translations frame
        translations_frame = ttk.Frame(main_frame)
        translations_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        translations_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Create scrollable frame for translations
        canvas = tk.Canvas(translations_frame, highlightthickness=0, bg='#2b2b2b')
        scrollbar = ttk.Scrollbar(translations_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # Only show scrollbar when needed
        self.canvas = canvas
        self.scrollbar = scrollbar
        
        translations_frame.rowconfigure(0, weight=1)
        translations_frame.columnconfigure(0, weight=1)
        
        # Make scrollable frame expand to canvas width and manage scrollbar
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas.find_all()[0], width=canvas.winfo_width())
            
            # Show/hide scrollbar based on content height
            canvas.update_idletasks()
            content_height = self.scrollable_frame.winfo_reqheight()
            canvas_height = canvas.winfo_height()
            
            if content_height > canvas_height:
                scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
                translations_frame.columnconfigure(1, weight=0)
            else:
                scrollbar.grid_remove()
                translations_frame.columnconfigure(1, weight=0)
        
        self.scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_scroll_region)
        
        # Mouse wheel scrolling and zooming
        def _on_mousewheel(event):
            if event.state & 0x4:  # Ctrl key is pressed
                # Zoom functionality
                if event.delta > 0:
                    self.zoom_in()
                else:
                    self.zoom_out()
            else:
                # Normal scrolling
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Navigation buttons
        nav_frame = ttk.Frame(main_frame)
        nav_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        self.next_button = ttk.Button(nav_frame, text="Next →", command=self.next_question)
        self.next_button.grid(row=0, column=0, padx=(0, 10))
        
        self.save_button = ttk.Button(nav_frame, text="Save and Close", command=self.save_and_close)
        self.save_button.grid(row=0, column=1, padx=(10, 0))
    
    def setup_comparison_tab(self):
        # Main frame for comparison tab
        comp_main_frame = ttk.Frame(self.comparison_frame, padding="10")
        comp_main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.comparison_frame.columnconfigure(0, weight=1)
        self.comparison_frame.rowconfigure(0, weight=1)
        comp_main_frame.columnconfigure(0, weight=1)
        
        # Source text header with language filter
        comp_header_frame = ttk.Frame(comp_main_frame)
        comp_header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 3))
        comp_header_frame.columnconfigure(0, weight=1)
        
        ttk.Label(comp_header_frame, text="Source Text:", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky=tk.W)
        
        comp_filter_frame = ttk.Frame(comp_header_frame)
        comp_filter_frame.grid(row=0, column=1, sticky=tk.E)
        
        ttk.Label(comp_filter_frame, text="Source Language:", font=("Arial", 12)).grid(row=0, column=0, padx=(0, 5))
        
        self.comp_language_var = tk.StringVar(value="Both")
        self.comp_language_combo = ttk.Combobox(comp_filter_frame, textvariable=self.comp_language_var, 
                                               values=["Both", "English", "French"], 
                                               state="readonly", width=10)
        self.comp_language_combo.grid(row=0, column=1)
        self.comp_language_combo.bind('<<ComboboxSelected>>', self.on_comp_language_filter_change)
        
        # Source text
        self.comp_source_label = ttk.Label(comp_main_frame, text="", font=("Arial", 11, "bold"), wraplength=1000, justify=tk.LEFT)
        self.comp_source_label.grid(row=1, column=0, pady=(0, 5), sticky=(tk.W, tk.E))
        
        # Separator line
        comp_separator = ttk.Separator(comp_main_frame, orient='horizontal')
        comp_separator.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Comparison frame
        self.comp_translations_frame = ttk.Frame(comp_main_frame)
        self.comp_translations_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.comp_translations_frame.columnconfigure(0, weight=1)
        comp_main_frame.rowconfigure(3, weight=1)
        
        # Navigation buttons for comparison tab
        comp_nav_frame = ttk.Frame(comp_main_frame)
        comp_nav_frame.grid(row=4, column=0, pady=(10, 0))
        
        self.comp_next_button = ttk.Button(comp_nav_frame, text="Next →", command=self.comp_next_question)
        self.comp_next_button.grid(row=0, column=0, padx=(0, 10))
        
        self.comp_save_button = ttk.Button(comp_nav_frame, text="Save and Close", command=self.save_and_close)
        self.comp_save_button.grid(row=0, column=1, padx=(10, 0))
    
    def apply_language_filter(self):
        """Filter data based on selected language and randomize question order"""
        if self.current_language_filter == "Both":
            self.data = self.all_data.copy()
        elif self.current_language_filter == "English":
            self.data = self.all_data[self.all_data['source_lang'] == 'en'].copy()
        else:  # French
            self.data = self.all_data[self.all_data['source_lang'] == 'fr'].copy()
        
        # Reset indices and randomize
        self.question_indices = list(range(len(self.data)))
        random.shuffle(self.question_indices)
    
    def on_language_filter_change(self, event=None):
        """Handle language filter change"""
        new_filter = self.language_var.get()
        if new_filter != self.current_language_filter:
            # Save current rankings before switching
            if hasattr(self, 'ranking_vars'):
                self.save_current_rankings()
            
            self.current_language_filter = new_filter
            self.apply_language_filter()
            self.current_position = 0
            self.load_next_question()
    
    def on_comp_language_filter_change(self, event=None):
        """Handle language filter change for comparison tab"""
        new_filter = self.comp_language_var.get()
        if new_filter != self.comp_current_language_filter:
            self.comp_current_language_filter = new_filter
            self.apply_comp_language_filter()
            self.comp_current_position = 0
            self.load_next_comparison()
    
    def apply_comp_language_filter(self):
        """Filter data based on selected language for comparison tab"""
        if self.comp_current_language_filter == "Both":
            self.comp_data = self.all_data.copy()
        elif self.comp_current_language_filter == "English":
            self.comp_data = self.all_data[self.all_data['source_lang'] == 'en'].copy()
        else:  # French
            self.comp_data = self.all_data[self.all_data['source_lang'] == 'fr'].copy()
        
        # Reset indices and randomize
        self.comp_question_indices = list(range(len(self.comp_data)))
        random.shuffle(self.comp_question_indices)
    
    def create_translation_widgets(self):
        # Clear existing widgets and labels list
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.ranking_vars = {}
        self.translation_labels = []  # Reset labels list
        current_row = self.data.iloc[self.current_index]
        
        # Get translations and randomize order
        translations = []
        for col in self.translation_columns:
            if pd.notna(current_row[col]) and str(current_row[col]).strip():
                translations.append((col, str(current_row[col])))
        
        # Randomize the order
        random.shuffle(translations)
        
        # Create widgets for each translation
        for i, (col_name, translation) in enumerate(translations):
            frame = ttk.Frame(self.scrollable_frame, padding="5")
            frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=(0, 8), padx=(0, 10))
            self.scrollable_frame.columnconfigure(0, weight=1)
            
            # Header with translation number and rank dropdown on same line
            header_frame = ttk.Frame(frame)
            header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
            header_frame.columnconfigure(0, weight=1)
            
            ttk.Label(header_frame, text=f"Translation {i+1}", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky=tk.W)
            
            rank_frame = ttk.Frame(header_frame)
            rank_frame.grid(row=0, column=1, sticky=tk.E)
            
            ttk.Label(rank_frame, text="Rank:").grid(row=0, column=0, padx=(0, 5))
            
            var = tk.StringVar(value='')  # Explicitly set to empty
            combo = ttk.Combobox(rank_frame, textvariable=var, values=self.ranking_options, state="readonly", width=10)
            combo.set('')  # Ensure it starts blank
            combo.grid(row=0, column=1)
            
            # Disable mousewheel on combobox to prevent accidental changes
            def disable_mousewheel(event):
                return "break"
            combo.bind("<MouseWheel>", disable_mousewheel)
            
            # Translation text as label
            translation_label = ttk.Label(frame, text=translation, font=("Arial", 10), wraplength=1000, justify=tk.LEFT)
            translation_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 3))
            
            # Store translation labels for resize handling
            self.translation_labels.append(translation_label)
            
            # Add separator line
            separator = ttk.Separator(frame, orient='horizontal')
            separator.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(3, 0))
            
            # Store the variable with the original column name for tracking
            self.ranking_vars[col_name] = var
            
            frame.columnconfigure(0, weight=1)
    
    def load_next_question(self):
        if self.current_position < len(self.question_indices):
            self.current_index = self.question_indices[self.current_position]
            self.update_progress()
            self.update_source_text()
            self.create_translation_widgets()
            self.update_navigation_buttons()
            # Reapply zoom level to new widgets
            self.update_font_sizes()
        else:
            messagebox.showinfo("Survey Complete", "You have completed all questions!")
    
    def update_progress(self):
        pass  # ID removed
    
    def update_source_text(self):
        current_row = self.data.iloc[self.current_index]
        self.source_label.config(text=str(current_row['source']))
    
    def update_navigation_buttons(self):
        self.next_button.config(state=tk.NORMAL if self.current_position < len(self.question_indices) - 1 else tk.DISABLED)
    
    def save_current_rankings(self):
        """Save current rankings to CSV if any rankings exist"""
        if not hasattr(self, 'ranking_vars'):
            return
        
        # Get current rankings
        current_rankings = {}
        for col_name, var in self.ranking_vars.items():
            ranking = var.get()
            current_rankings[col_name] = ranking if ranking else ''
        
        # Only save if any rankings were made
        if not any(ranking for ranking in current_rankings.values()):
            return
        
        # Create result row matching original CSV structure
        current_row = self.data.iloc[self.current_index]
        result_row = {
            'source': str(current_row['source']),
            'corpus_type': str(current_row['corpus_type'])
        }
        
        # Add rankings for each translation column
        for col in self.translation_columns:
            result_row[col] = current_rankings.get(col, '')
        
        # Write to CSV
        filename = 'translation_quality_results.csv'
        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['source'] + self.translation_columns + ['corpus_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(result_row)
    
    def load_saved_rankings(self):
        # No longer remember rankings - always start blank
        for col_name, var in self.ranking_vars.items():
            var.set('')
    
    def next_question(self):
        # Save current rankings before moving
        self.save_current_rankings()
        
        if self.current_position < len(self.question_indices) - 1:
            self.current_position += 1
            self.load_next_question()
    
    def comp_next_question(self):
        """Move to next comparison question"""
        # Save current comparison if any
        if hasattr(self, 'comp_translation1_col') and hasattr(self, 'comp_translation2_col'):
            self.save_current_comparison()
        
        if self.comp_current_position < len(self.comp_question_indices) - 1:
            self.comp_current_position += 1
            self.load_next_comparison()
    
    def load_next_comparison(self):
        """Load next comparison question"""
        if self.comp_current_position < len(self.comp_question_indices):
            self.comp_current_index = self.comp_question_indices[self.comp_current_position]
            self.update_comp_source_text()
            self.create_comparison_widgets()
            self.update_comp_navigation_buttons()
            # Reapply zoom level to new widgets
            self.update_font_sizes()
        else:
            messagebox.showinfo("Survey Complete", "You have completed all comparison questions!")
    
    def update_comp_source_text(self):
        """Update source text for comparison tab"""
        current_row = self.comp_data.iloc[self.comp_current_index]
        self.comp_source_label.config(text=str(current_row['source']))
    
    def update_comp_navigation_buttons(self):
        """Update navigation buttons for comparison tab"""
        self.comp_next_button.config(state=tk.NORMAL if self.comp_current_position < len(self.comp_question_indices) - 1 else tk.DISABLED)
    
    def create_comparison_widgets(self):
        """Create comparison widgets with 2 random translations"""
        # Clear existing widgets
        for widget in self.comp_translations_frame.winfo_children():
            widget.destroy()
        
        current_row = self.comp_data.iloc[self.comp_current_index]
        
        # Get available translations
        available_translations = []
        for col in self.translation_columns:
            if pd.notna(current_row[col]) and str(current_row[col]).strip():
                available_translations.append((col, str(current_row[col])))
        
        # Select 2 random translations
        if len(available_translations) < 2:
            messagebox.showwarning("Not enough translations", "Need at least 2 translations for comparison!")
            return
        
        selected_translations = random.sample(available_translations, 2)
        self.comp_translation1_col, translation1_text = selected_translations[0]
        self.comp_translation2_col, translation2_text = selected_translations[1]
        
        # Translation A section
        ttk.Label(self.comp_translations_frame, text="Translation A", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        translation1_label = ttk.Label(self.comp_translations_frame, text=translation1_text, font=("Arial", 10), wraplength=1000, justify=tk.LEFT)
        translation1_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        better1_button = ttk.Button(self.comp_translations_frame, text="This is Better", command=lambda: self.choose_better(1))
        better1_button.grid(row=2, column=0, pady=(0, 15))
        
        # Separator between translations
        separator = ttk.Separator(self.comp_translations_frame, orient='horizontal')
        separator.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Translation B section
        ttk.Label(self.comp_translations_frame, text="Translation B", font=("Arial", 12, "bold")).grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        
        translation2_label = ttk.Label(self.comp_translations_frame, text=translation2_text, font=("Arial", 10), wraplength=1000, justify=tk.LEFT)
        translation2_label.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        better2_button = ttk.Button(self.comp_translations_frame, text="This is Better", command=lambda: self.choose_better(2))
        better2_button.grid(row=6, column=0, pady=(0, 10))
        
        # Store labels for font updating
        if not hasattr(self, 'comp_translation_labels'):
            self.comp_translation_labels = []
        self.comp_translation_labels = [translation1_label, translation2_label]
    
    def choose_better(self, choice):
        """Handle user choosing which translation is better"""
        self.comp_choice = choice
        # Automatically move to next question after choice
        self.comp_next_question()
    
    def save_current_comparison(self):
        """Save comparison result to CSV"""
        if not hasattr(self, 'comp_choice'):
            return  # No choice made
        
        current_row = self.comp_data.iloc[self.comp_current_index]
        
        # Create result row
        result_row = {
            'source': str(current_row['source']),
            'corpus_type': str(current_row['corpus_type'])
        }
        
        # Set better/worse based on choice
        for col in self.translation_columns:
            if col == self.comp_translation1_col:
                result_row[col] = 'better' if self.comp_choice == 1 else 'worse'
            elif col == self.comp_translation2_col:
                result_row[col] = 'better' if self.comp_choice == 2 else 'worse'
            else:
                result_row[col] = ''
        
        # Write to same CSV as ranking mode
        filename = 'translation_quality_results.csv'
        file_exists = os.path.isfile(filename)
        
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['source'] + self.translation_columns + ['corpus_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(result_row)
        
        # Clear choice for next comparison
        delattr(self, 'comp_choice')
    
    def save_and_close(self):
        """Save current rankings and close the application"""
        # Save rankings if any exist
        if hasattr(self, 'ranking_vars'):
            self.save_current_rankings()
        
        self.root.quit()
    
    def zoom_in(self):
        """Increase font size"""
        self.zoom_level = min(2.0, self.zoom_level + 0.1)  # Max 2x zoom
        self.update_font_sizes()
    
    def zoom_out(self):
        """Decrease font size"""
        self.zoom_level = max(0.5, self.zoom_level - 0.1)  # Min 0.5x zoom
        self.update_font_sizes()
    
    def update_font_sizes(self):
        """Update all font sizes based on current zoom level"""
        # Update header font
        header_size = int(self.base_font_sizes['header'] * self.zoom_level)
        source_size = int(self.base_font_sizes['source'] * self.zoom_level)
        filter_size = int(self.base_font_sizes['filter_label'] * self.zoom_level)
        translation_header_size = int(self.base_font_sizes['translation_header'] * self.zoom_level)
        translation_text_size = int(self.base_font_sizes['translation_text'] * self.zoom_level)
        
        # Update source text label
        self.source_label.config(font=("Arial", source_size))
        
        # Update translation labels
        if hasattr(self, 'translation_labels'):
            for label in self.translation_labels:
                label.config(font=("Arial", translation_text_size))
        
        # Update comparison labels
        if hasattr(self, 'comp_translation_labels'):
            for label in self.comp_translation_labels:
                label.config(font=("Arial", translation_text_size))
        
        # Update comparison source label
        if hasattr(self, 'comp_source_label'):
            self.comp_source_label.config(font=("Arial", source_size))
        
        # Note: Static UI elements (headers, filter labels) would need widget references to update
        # For now, they'll keep their original size as they're created once
    
    def on_window_resize(self, event):
        """Handle window resize event to update text wrapping"""
        # Only handle resize events for the root window
        if event.widget != self.root:
            return
            
        # Get current window width and calculate wrap length
        window_width = self.root.winfo_width()
        # Subtract padding and scrollbar space, convert pixels to characters
        wrap_length = max(200, window_width - 100)  # Minimum 200, subtract padding
        
        # Update source label wraplength
        self.source_label.config(wraplength=wrap_length)
        
        # Update translation labels wraplength
        if hasattr(self, 'translation_labels'):
            for label in self.translation_labels:
                label.config(wraplength=wrap_length)
        
        # Update comparison labels wraplength
        if hasattr(self, 'comp_translation_labels'):
            for label in self.comp_translation_labels:
                label.config(wraplength=wrap_length)  # Full width since stacked vertically
        
        # Update comparison source label wraplength
        if hasattr(self, 'comp_source_label'):
            self.comp_source_label.config(wraplength=wrap_length)
    
    def run(self):
        self.root.mainloop()

def main():
    # Check if data file exists
    if not os.path.exists('merged_translation_data.csv'):
        messagebox.showerror("Error", "merged_translation_data.csv not found!")
        return
    
    app = TranslationSurveyApp()
    app.run()

if __name__ == "__main__":
    main()