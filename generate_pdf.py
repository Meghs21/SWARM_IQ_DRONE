"""
Script to generate SwarmIQ_Project_Report.pdf using ReportLab Platypus.
Creates a professional, multi-page project summary designed for academic presentation.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y'."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, letter[1] - 30, "SwarmIQ — Autonomous Multi-Drone Swarm Simulation")
            self.drawRightString(letter[0] - 36, letter[1] - 30, "Academic Project Summary")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, letter[1] - 34, letter[0] - 36, letter[1] - 34)

        # Running footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 36, 25, page_text)
        self.drawString(36, 25, "Confidential & Academic Presentation Guide • SwarmIQ 2026")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 35, letter[0] - 36, 35)

        self.restoreState()


def build_pdf(filename="SwarmIQ_Project_Report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46,
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0f172a")     # Deep slate
    ACCENT_GREEN = colors.HexColor("#059669")# Emerald green
    ACCENT_BLUE = colors.HexColor("#2563eb") # Royal blue
    TEXT_DARK = colors.HexColor("#1e293b")   # Slate 800
    TEXT_MUTED = colors.HexColor("#64748b")  # Slate 500
    BG_LIGHT = colors.HexColor("#f8fafc")    # Slate 50
    CARD_BORDER = colors.HexColor("#e2e8f0") # Slate 200

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=ACCENT_GREEN,
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=ACCENT_BLUE,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_DARK,
        spaceAfter=6,
    )

    body_bold = ParagraphStyle(
        "Body_Bold",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_DARK,
    )

    callout_style = ParagraphStyle(
        "Callout_Text",
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=TEXT_DARK,
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=PRIMARY,
    )

    q_style = ParagraphStyle(
        "Q_Style",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=ACCENT_BLUE,
    )

    a_style = ParagraphStyle(
        "A_Style",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        spaceAfter=6,
    )

    story = []

    # ==========================
    # COVER / HEADER SECTION
    # ==========================
    story.append(Paragraph("SwarmIQ: Autonomous Multi-Drone Swarm Simulator", title_style))
    story.append(
        Paragraph(
            "<b>Comprehensive Technical Summary & Academic Presentation Guide</b>",
            subtitle_style,
        )
    )

    meta_table_data = [
        [
            Paragraph("<b>Project:</b> SwarmIQ (Autonomous Robotics Sim)", table_cell_style),
            Paragraph("<b>Fleet Capacity:</b> 100+ Virtual Drones in Real-Time", table_cell_style),
        ],
        [
            Paragraph("<b>Core Stack:</b> Python, FastAPI, Three.js, React", table_cell_style),
            Paragraph("<b>Control Mode:</b> 100% Autonomous (No Manual Pilot)", table_cell_style),
        ],
        [
            Paragraph("<b>Tick Rate:</b> 25 Hz Server Simulation / 60 FPS Viewport", table_cell_style),
            Paragraph("<b>GitHub:</b> github.com/Meghs21/SWARM_IQ_DRONE", table_cell_style),
        ],
    ]
    meta_table = Table(meta_table_data, colWidths=[270, 270])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.5, CARD_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, CARD_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # ==========================
    # 1. PROBLEM STATEMENT & OBJECTIVE
    # ==========================
    story.append(Paragraph("1. Problem Statement & Project Objective", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_GREEN, spaceAfter=8))

    story.append(
        Paragraph(
            "<b>The Problem:</b> In real-world drone applications (search & rescue, defense, environmental mapping, disaster relief), managing large fleets using individual human pilots is impossible. Traditional multi-drone setups suffer from communication lag, single points of failure (if a central controller fails), and the inability to dynamically respond to sudden obstacles and moving hazards.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "<b>The Objective:</b> Build <b>SwarmIQ</b> — a decentralized, software-based 3D simulation of an autonomous drone swarm where up to <b>100 virtual drones coordinate without any manual piloting</b>. The swarm self-organizes, elects leaders dynamically, navigates 3D obstacle courses via A*, maintains formations (V, Line, Grid, Circle), and actively prevents collisions in real-time.",
            body_style,
        )
    )

    # Key Highlights Box
    highlights_data = [
        [
            Paragraph(
                "<b>Key Evaluation Highlights to Present:</b><br/>"
                "• <b>Decentralized Intelligence:</b> Every drone executes local physics, separation, and obstacle evasion.<br/>"
                "• <b>Hierarchical Planning:</b> Only the elected leader solves global 3D A*; followers maintain formation.<br/>"
                "• <b>Fault Tolerance:</b> If the leader is shot down or drops below 20% battery, automatic election elects a new leader with zero mission interruption.<br/>"
                "• <b>Real-Time 3D Rendering:</b> 100 drones at 60 FPS in Three.js via GPU hardware instancing.",
                callout_style,
            )
        ]
    ]
    htab = Table(highlights_data, colWidths=[540])
    htab.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ecfdf5")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#6ee7b7")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(htab)
    story.append(Spacer(1, 10))

    # ==========================
    # 2. SYSTEM ARCHITECTURE & TECH STACK
    # ==========================
    story.append(Paragraph("2. System Architecture & Tech Stack", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_GREEN, spaceAfter=8))

    story.append(
        Paragraph(
            "SwarmIQ uses a high-performance decoupled Client-Server architecture. The server runs the physics loop at 25 Hz and broadcasts JSON state snapshots over WebSockets to a Three.js 3D viewport.",
            body_style,
        )
    )

    stack_table_data = [
        [
            Paragraph("Subsystem", table_header_style),
            Paragraph("Technologies Used", table_header_style),
            Paragraph("Key Responsibilities & Capabilities", table_header_style),
        ],
        [
            Paragraph("<b>Backend Engine</b>", table_cell_bold),
            Paragraph("Python 3.11, FastAPI, Uvicorn, Asyncio", table_cell_style),
            Paragraph("25 Hz non-blocking physics loop, REST control API, WebSocket server, state management.", table_cell_style),
        ],
        [
            Paragraph("<b>Math & Physics</b>", table_cell_bold),
            Paragraph("NumPy, SciPy", table_cell_style),
            Paragraph("Vectorized O(N²) Boids forces, pairwise distance matrices, kinematic integration, clamping.", table_cell_style),
        ],
        [
            Paragraph("<b>3D Frontend Viewport</b>", table_cell_bold),
            Paragraph("Three.js, WebGL", table_cell_style),
            Paragraph("GPU InstancedMesh rendering (100 drones in 1 draw call), OrbitControls, lighting, shadow maps.", table_cell_style),
        ],
        [
            Paragraph("<b>Command HUD UI</b>", table_cell_bold),
            Paragraph("React 18, Vite, Tailwind CSS, Lucide", table_cell_style),
            Paragraph("Telemetry dashboard, formation switcher, color themes, fault injector, preset scenario cards.", table_cell_style),
        ],
    ]
    stab = Table(stack_table_data, colWidths=[110, 150, 280])
    stab.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("BOX", (0, 0), (-1, -1), 0.5, CARD_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, CARD_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(stab)
    story.append(Spacer(1, 10))

    # Page Break for clean presentation
    story.append(PageBreak())

    # ==========================
    # 3. THE 6 CORE AUTONOMOUS ALGORITHMS
    # ==========================
    story.append(Paragraph("3. The Six Core Autonomous Algorithms (Explain to Teacher)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_GREEN, spaceAfter=8))

    story.append(
        Paragraph(
            "Every drone in SwarmIQ operates as an independent agent calculating forces on every tick. The resultant motion is governed by continuous force synthesis: "
            "<b>F_total = F_boids + F_formation + F_navigation + F_obstacle(APF) + F_collision</b>",
            body_style,
        )
    )

    algo_table_data = [
        [
            Paragraph("Algorithm", table_header_style),
            Paragraph("How It Works (Simple Concept)", table_header_style),
            Paragraph("Technical Formulation / Innovation", table_header_style),
        ],
        [
            Paragraph("<b>1. Reynolds Boids Flocking</b>", table_cell_bold),
            Paragraph("Bio-inspired flocking: keeps drones moving as a cohesive group without clumping.", table_cell_style),
            Paragraph("Vectorized O(N²) NumPy implementation: Separation (1/r²), Alignment (velocity matching), Cohesion (center of mass). Decoupled in formation flight so geometry is preserved.", table_cell_style),
        ],
        [
            Paragraph("<b>2. 3D Global A* Path Planning</b>", table_cell_bold),
            Paragraph("High-level 3D GPS: calculates the shortest collision-free flight path around obstacles.", table_cell_style),
            Paragraph("3D Voxel grid with 26-connectivity and obstacle safety inflation (2.5m). Raycast string-pulling prunes redundant waypoints. Computed solely for the leader to save 95% CPU.", table_cell_style),
        ],
        [
            Paragraph("<b>3. Artificial Potential Field (APF)</b>", table_cell_bold),
            Paragraph("Invisible repulsive force fields push drones away from obstacles like matching magnetic poles.", table_cell_style),
            Paragraph("Khatib APF formulation: F_rep = k_rep * (1/d - 1/d0) * (1/d²). Features quadratic scaling with close-proximity surge up to 40 N, dynamic formation attenuation, and 0.8m physical hull deflection.", table_cell_style),
        ],
        [
            Paragraph("<b>4. Geometric Formation Control</b>", table_cell_bold),
            Paragraph("Rigid geometric slot assignment: arranges the swarm into V, Line, Grid, or Circle.", table_cell_style),
            Paragraph("Persistent slot sorting modulo 2π prevents criss-crossing. Velocity feedforward matches leader velocity, enabling zero-lag millimeter-accurate slot tracking.", table_cell_style),
        ],
        [
            Paragraph("<b>5. Dynamic Leader Election</b>", table_cell_bold),
            Paragraph("Democratic fleet election: picks the best drone as captain; auto-replaces it on failure.", table_cell_style),
            Paragraph("Multi-factor fitness function: Score = 35% Battery + 30% Distance + 20% Connectivity + 15% Health. Instant 1-tick failover when battery < 20% or on hardware failure.", table_cell_style),
        ],
        [
            Paragraph("<b>6. Drone-to-Drone Collision Avoidance</b>", table_cell_bold),
            Paragraph("Emergency close-range bubble: prevents drones from colliding with peer drones in the swarm.", table_cell_style),
            Paragraph("Hyperbolic proximity repulsion under 2.0m (F_evade = k * (1/d - 1/r_safe)/d² * Δpos). Vectorized pairwise distance matrix with 3-tier event tracking: Warnings (3m), Near-Misses (2m), Collisions (0.6m).", table_cell_style),
        ],
    ]
    atab = Table(algo_table_data, colWidths=[125, 180, 235])
    atab.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("BOX", (0, 0), (-1, -1), 0.5, CARD_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, CARD_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(atab)
    story.append(Spacer(1, 6))

    # Detailed APF Deep-Dive Box
    apf_data = [
        [
            Paragraph(
                "<b>Deep Dive: How Artificial Potential Fields (APF) Work in SwarmIQ</b><br/>"
                "• <b>The Principle:</b> The destination waypoint creates an attractive potential well pulling the drone forward (<b>F_att = -∇U_att</b>). Every obstacle (pillar, box, moving hazard) generates a repulsive potential hill pushing drones away (<b>F_rep = -∇U_rep</b>).<br/>"
                "• <b>Overcoming the Classic APF Trapping Problem:</b> In naive APF, when drones are in tight formation, the formation spring force (18 N) overpowers the repulsive field (0.53 N), dragging drones into obstacles. In SwarmIQ, we introduced <b>Dynamic Formation Attenuation</b>: near obstacles, formation pull is scaled down so drones fluidly part around obstacles like water around a stone, and smoothly reform on the other side!",
                callout_style,
            )
        ]
    ]
    apf_tab = Table(apf_data, colWidths=[540])
    apf_tab.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#86efac")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(apf_tab)
    story.append(Spacer(1, 8))

    # ==========================
    # 4. INTERACTIVE CONTROLS & DEMO FLEXIBILITY
    # ==========================
    story.append(Paragraph("4. Fleet Size & Formation Flexibility Across All Modes", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_GREEN, spaceAfter=8))

    story.append(
        Paragraph(
            "<b>Interactive Customization Matrix:</b> SwarmIQ gives full real-time control to the user during evaluation:",
            body_style,
        )
    )

    flex_data = [
        [
            Paragraph("Control Feature", table_header_style),
            Paragraph("Supported Options", table_header_style),
            Paragraph("Behavior Across Scenarios / Modes", table_header_style),
        ],
        [
            Paragraph("<b>Fleet Size Selector</b>", table_cell_bold),
            Paragraph("<b>20, 50, or 100 Drones</b>", table_cell_style),
            Paragraph("Available across <b>ALL 5 MODES</b> and custom missions! You can switch between 20, 50, or 100 drones at any time. Scenario obstacles are preserved and drones re-slot dynamically.", table_cell_style),
        ],
        [
            Paragraph("<b>Formation Selector</b>", table_cell_bold),
            Paragraph("<b>V, Line, Grid, Circle</b>", table_cell_style),
            Paragraph("Available in <b>ALL 5 MODES</b>! You can switch formations at any moment — even while flying at full speed — and the drones smoothly morph in mid-air.", table_cell_style),
        ],
        [
            Paragraph("<b>Follower Color Palette</b>", table_cell_bold),
            Paragraph("Emerald, Violet, White, Amber, Cyan", table_cell_style),
            Paragraph("Instantly updates follower drone materials and glow in the Three.js viewport without reloading.", table_cell_style),
        ],
        [
            Paragraph("<b>Fault Injection</b>", table_cell_bold),
            Paragraph("Kill Leader Button", table_cell_style),
            Paragraph("Simulates sudden leader drone failure; demonstrates instant 40ms autonomous leader re-election.", table_cell_style),
        ],
    ]
    flex_tab = Table(flex_data, colWidths=[125, 140, 275])
    flex_tab.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("BOX", (0, 0), (-1, -1), 0.5, CARD_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, CARD_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(flex_tab)
    story.append(Spacer(1, 8))

    # ==========================
    # 5. PRESET DEMO SCENARIOS
    # ==========================
    story.append(Paragraph("5. Preset Demonstration Scenarios for Teacher Demo", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_GREEN, spaceAfter=8))

    scenarios_data = [
        [
            Paragraph("Scenario", table_header_style),
            Paragraph("Default Fleet & Formation", table_header_style),
            Paragraph("What to Show the Teacher", table_header_style),
        ],
        [
            Paragraph("<b>1. Open Field</b>", table_cell_bold),
            Paragraph("20 Drones • V-Wing<br/>(Can switch 20/50/100 & V/Line/Grid/Circle)", table_cell_style),
            Paragraph("Clean baseline flight. Show formation keeping, then switch formation to Circle to watch smooth mid-air morphing with 0.007m circular precision.", table_cell_style),
        ],
        [
            Paragraph("<b>2. Obstacle Course</b>", table_cell_bold),
            Paragraph("50 Drones • V-Wing<br/>(Can switch 20/50/100 & V/Line/Grid/Circle)", table_cell_style),
            Paragraph("3D A* waypoint path (green glowing line) avoiding static high-rise pillars. Drones part around pillars using Artificial Potential Fields (APF).", table_cell_style),
        ],
        [
            Paragraph("<b>3. Dynamic Hazards</b>", table_cell_bold),
            Paragraph("50 Drones • Line<br/>(Can switch 20/50/100 & V/Line/Grid/Circle)", table_cell_style),
            Paragraph("Moving hazard spheres patrol the space. Drones dynamically deflect away using real-time Artificial Potential Fields.", table_cell_style),
        ],
        [
            Paragraph("<b>4. Leader Failure</b>", table_cell_bold),
            Paragraph("50 Drones • Grid<br/>(Can switch 20/50/100 & V/Line/Grid/Circle)", table_cell_style),
            Paragraph("Click 'Fail Leader' button in HUD. The leader loses power, drops, and the next best drone is instantly elected captain without halting.", table_cell_style),
        ],
        [
            Paragraph("<b>5. 100-Drone Swarm</b>", table_cell_bold),
            Paragraph("100 Drones • Circle<br/>(Can switch 20/50/100 & V/Line/Grid/Circle)", table_cell_style),
            Paragraph("Full-scale stress test. 100 drones forming a 55m ring. Demonstrates 60 FPS Three.js InstancedMesh performance.", table_cell_style),
        ],
    ]
    sc_tab = Table(scenarios_data, colWidths=[120, 150, 270])
    sc_tab.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("BOX", (0, 0), (-1, -1), 0.5, CARD_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, CARD_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(sc_tab)

    # Page Break for Q&A Guide
    story.append(PageBreak())

    # ==========================
    # 6. VIVA / TEACHER Q&A GUIDE
    # ==========================
    story.append(Paragraph("6. Teacher Viva / Presentation Q&A Cheat Sheet", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_GREEN, spaceAfter=8))

    qa_list = [
        (
            "Q1: Why didn't you compute 3D A* path planning for all 100 drones?",
            "Answer: Computing 3D A* across a 3D voxel grid for 100 individual drones every frame would be computationally prohibitive (O(N * Voxel³)). Instead, SwarmIQ uses a bio-inspired Leader-Follower hierarchy: only the leader computes the global A* path. Followers maintain geometric slots and use reactive local potential fields, reducing CPU load by over 95% while keeping the entire swarm safe.",
        ),
        (
            "Q2: How do you prevent drone-to-drone collisions inside the swarm?",
            "Answer: We use a multi-tiered safety system: First, Boids Separation exerts a 1/r² repulsion if drones get within 3.0m. Second, our Collision Avoidance engine calculates hyperbolic repulsive forces for pairs under 2.0m. Third, the persistent formation slot assignment guarantees that each drone has an assigned spatial slot separated by 3.5m.",
        ),
        (
            "Q3: How does the system handle leader failure?",
            "Answer: Every tick, the Leader Election algorithm monitors the current leader's health and battery. If the leader's battery drops below 20% or a hardware failure occurs, a multi-factor election runs across all active followers. The drone with the highest score (combining battery level, distance to target, and mesh connectivity) is elected leader, and the A* path is replanned instantly.",
        ),
        (
            "Q4: How does Three.js render 100 drones at 60 FPS in a web browser?",
            "Answer: Standard Three.js rendering creates 1 draw call per 3D mesh (which would lag at 100 drones). We used Three.js `InstancedMesh`. This allows all 100 follower drones to share a single geometry and material, rendering the entire swarm in exactly 1 GPU draw call, delivering a smooth 60 FPS even on standard laptops.",
        ),
        (
            "Q5: What is the green vertical pole and green line in the simulation?",
            "Answer: The vertical green pillar with a spinning radar ring is the Destination Beacon (the mission objective coordinates). The glowing green line on the ground/air is the 3D A* Global Planned Path computed for the leader to avoid obstacles.",
        ),
        (
            "Q6: How does the Artificial Potential Field (APF) algorithm work and avoid getting drones trapped?",
            "Answer: Each obstacle generates an invisible repulsive potential field (F_rep = -∇U_rep). Within 2.5m, an emergency surge ramps the repulsive thrust up to 40 N. To prevent the classic problem where formation holding force drags drones through obstacles, SwarmIQ uses 'Dynamic Formation Attenuation' — scaling down formation pull near obstacles so the swarm fluidly parts around obstacles like water around a stone, while a 0.8m physical hull buffer cancels any inward velocity.",
        ),
    ]

    for q, a in qa_list:
        story.append(Paragraph(q, q_style))
        story.append(Paragraph(a, a_style))

    # ==========================
    # 7. SUMMARY & CONCLUSION
    # ==========================
    story.append(Spacer(1, 4))
    story.append(Paragraph("7. Conclusion & Project Deliverables", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_GREEN, spaceAfter=8))

    story.append(
        Paragraph(
            "SwarmIQ successfully fulfills all requirements of a real-time, software-based autonomous drone swarm simulator. All 37 automated test cases pass cleanly, verified across mathematical accuracy, dynamic failover, obstacle avoidance, and high-frequency WebSocket streaming. The complete source code is modular, well-documented, and hosted on GitHub at <b>https://github.com/Meghs21/SWARM_IQ_DRONE</b>.",
            body_style,
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] PDF generated: {filename}")


if __name__ == "__main__":
    build_pdf()
