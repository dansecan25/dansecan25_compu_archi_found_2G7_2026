"""
Test/Demo file for processor diagram
This demonstrates the modular processor components in action
"""

import tkinter as tk
from tkinter import ttk
from processor_diagram import ProcessorDiagram


class ProcessorDiagramDemo:
    """Demo application to test processor diagram"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Processor Diagram Test")
        self.root.geometry("1400x700")
        self.root.configure(bg='#1A1A1A')

        self.current_stage = 0
        self.stages = ['IF', 'ID', 'EX', 'MEM', 'WB']

        # Create UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the demo UI"""
        # Control panel
        control_frame = tk.Frame(self.root, bg='#2A2A2A', height=80)
        control_frame.pack(fill='x', padx=10, pady=10)
        control_frame.pack_propagate(False)

        tk.Label(control_frame, text='Processor Diagram Demo',
                bg='#2A2A2A', fg='white', font=('Arial', 14, 'bold')).pack(pady=5)

        # Buttons
        btn_frame = tk.Frame(control_frame, bg='#2A2A2A')
        btn_frame.pack()

        btn_style = {'font': ('Arial', 10), 'bg': '#4A4A4A', 'fg': 'white',
                    'activebackground': '#5A5A5A', 'padx': 10, 'pady': 5}

        tk.Button(btn_frame, text='Reset', command=self.reset, **btn_style).pack(side='left', padx=5)
        tk.Button(btn_frame, text='◀ Prev Stage', command=self.prev_stage, **btn_style).pack(side='left', padx=5)
        tk.Button(btn_frame, text='Next Stage ▶', command=self.next_stage, **btn_style).pack(side='left', padx=5)
        tk.Button(btn_frame, text='Show IF', command=lambda: self.show_stage('IF'), **btn_style).pack(side='left', padx=5)
        tk.Button(btn_frame, text='Show ID', command=lambda: self.show_stage('ID'), **btn_style).pack(side='left', padx=5)
        tk.Button(btn_frame, text='Show EX', command=lambda: self.show_stage('EX'), **btn_style).pack(side='left', padx=5)
        tk.Button(btn_frame, text='Show MEM', command=lambda: self.show_stage('MEM'), **btn_style).pack(side='left', padx=5)
        tk.Button(btn_frame, text='Show WB', command=lambda: self.show_stage('WB'), **btn_style).pack(side='left', padx=5)

        # Status label
        self.status_label = tk.Label(control_frame, text='Stage: None', bg='#2A2A2A',
                                    fg='#6ADA6A', font=('Arial', 11, 'bold'))
        self.status_label.pack(pady=5)

        # Canvas for processor diagram
        canvas_frame = tk.Frame(self.root, bg='#1A1A1A')
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Add scrollbars
        h_scroll = ttk.Scrollbar(canvas_frame, orient='horizontal')
        v_scroll = ttk.Scrollbar(canvas_frame, orient='vertical')

        self.canvas = tk.Canvas(
            canvas_frame,
            bg='#1A1A1A',
            highlightthickness=0,
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set
        )

        h_scroll.config(command=self.canvas.xview)
        v_scroll.config(command=self.canvas.yview)

        self.canvas.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Create processor diagram
        self.diagram = ProcessorDiagram(self.canvas)

        # Configure scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        # Info panel
        info_frame = tk.Frame(self.root, bg='#2A2A2A', height=100)
        info_frame.pack(fill='x', padx=10, pady=(0, 10))
        info_frame.pack_propagate(False)

        tk.Label(info_frame, text='Component Info', bg='#2A2A2A', fg='white',
                font=('Arial', 11, 'bold')).pack(pady=5)

        info_text = """
        • Click stage buttons to highlight different pipeline stages
        • IF: Instruction Fetch - PC, Instruction Memory
        • ID: Instruction Decode - Control Unit, Register File, Sign Extend
        • EX: Execute - ALU, ALU Control, Multiplexers
        • MEM: Memory Access - Data Memory
        • WB: Write Back - Write Back Multiplexer
        """

        tk.Label(info_frame, text=info_text, bg='#2A2A2A', fg='#AAAAAA',
                font=('Arial', 9), justify='left').pack()

    def reset(self):
        """Reset all highlighting"""
        self.diagram.reset_all()
        self.current_stage = 0
        self.status_label.config(text='Stage: None')

    def show_stage(self, stage: str):
        """Show specific stage"""
        self.diagram.highlight_stage(stage)
        self.status_label.config(text=f'Stage: {stage}')

    def next_stage(self):
        """Show next stage"""
        self.current_stage = (self.current_stage + 1) % len(self.stages)
        stage = self.stages[self.current_stage]
        self.show_stage(stage)

    def prev_stage(self):
        """Show previous stage"""
        self.current_stage = (self.current_stage - 1) % len(self.stages)
        stage = self.stages[self.current_stage]
        self.show_stage(stage)

    def run(self):
        """Run the demo application"""
        self.root.mainloop()


if __name__ == '__main__':
    demo = ProcessorDiagramDemo()
    demo.run()
