"""
Modular components for RISC-V Pipeline Processor visualization
Phase 1: Define reusable blocks and wires for processor diagram
"""

import tkinter as tk
from typing import List, Tuple, Optional


class Wire:
    """Represents a wire/connection in the processor"""

    def __init__(self, canvas, points: List[Tuple[int, int]], width=2,
                 color='#4A4A4A', active_color='#6ADA6A', name=""):
        """
        Create a wire with multiple points
        Args:
            canvas: tkinter Canvas to draw on
            points: List of (x, y) coordinates
            width: Line width
            color: Inactive color
            active_color: Active color when signal is flowing
            name: Wire name for debugging
        """
        self.canvas = canvas
        self.points = points
        self.width = width
        self.color = color
        self.active_color = active_color
        self.name = name
        self.is_active = False
        self.line_ids = []

        self._draw()

    def _draw(self):
        """Draw the wire as a series of line segments"""
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            line_id = self.canvas.create_line(
                x1, y1, x2, y2,
                fill=self.color,
                width=self.width,
                tags=('wire', self.name)
            )
            self.line_ids.append(line_id)

    def set_active(self, active: bool):
        """Activate or deactivate the wire"""
        self.is_active = active
        color = self.active_color if active else self.color
        for line_id in self.line_ids:
            self.canvas.itemconfig(line_id, fill=color, width=self.width if not active else self.width + 1)

    def add_label(self, text: str, position: int = 0, offset=(0, -10)):
        """Add a text label to the wire"""
        if position < len(self.points):
            x, y = self.points[position]
            self.canvas.create_text(
                x + offset[0], y + offset[1],
                text=text,
                fill='#AAAAAA',
                font=('Arial', 7),
                tags=('wire_label', self.name)
            )


