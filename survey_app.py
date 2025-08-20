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
        
        # Translation columns (excluding source and corpus_type)
        self.translation_columns = [
            'translation_bureau', 'm2m100_418m_base', 'm2m100_418m_finetuned',
            'mbart50_mmt_base', 'mbart50_mmt_finetuned', 'nllb_3b_base_researchonly',
            'opus_mt_base', 'opus_mt_finetuned'
        ]
        
        self.ranking_options = ['', 'good', 'bad', 'best', 'unknown']
        
        self.setup_ui()
        self.load_next_question()
        
        # Bind window resize event
        self.root.bind('<Configure>', self.on_window_resize)
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
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
        
        self.source_label = ttk.Label(main_frame, text="", font=("Arial", 11), wraplength=1000, justify=tk.LEFT)
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
        canvas = tk.Canvas(translations_frame, height=400)
        scrollbar = ttk.Scrollbar(translations_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        translations_frame.rowconfigure(0, weight=1)
        translations_frame.columnconfigure(0, weight=1)
        
        # Make scrollable frame expand to canvas width
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas.find_all()[0], width=canvas.winfo_width())
        
        self.scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_scroll_region)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Navigation buttons
        nav_frame = ttk.Frame(main_frame)
        nav_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        self.next_button = ttk.Button(nav_frame, text="Next →", command=self.next_question)
        self.next_button.grid(row=0, column=0, padx=(0, 10))
        
        self.save_button = ttk.Button(nav_frame, text="Save and Close", command=self.save_and_close)
        self.save_button.grid(row=0, column=1, padx=(10, 0))
    
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
    
    def save_and_close(self):
        """Save current rankings and close the application"""
        # Save rankings if any exist
        if hasattr(self, 'ranking_vars'):
            self.save_current_rankings()
        
        self.root.quit()
    
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