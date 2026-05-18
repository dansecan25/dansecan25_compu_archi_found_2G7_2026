"""
Phase 2: Assemble processor components into complete pipeline diagram
"""

import tkinter as tk
from typing import Dict, List, Optional
from processor_components import *


class ProcessorDiagram:
    """Complete RISC-V 5-stage pipeline processor diagram"""

    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.components: Dict[str, ProcessorBlock] = {}
        self.wires: Dict[str, Wire] = {}
        self.junctions: Dict[str, Junction] = {}

        # Build the complete processor
        self._build_processor()

    def _build_processor(self):
        """Construct the complete processor diagram"""
        # Define layout parameters
        margin_x = 50
        margin_y = 20
        stage_width = 200  # Width allocated for each stage

        # ============ STAGE 1: INSTRUCTION FETCH (IF) ============
        x_if = margin_x

        # PC Register
        self.components['PC'] = PCRegister(self.canvas, x_if, margin_y + 80, 60, 50)

        # PC+4 Adder
        self.components['PC_Adder'] = Adder(self.canvas, x_if + 80, margin_y + 50, 35)

        # Instruction Memory
        self.components['Inst_Mem'] = Memory(self.canvas, x_if + 10, margin_y + 150, 90, 110, "Instruction")

        # IF/ID Pipeline Register
        x_ifid = x_if + stage_width - 30
        self.components['IF/ID'] = Register(self.canvas, x_ifid, margin_y + 10, 50, 280, "IF/ID")

        # ============ STAGE 2: INSTRUCTION DECODE (ID) ============
        x_id = x_ifid + 80

        # Control Unit
        self.components['Control'] = ControlUnit(self.canvas, x_id, margin_y + 10, 110, 70)

        # Register File
        self.components['RegFile'] = RegisterFile(self.canvas, x_id + 20, margin_y + 120, 90, 110)

        # Sign Extend
        self.components['SignExt'] = SignExtend(self.canvas, x_id + 10, margin_y + 240, 70, 40)

        # ID/EX Pipeline Register
        x_idex = x_id + stage_width - 20
        self.components['ID/EX'] = Register(self.canvas, x_idex, margin_y + 10, 50, 280, "ID/EX")

        # ============ STAGE 3: EXECUTE (EX) ============
        x_ex = x_idex + 80

        # ALU Control (small)
        self.components['ALU_Control'] = ProcessorBlock(self.canvas, x_ex + 70, margin_y + 70, 60, 40, "ALU\nCtrl")

        # ALU
        self.components['ALU'] = ALU(self.canvas, x_ex + 50, margin_y + 130, 70, 90)

        # Muxes for ALU inputs
        self.components['Mux_ALU_A'] = Multiplexer(self.canvas, x_ex + 10, margin_y + 140, 35, 50, 2)
        self.components['Mux_ALU_B'] = Multiplexer(self.canvas, x_ex + 130, margin_y + 160, 35, 50, 2)

        # Branch Adder
        self.components['Branch_Adder'] = Adder(self.canvas, x_ex + 60, margin_y + 30, 35)

        # EX/MEM Pipeline Register
        x_exmem = x_ex + stage_width - 20
        self.components['EX/MEM'] = Register(self.canvas, x_exmem, margin_y + 10, 50, 280, "EX/MEM")

        # ============ STAGE 4: MEMORY ACCESS (MEM) ============
        x_mem = x_exmem + 80

        # Data Memory
        self.components['Data_Mem'] = Memory(self.canvas, x_mem + 20, margin_y + 120, 90, 110, "Data")

        # Branch Mux (for PC source)
        self.components['Mux_PC'] = Multiplexer(self.canvas, x_mem + 10, margin_y + 30, 35, 50, 2)

        # MEM/WB Pipeline Register
        x_memwb = x_mem + stage_width - 30
        self.components['MEM/WB'] = Register(self.canvas, x_memwb, margin_y + 10, 50, 280, "MEM/WB")

        # ============ STAGE 5: WRITE BACK (WB) ============
        x_wb = x_memwb + 80

        # Write Back Mux
        self.components['Mux_WB'] = Multiplexer(self.canvas, x_wb + 20, margin_y + 150, 35, 50, 2)

        # Now create the wires connecting everything
        self._create_wires()

    def _create_wires(self):
        """Create all wire connections between components"""

        # ====== IF Stage Wires ======

        # PC to Instruction Memory
        pc_out = self.components['PC'].get_port('right')
        imem_in = self.components['Inst_Mem'].get_port('Addr')
        self.wires['PC_to_IMem'] = Wire(
            self.canvas,
            create_path(pc_out, imem_in, 'vertical_first'),
            name='PC_to_IMem'
        )

        # PC to PC+4 Adder
        pc_adder_in = self.components['PC_Adder'].get_port('left')
        self.wires['PC_to_Adder'] = Wire(
            self.canvas,
            create_path((pc_out[0], pc_out[1]), (pc_adder_in[0], pc_adder_in[1] + 10), 'horizontal_first'),
            name='PC_to_Adder'
        )

        # PC+4 Adder to IF/ID
        pc_adder_out = self.components['PC_Adder'].get_port('right')
        ifid_in = self.components['IF/ID'].get_port('left')
        self.wires['Adder_to_IFID'] = Wire(
            self.canvas,
            [(pc_adder_out[0], pc_adder_out[1]), (ifid_in[0], ifid_in[1] + 50)],
            name='Adder_to_IFID'
        )

        # Instruction Memory to IF/ID
        imem_out = self.components['Inst_Mem'].get_port('RD')
        self.wires['IMem_to_IFID'] = Wire(
            self.canvas,
            create_path(imem_out, (ifid_in[0], ifid_in[1] + 100), 'horizontal_first'),
            name='IMem_to_IFID'
        )

        # ====== ID Stage Wires ======

        # IF/ID to Control Unit
        ifid_out = self.components['IF/ID'].get_port('right')
        control_in = self.components['Control'].get_port('left')
        self.wires['IFID_to_Control'] = Wire(
            self.canvas,
            create_path((ifid_out[0], ifid_out[1] + 50), control_in, 'horizontal_first'),
            name='IFID_to_Control'
        )

        # IF/ID to Register File
        regfile_rr1 = self.components['RegFile'].get_port('RR1')
        self.wires['IFID_to_RegFile'] = Wire(
            self.canvas,
            create_path((ifid_out[0], ifid_out[1] + 100), regfile_rr1, 'horizontal_first'),
            name='IFID_to_RegFile'
        )

        # Register File to ID/EX
        regfile_rd1 = self.components['RegFile'].get_port('RD1')
        idex_in = self.components['ID/EX'].get_port('left')
        self.wires['RegFile_to_IDEX'] = Wire(
            self.canvas,
            create_path(regfile_rd1, (idex_in[0], idex_in[1] + 100), 'horizontal_first'),
            name='RegFile_to_IDEX'
        )

        # Sign Extend to ID/EX
        signext_out = self.components['SignExt'].get_port('right')
        self.wires['SignExt_to_IDEX'] = Wire(
            self.canvas,
            create_path(signext_out, (idex_in[0], idex_in[1] + 200), 'horizontal_first'),
            name='SignExt_to_IDEX'
        )

        # ====== EX Stage Wires ======

        # ID/EX to ALU
        idex_out = self.components['ID/EX'].get_port('right')
        mux_alu_a_in = self.components['Mux_ALU_A'].get_input_port(0)
        self.wires['IDEX_to_ALU'] = Wire(
            self.canvas,
            create_path((idex_out[0], idex_out[1] + 120), mux_alu_a_in, 'horizontal_first'),
            name='IDEX_to_ALU'
        )

        # Mux to ALU inputs
        mux_a_out = self.components['Mux_ALU_A'].get_output_port()
        alu_in_a = self.components['ALU'].get_port('top_left')
        self.wires['MuxA_to_ALU'] = Wire(
            self.canvas,
            create_path(mux_a_out, alu_in_a, 'horizontal_first'),
            name='MuxA_to_ALU'
        )

        mux_b_out = self.components['Mux_ALU_B'].get_output_port()
        alu_in_b = self.components['ALU'].get_port('top_right')
        self.wires['MuxB_to_ALU'] = Wire(
            self.canvas,
            create_path(mux_b_out, alu_in_b, 'horizontal_first'),
            name='MuxB_to_ALU'
        )

        # ALU to EX/MEM
        alu_out = self.components['ALU'].get_port('bottom')
        exmem_in = self.components['EX/MEM'].get_port('left')
        self.wires['ALU_to_EXMEM'] = Wire(
            self.canvas,
            create_path(alu_out, (exmem_in[0], exmem_in[1] + 150), 'vertical_first'),
            name='ALU_to_EXMEM'
        )

        # ====== MEM Stage Wires ======

        # EX/MEM to Data Memory
        exmem_out = self.components['EX/MEM'].get_port('right')
        dmem_addr = self.components['Data_Mem'].get_port('Addr')
        self.wires['EXMEM_to_DMem'] = Wire(
            self.canvas,
            create_path((exmem_out[0], exmem_out[1] + 120), dmem_addr, 'horizontal_first'),
            name='EXMEM_to_DMem'
        )

        # Data Memory to MEM/WB
        dmem_out = self.components['Data_Mem'].get_port('RD')
        memwb_in = self.components['MEM/WB'].get_port('left')
        self.wires['DMem_to_MEMWB'] = Wire(
            self.canvas,
            create_path(dmem_out, (memwb_in[0], memwb_in[1] + 150), 'horizontal_first'),
            name='DMem_to_MEMWB'
        )

        # ====== WB Stage Wires ======

        # MEM/WB to WB Mux
        memwb_out = self.components['MEM/WB'].get_port('right')
        mux_wb_in = self.components['Mux_WB'].get_input_port(0)
        self.wires['MEMWB_to_Mux'] = Wire(
            self.canvas,
            create_path((memwb_out[0], memwb_out[1] + 140), mux_wb_in, 'horizontal_first'),
            name='MEMWB_to_Mux'
        )

        # WB Mux back to Register File (feedback path)
        mux_wb_out = self.components['Mux_WB'].get_output_port()
        regfile_wd = self.components['RegFile'].get_port('WD')

        # Create feedback wire (goes down then back)
        feedback_points = [
            mux_wb_out,
            (mux_wb_out[0] + 20, mux_wb_out[1]),
            (mux_wb_out[0] + 20, 320),
            (regfile_wd[0] - 20, 320),
            (regfile_wd[0] - 20, regfile_wd[1]),
            regfile_wd
        ]
        self.wires['WB_to_RegFile'] = Wire(
            self.canvas,
            feedback_points,
            name='WB_to_RegFile',
            color='#6A4A6A'  # Different color for feedback
        )

        # Control signals (simplified - just show they exist)
        control_out = self.components['Control'].get_port('right')
        for i in range(5):
            end_x = control_out[0] + 30
            end_y = control_out[1] + i * 10
            self.wires[f'Control_{i}'] = Wire(
                self.canvas,
                [(control_out[0], control_out[1] + i * 10), (end_x, end_y)],
                width=1,
                name=f'Control_{i}'
            )

    def set_active_components(self, active_components: List[str]):
        """
        Activate specific components
        Args:
            active_components: List of component names to activate
        """
        # Deactivate all first
        for comp in self.components.values():
            comp.set_active(False)

        # Activate specified components
        for comp_name in active_components:
            if comp_name in self.components:
                self.components[comp_name].set_active(True)

    def set_active_wires(self, active_wires: List[str]):
        """
        Activate specific wires
        Args:
            active_wires: List of wire names to activate
        """
        # Deactivate all first
        for wire in self.wires.values():
            wire.set_active(False)

        # Activate specified wires
        for wire_name in active_wires:
            if wire_name in self.wires:
                self.wires[wire_name].set_active(True)

    def set_state_from_json(self, state_data: dict):
        """
        Set processor state from JSON/dict configuration
        Args:
            state_data: Dictionary with 'components' and 'wires' lists
        Example:
            {
                'components': ['PC', 'Inst_Mem', 'ALU'],
                'wires': ['PC_to_IMem', 'ALU_to_EXMEM']
            }
        """
        active_components = state_data.get('components', [])
        active_wires = state_data.get('wires', [])

        self.set_active_components(active_components)
        self.set_active_wires(active_wires)

    def reset_all(self):
        """Deactivate all components and wires"""
        self.set_active_components([])
        self.set_active_wires([])

    def highlight_stage(self, stage: str):
        """
        Highlight all components in a specific pipeline stage
        Args:
            stage: 'IF', 'ID', 'EX', 'MEM', or 'WB'
        """
        stage_components = {
            'IF': ['PC', 'PC_Adder', 'Inst_Mem', 'IF/ID'],
            'ID': ['Control', 'RegFile', 'SignExt', 'ID/EX'],
            'EX': ['ALU_Control', 'ALU', 'Mux_ALU_A', 'Mux_ALU_B', 'Branch_Adder', 'EX/MEM'],
            'MEM': ['Data_Mem', 'Mux_PC', 'MEM/WB'],
            'WB': ['Mux_WB']
        }

        stage_wires = {
            'IF': ['PC_to_IMem', 'PC_to_Adder', 'Adder_to_IFID', 'IMem_to_IFID'],
            'ID': ['IFID_to_Control', 'IFID_to_RegFile', 'RegFile_to_IDEX', 'SignExt_to_IDEX'],
            'EX': ['IDEX_to_ALU', 'MuxA_to_ALU', 'MuxB_to_ALU', 'ALU_to_EXMEM'],
            'MEM': ['EXMEM_to_DMem', 'DMem_to_MEMWB'],
            'WB': ['MEMWB_to_Mux', 'WB_to_RegFile']
        }

        components = stage_components.get(stage, [])
        wires = stage_wires.get(stage, [])

        self.set_active_components(components)
        self.set_active_wires(wires)

    def get_all_component_names(self) -> List[str]:
        """Get list of all component names"""
        return list(self.components.keys())

    def get_all_wire_names(self) -> List[str]:
        """Get list of all wire names"""
        return list(self.wires.keys())