class ProcessorBlock:
    """Base class for processor components (ALU, Memory, Mux, etc.)"""

    def __init__(self, canvas, x: int, y: int, width: int, height: int,
                 label: str = "", color='#3A3A3A', active_color='#4A6A4A'):
        """
        Create a processor block
        Args:
            canvas: tkinter Canvas
            x, y: Top-left position
            width, height: Block dimensions
            label: Text label for the block
            color: Inactive color
            active_color: Active color
        """
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.color = color
        self.active_color = active_color
        self.is_active = False

        self.rect_id = None
        self.label_id = None
        self.additional_elements = []

        self._draw()

    def _draw(self):
        """Draw the basic rectangle block"""
        self.rect_id = self.canvas.create_rectangle(
            self.x, self.y,
            self.x + self.width, self.y + self.height,
            fill=self.color,
            outline='#5A5A5A',
            width=2,
            tags=('block', self.label)
        )

        # Add label
        self.label_id = self.canvas.create_text(
            self.x + self.width // 2,
            self.y + self.height // 2,
            text=self.label,
            fill='white',
            font=('Arial', 9, 'bold'),
            tags=('block_label', self.label)
        )

    def set_active(self, active: bool):
        """Activate or deactivate the block"""
        self.is_active = active
        color = self.active_color if active else self.color
        self.canvas.itemconfig(self.rect_id, fill=color, outline='#6ADA6A' if active else '#5A5A5A')

    def get_center(self) -> Tuple[int, int]:
        """Get the center point of the block"""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def get_port(self, side: str) -> Tuple[int, int]:
        """Get connection point on a specific side (top, bottom, left, right)"""
        if side == 'top':
            return (self.x + self.width // 2, self.y)
        elif side == 'bottom':
            return (self.x + self.width // 2, self.y + self.height)
        elif side == 'left':
            return (self.x, self.y + self.height // 2)
        elif side == 'right':
            return (self.x + self.width, self.y + self.height // 2)
        return self.get_center()


class ALU(ProcessorBlock):
    """ALU component with trapezoid shape"""

    def __init__(self, canvas, x: int, y: int, width=80, height=100):
        super().__init__(canvas, x, y, width, height, "ALU", '#3A3A3A', '#4A6A4A')

    def _draw(self):
        """Draw ALU as a trapezoid"""
        # Create trapezoid points
        indent = 15
        points = [
            self.x + indent, self.y,                    # Top left
            self.x + self.width - indent, self.y,       # Top right
            self.x + self.width, self.y + self.height,  # Bottom right
            self.x, self.y + self.height                # Bottom left
        ]

        self.rect_id = self.canvas.create_polygon(
            points,
            fill=self.color,
            outline='#5A5A5A',
            width=2,
            tags=('block', 'alu')
        )

        # Add label
        self.label_id = self.canvas.create_text(
            self.x + self.width // 2,
            self.y + self.height // 2,
            text="ALU",
            fill='white',
            font=('Arial', 11, 'bold'),
            tags=('block_label', 'alu')
        )

    def get_port(self, side: str) -> Tuple[int, int]:
        """Get ALU ports"""
        if side == 'top_left':
            return (self.x + 20, self.y + 20)
        elif side == 'top_right':
            return (self.x + self.width - 20, self.y + 20)
        elif side == 'bottom':
            return (self.x + self.width // 2, self.y + self.height)
        elif side == 'left':
            return (self.x + 10, self.y + self.height // 2)
        elif side == 'right':
            return (self.x + self.width - 10, self.y + self.height // 2)
        return super().get_port(side)


class Multiplexer(ProcessorBlock):
    """Multiplexer (Mux) component"""

    def __init__(self, canvas, x: int, y: int, width=40, height=60, num_inputs=2):
        self.num_inputs = num_inputs
        super().__init__(canvas, x, y, width, height, "MUX", '#3A3A3A', '#4A6A4A')

    def _draw(self):
        """Draw Mux as a trapezoid"""
        # Trapezoid shape (narrow on left, wide on right)
        points = [
            self.x, self.y + self.height // 4,           # Top left
            self.x + self.width, self.y,                 # Top right
            self.x + self.width, self.y + self.height,   # Bottom right
            self.x, self.y + 3 * self.height // 4        # Bottom left
        ]

        self.rect_id = self.canvas.create_polygon(
            points,
            fill=self.color,
            outline='#5A5A5A',
            width=2,
            tags=('block', 'mux')
        )

        # Add label
        self.label_id = self.canvas.create_text(
            self.x + self.width // 2,
            self.y + self.height // 2,
            text="M\nU\nX",
            fill='white',
            font=('Arial', 7, 'bold'),
            tags=('block_label', 'mux')
        )

    def get_input_port(self, index: int) -> Tuple[int, int]:
        """Get input port position"""
        spacing = self.height / (self.num_inputs + 1)
        y = self.y + spacing * (index + 1)
        return (self.x, int(y))

    def get_output_port(self) -> Tuple[int, int]:
        """Get output port position"""
        return (self.x + self.width, self.y + self.height // 2)

    def get_control_port(self) -> Tuple[int, int]:
        """Get control signal port (bottom)"""
        return (self.x + self.width // 2, self.y + self.height)


class RegisterFile(ProcessorBlock):
    """Register File component"""

    def __init__(self, canvas, x: int, y: int, width=100, height=120):
        super().__init__(canvas, x, y, width, height, "Register\nFile", '#3A3A3A', '#4A6A4A')

    def _draw(self):
        """Draw register file with ports"""
        super()._draw()

        # Add port labels
        port_font = ('Arial', 6)
        # Read ports
        self.canvas.create_text(self.x - 15, self.y + 25, text='RR1', fill='#888', font=port_font)
        self.canvas.create_text(self.x - 15, self.y + 45, text='RR2', fill='#888', font=port_font)
        self.canvas.create_text(self.x - 15, self.y + 85, text='WR', fill='#888', font=port_font)

        # Data ports
        self.canvas.create_text(self.x + self.width + 15, self.y + 25, text='RD1', fill='#888', font=port_font)
        self.canvas.create_text(self.x + self.width + 15, self.y + 45, text='RD2', fill='#888', font=port_font)
        self.canvas.create_text(self.x - 15, self.y + 105, text='WD', fill='#888', font=port_font)

    def get_port(self, port_name: str) -> Tuple[int, int]:
        """Get specific port position"""
        ports = {
            'RR1': (self.x, self.y + 25),      # Read Register 1
            'RR2': (self.x, self.y + 45),      # Read Register 2
            'WR': (self.x, self.y + 85),       # Write Register
            'RD1': (self.x + self.width, self.y + 25),   # Read Data 1
            'RD2': (self.x + self.width, self.y + 45),   # Read Data 2
            'WD': (self.x, self.y + 105),      # Write Data
            'WE': (self.x + self.width // 2, self.y)     # Write Enable
        }
        return ports.get(port_name, self.get_center())


class Memory(ProcessorBlock):
    """Memory component (Instruction or Data Memory)"""

    def __init__(self, canvas, x: int, y: int, width=100, height=120, mem_type="Instruction"):
        self.mem_type = mem_type
        label = f"{mem_type}\nMemory"
        super().__init__(canvas, x, y, width, height, label, '#3A3A3A', '#4A6A4A')

    def _draw(self):
        """Draw memory block with ports"""
        super()._draw()

        # Add port labels
        port_font = ('Arial', 6)
        if self.mem_type == "Instruction":
            self.canvas.create_text(self.x - 15, self.y + self.height // 2,
                                  text='Addr', fill='#888', font=port_font)
            self.canvas.create_text(self.x + self.width + 15, self.y + self.height // 2,
                                  text='RD', fill='#888', font=port_font)
        else:  # Data Memory
            self.canvas.create_text(self.x - 15, self.y + 30, text='Addr', fill='#888', font=port_font)
            self.canvas.create_text(self.x - 15, self.y + 60, text='WD', fill='#888', font=port_font)
            self.canvas.create_text(self.x + self.width + 15, self.y + self.height // 2,
                                  text='RD', fill='#888', font=port_font)
            self.canvas.create_text(self.x + self.width // 2, self.y - 10,
                                  text='WE', fill='#888', font=port_font)

    def get_port(self, port_name: str) -> Tuple[int, int]:
        """Get specific port position"""
        if self.mem_type == "Instruction":
            ports = {
                'Addr': (self.x, self.y + self.height // 2),
                'RD': (self.x + self.width, self.y + self.height // 2)
            }
        else:
            ports = {
                'Addr': (self.x, self.y + 30),
                'WD': (self.x, self.y + 60),
                'RD': (self.x + self.width, self.y + self.height // 2),
                'WE': (self.x + self.width // 2, self.y)
            }
        return ports.get(port_name, self.get_center())


class Adder(ProcessorBlock):
    """Adder component (for PC+4, branch calculation, etc.)"""

    def __init__(self, canvas, x: int, y: int, size=40):
        super().__init__(canvas, x, y, size, size, "+", '#3A3A3A', '#4A6A4A')

    def _draw(self):
        """Draw adder as a circle with + sign"""
        radius = self.width // 2

        self.rect_id = self.canvas.create_oval(
            self.x, self.y,
            self.x + self.width, self.y + self.height,
            fill=self.color,
            outline='#5A5A5A',
            width=2,
            tags=('block', 'adder')
        )

        # Add + sign
        self.label_id = self.canvas.create_text(
            self.x + radius,
            self.y + radius,
            text="+",
            fill='white',
            font=('Arial', 16, 'bold'),
            tags=('block_label', 'adder')
        )


class Register(ProcessorBlock):
    """Pipeline register (flip-flop) between stages"""

    def __init__(self, canvas, x: int, y: int, width=60, height=200, stage_name="IF/ID"):
        self.stage_name = stage_name
        super().__init__(canvas, x, y, width, height, stage_name, '#2A2A2A', '#3A4A3A')

    def _draw(self):
        """Draw pipeline register as a vertical bar"""
        super()._draw()

        # Add clock symbol
        clk_y = self.y + self.height - 15
        clk_x = self.x + self.width // 2

        # Small triangle for clock
        points = [
            clk_x - 5, clk_y,
            clk_x + 5, clk_y,
            clk_x, clk_y - 8
        ]
        self.canvas.create_polygon(points, fill='#888', outline='#AAA', tags=('clock', self.stage_name))


class ControlUnit(ProcessorBlock):
    """Control Unit component"""

    def __init__(self, canvas, x: int, y: int, width=120, height=80):
        super().__init__(canvas, x, y, width, height, "Control\nUnit", '#3A3A3A', '#4A6A4A')

    def _draw(self):
        """Draw control unit with multiple output ports"""
        super()._draw()

        # Add small output indicators on the right side
        num_outputs = 7
        spacing = self.height / (num_outputs + 1)
        for i in range(num_outputs):
            y = self.y + spacing * (i + 1)
            self.canvas.create_oval(
                self.x + self.width - 5, y - 3,
                self.x + self.width + 5, y + 3,
                fill='#555', outline='#777',
                tags=('control_output', self.label)
            )

    def get_output_port(self, index: int) -> Tuple[int, int]:
        """Get control output port position"""
        num_outputs = 7
        spacing = self.height / (num_outputs + 1)
        y = self.y + spacing * (index + 1)
        return (self.x + self.width, int(y))


class SignExtend(ProcessorBlock):
    """Sign Extend component"""

    def __init__(self, canvas, x: int, y: int, width=80, height=50):
        super().__init__(canvas, x, y, width, height, "Sign\nExtend", '#3A3A3A', '#4A6A4A')


class PCRegister(ProcessorBlock):
    """Program Counter register"""

    def __init__(self, canvas, x: int, y: int, width=60, height=50):
        super().__init__(canvas, x, y, width, height, "PC", '#3A3A3A', '#4A6A4A')
        self.current_value = 0

    def update_value(self, value: int):
        """Update PC value display"""
        self.current_value = value
        # Could add value display here


class Junction:
    """Wire junction/split point"""

    def __init__(self, canvas, x: int, y: int, radius=4):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radius = radius
        self.is_active = False

        self.circle_id = self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill='#4A4A4A',
            outline='#5A5A5A',
            tags='junction'
        )

    def set_active(self, active: bool):
        """Activate or deactivate the junction"""
        self.is_active = active
        color = '#6ADA6A' if active else '#4A4A4A'
        self.canvas.itemconfig(self.circle_id, fill=color, outline='#6ADA6A' if active else '#5A5A5A')


# Helper functions for creating wires with right angles
def create_path(start: Tuple[int, int], end: Tuple[int, int],
                style='horizontal_first') -> List[Tuple[int, int]]:
    """
    Create a path between two points with right angles
    Args:
        start: Starting point (x, y)
        end: Ending point (x, y)
        style: 'horizontal_first' or 'vertical_first'
    """
    x1, y1 = start
    x2, y2 = end

    if style == 'horizontal_first':
        return [start, (x2, y1), end]
    elif style == 'vertical_first':
        return [start, (x1, y2), end]
    else:  # direct line
        return [start, end]


def create_multi_segment_path(points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Create a path through multiple waypoints"""
    return points
