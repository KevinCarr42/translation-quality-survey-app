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
        
        # Load data and randomize question order
        self.data = pd.read_csv('merged_translation_data.csv')
        self.question_indices = list(range(len(self.data)))
        random.shuffle(self.question_indices)
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
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Progress label
        self.progress_label = ttk.Label(main_frame, text="", font=("Arial", 12))
        self.progress_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)
        
        # Source text
        ttk.Label(main_frame, text="Source Text:", font=("Arial", 14, "bold")).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.source_text = tk.Text(main_frame, height=4, width=100, wrap=tk.WORD, font=("Arial", 11))
        self.source_text.grid(row=2, column=0, columnspan=2, pady=(0, 20), sticky=(tk.W, tk.E))
        
        # Translations frame
        translations_frame = ttk.Frame(main_frame)
        translations_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        translations_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        ttk.Label(translations_frame, text="Translations (in random order):", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
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
        
        canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        translations_frame.rowconfigure(1, weight=1)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Navigation buttons
        nav_frame = ttk.Frame(main_frame)
        nav_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        
        self.prev_button = ttk.Button(nav_frame, text="← Previous", command=self.previous_question)
        self.prev_button.grid(row=0, column=0, padx=(0, 10))
        
        self.next_button = ttk.Button(nav_frame, text="Next →", command=self.next_question)
        self.next_button.grid(row=0, column=1, padx=(10, 0))
        
        self.save_button = ttk.Button(nav_frame, text="Save Rankings", command=self.save_results)
        self.save_button.grid(row=0, column=2, padx=(20, 0))
    
    def create_translation_widgets(self):
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.ranking_vars = {}
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
            frame = ttk.LabelFrame(self.scrollable_frame, text=f"Translation {i+1}", padding="10")
            frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=(0, 10), padx=(0, 10))
            self.scrollable_frame.columnconfigure(0, weight=1)
            
            # Translation text
            text_widget = tk.Text(frame, height=3, width=80, wrap=tk.WORD, font=("Arial", 10))
            text_widget.insert("1.0", translation)
            text_widget.config(state=tk.DISABLED)
            text_widget.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
            
            # Ranking dropdown
            ttk.Label(frame, text="Rank:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
            
            var = tk.StringVar(value='')  # Explicitly set to empty
            combo = ttk.Combobox(frame, textvariable=var, values=self.ranking_options, state="readonly", width=10)
            combo.set('')  # Ensure it starts blank
            combo.grid(row=1, column=1, sticky=tk.W)
            
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
        self.progress_label.config(text=f"Question {self.current_position + 1} of {len(self.question_indices)} (ID: {self.current_index})")
    
    def update_source_text(self):
        current_row = self.data.iloc[self.current_index]
        self.source_text.config(state=tk.NORMAL)
        self.source_text.delete("1.0", tk.END)
        self.source_text.insert("1.0", str(current_row['source']))
        self.source_text.config(state=tk.DISABLED)
    
    def update_navigation_buttons(self):
        self.prev_button.config(state=tk.NORMAL if self.current_position > 0 else tk.DISABLED)
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
    
    def previous_question(self):
        # Save current rankings before moving
        self.save_current_rankings()
        
        if self.current_position > 0:
            self.current_position -= 1
            self.load_next_question()
    
    def save_results(self):
        """Manual save button - saves current rankings and shows confirmation"""
        if not hasattr(self, 'ranking_vars'):
            messagebox.showwarning("No Data", "No rankings to save!")
            return
        
        # Get current rankings
        current_rankings = {}
        for col_name, var in self.ranking_vars.items():
            ranking = var.get()
            current_rankings[col_name] = ranking if ranking else ''
        
        # Check if any rankings were made
        if not any(ranking for ranking in current_rankings.values()):
            messagebox.showwarning("No Rankings", "Please rank at least one translation before saving!")
            return
        
        # Save the rankings
        self.save_current_rankings()
        
        messagebox.showinfo("Saved", f"Rankings saved to translation_quality_results.csv!\n\nYou can now navigate to another question or re-rank this one.")
    
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