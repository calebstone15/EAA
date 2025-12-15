# handlers/plot_ox_mdot_venturi.py
# Calculates Oxidizer Mass Flow Rate (Mdot) from Venturi measurements
# Equation: ṁ = Cd × Y × A₂ × √( 2ρ(P₁-P₂) / (1 - (A₂/A₁)²) )

import numpy as np
from utils import apply_extra_data
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


def run(app):
    """Open a window to calculate Oxidizer Mdot from Venturi measurements"""
    ctx = app.ctx
    if ctx.df is None or ctx.time_col is None:
        messagebox.showerror("Error", "Please load a CSV file first.")
        return
    
    # Create the venturi calculator window
    VenturiMdotWindow(app, propellant_type="Oxidizer")


class VenturiMdotWindow(tk.Toplevel):
    """Window for calculating mass flow rate from venturi measurements"""
    
    # Default density values (kg/m³)
    FLUID_DENSITIES = {
        "Water": 1000.0,
        "LOX": 1141.0,
        "N2O": 1220.0,
        "Ethanol": 789.0,
        "Custom": None
    }
    
    # Unit conversion constants
    PSI_TO_PA = 6894.76
    IN2_TO_M2 = 0.00064516  # square inches to square meters
    
    def __init__(self, app, propellant_type="Oxidizer"):
        super().__init__(app)
        self.app = app
        self.ctx = app.ctx
        self.propellant_type = propellant_type
        
        self.title(f"{propellant_type} Mdot from Venturi")
        self.geometry("1200x850")
        
        # Variables for inputs
        self.p1_col_var = tk.StringVar()
        self.p2_col_var = tk.StringVar()
        self.a1_var = tk.StringVar(value="0.5")  # Area 1 in in²
        self.a2_var = tk.StringVar(value="0.25")  # Area 2 (throat) in in²
        self.cd_var = tk.StringVar(value="0.98")  # Discharge coefficient
        self.y_var = tk.StringVar(value="1.0")  # Expansion factor (1 for incompressible)
        self.rho_var = tk.StringVar(value="1141")  # Density in kg/m³ (default to LOX for oxidizer)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the calculator UI"""
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text=f"{self.propellant_type} Mass Flow Rate from Venturi",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=10)
        
        # Equation display
        equation_frame = tk.LabelFrame(main_frame, text="Venturi Equation", font=("Arial", 12, "bold"))
        equation_frame.pack(fill=tk.X, pady=10, padx=10)
        
        eq_label = tk.Label(
            equation_frame,
            text="ṁ = Cd × Y × A₂ × √( 2ρ(P₁-P₂) / (1 - (A₂/A₁)²) )",
            font=("Arial", 14, "italic")
        )
        eq_label.pack(pady=10)
        
        # Description
        desc_label = tk.Label(
            equation_frame,
            text="Cd=discharge coefficient, Y=expansion factor (1 for liquids), ρ=fluid density, A=cross-sectional areas",
            font=("Arial", 9),
            fg="gray"
        )
        desc_label.pack(pady=5)
        
        # Input frame container
        input_container = tk.Frame(main_frame)
        input_container.pack(fill=tk.X, pady=10)
        
        # Left column: Pressure columns selection
        left_frame = tk.LabelFrame(input_container, text="Pressure Selection", font=("Arial", 11, "bold"))
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Get available pressure columns from the CSV
        columns = list(self.ctx.df.columns)
        
        # P1 selection
        p1_frame = tk.Frame(left_frame)
        p1_frame.pack(fill=tk.X, pady=5, padx=10)
        tk.Label(p1_frame, text="P₁ (Upstream) Column:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.p1_combo = ttk.Combobox(p1_frame, textvariable=self.p1_col_var, values=columns, state="readonly", width=30)
        self.p1_combo.pack(side=tk.LEFT, padx=10)
        
        # P2 selection
        p2_frame = tk.Frame(left_frame)
        p2_frame.pack(fill=tk.X, pady=5, padx=10)
        tk.Label(p2_frame, text="P₂ (Downstream/Throat) Column:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.p2_combo = ttk.Combobox(p2_frame, textvariable=self.p2_col_var, values=columns, state="readonly", width=30)
        self.p2_combo.pack(side=tk.LEFT, padx=10)
        
        tk.Label(left_frame, text="(Pressures assumed to be in PSI)", font=("Arial", 9), fg="gray").pack(pady=5)
        
        # Right column: Area and coefficient inputs
        right_frame = tk.LabelFrame(input_container, text="Venturi Parameters", font=("Arial", 11, "bold"))
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        params_grid = tk.Frame(right_frame)
        params_grid.pack(fill=tk.X, pady=10, padx=10)
        
        # A1 input
        tk.Label(params_grid, text="A₁ (Upstream Area, in²):", font=("Arial", 10)).grid(row=0, column=0, sticky="e", pady=5)
        tk.Entry(params_grid, textvariable=self.a1_var, width=12).grid(row=0, column=1, padx=10, pady=5)
        
        # A2 input
        tk.Label(params_grid, text="A₂ (Throat Area, in²):", font=("Arial", 10)).grid(row=1, column=0, sticky="e", pady=5)
        tk.Entry(params_grid, textvariable=self.a2_var, width=12).grid(row=1, column=1, padx=10, pady=5)
        
        # Cd input
        tk.Label(params_grid, text="Cd (Discharge Coefficient):", font=("Arial", 10)).grid(row=2, column=0, sticky="e", pady=5)
        tk.Entry(params_grid, textvariable=self.cd_var, width=12).grid(row=2, column=1, padx=10, pady=5)
        tk.Label(params_grid, text="(typically 0.95-0.99)", font=("Arial", 9), fg="gray").grid(row=2, column=2, sticky="w")
        
        # Y input (expansion factor)
        tk.Label(params_grid, text="Y (Expansion Factor):", font=("Arial", 10)).grid(row=3, column=0, sticky="e", pady=5)
        tk.Entry(params_grid, textvariable=self.y_var, width=12).grid(row=3, column=1, padx=10, pady=5)
        tk.Label(params_grid, text="(1.0 for incompressible)", font=("Arial", 9), fg="gray").grid(row=3, column=2, sticky="w")
        
        # Density selection frame
        density_frame = tk.LabelFrame(main_frame, text="Fluid Density", font=("Arial", 11, "bold"))
        density_frame.pack(fill=tk.X, pady=10, padx=10)
        
        density_inner = tk.Frame(density_frame)
        density_inner.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Label(density_inner, text="ρ (kg/m³):", font=("Arial", 10)).pack(side=tk.LEFT)
        tk.Entry(density_inner, textvariable=self.rho_var, width=12).pack(side=tk.LEFT, padx=10)
        
        # Quick select buttons for common fluids
        tk.Label(density_inner, text="Quick Select:", font=("Arial", 10)).pack(side=tk.LEFT, padx=20)
        for fluid, density in self.FLUID_DENSITIES.items():
            if density is not None:
                btn = tk.Button(
                    density_inner, 
                    text=fluid, 
                    command=lambda d=density: self.rho_var.set(str(d)),
                    font=("Arial", 9)
                )
                btn.pack(side=tk.LEFT, padx=3)
        
        # Calculate button
        calc_btn = tk.Button(
            main_frame, 
            text="Calculate & Plot Mdot", 
            command=self._calculate_and_plot,
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white"
        )
        calc_btn.pack(pady=15)
        
        # Plot frame
        self.plot_frame = tk.Frame(main_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Result label
        self.result_label = tk.Label(
            main_frame,
            text="Select pressure columns and enter parameters, then click Calculate",
            font=("Arial", 12),
            fg="gray"
        )
        self.result_label.pack(pady=10)
    
    def _calculate_and_plot(self):
        """Calculate mass flow rate and plot over time"""
        try:
            # Validate inputs
            p1_col = self.p1_col_var.get()
            p2_col = self.p2_col_var.get()
            
            if not p1_col or not p2_col:
                messagebox.showerror("Error", "Please select both P1 and P2 pressure columns.")
                return
            
            # Get parameters
            a1_in2 = float(self.a1_var.get())  # in²
            a2_in2 = float(self.a2_var.get())  # in²
            cd = float(self.cd_var.get())
            y = float(self.y_var.get())
            rho = float(self.rho_var.get())  # kg/m³
            
            if a1_in2 <= 0 or a2_in2 <= 0:
                messagebox.showerror("Error", "Areas must be positive values.")
                return
            
            if a2_in2 >= a1_in2:
                messagebox.showerror("Error", "A₂ (throat) must be smaller than A₁ (upstream).")
                return
            
            if cd <= 0 or cd > 1:
                messagebox.showerror("Error", "Discharge coefficient must be between 0 and 1.")
                return
            
            # Convert areas to m²
            a1 = a1_in2 * self.IN2_TO_M2
            a2 = a2_in2 * self.IN2_TO_M2
            
            # Apply data masking and downsampling
            mask = apply_extra_data(self.app)
            ds = max(self.app.downsampling_slider.get(), 1)
            
            # Get data
            time = self.ctx.df[self.ctx.time_col][mask].iloc[::ds].values
            p1_psi = self.ctx.df[p1_col][mask].iloc[::ds].values.astype(float)
            p2_psi = self.ctx.df[p2_col][mask].iloc[::ds].values.astype(float)
            
            # Convert pressures to Pa
            p1_pa = p1_psi * self.PSI_TO_PA
            p2_pa = p2_psi * self.PSI_TO_PA
            
            # Calculate pressure difference
            delta_p = p1_pa - p2_pa
            
            # Handle negative pressure differences (set to 0 or NaN)
            delta_p = np.maximum(delta_p, 0)
            
            # Calculate beta ratio squared
            beta_sq = (a2 / a1) ** 2
            
            # Venturi equation: ṁ = Cd * Y * A2 * sqrt(2 * rho * delta_p / (1 - beta²))
            denominator = 1 - beta_sq
            mdot = cd * y * a2 * np.sqrt(2 * rho * delta_p / denominator)
            
            # Handle any NaN values
            mdot = np.nan_to_num(mdot, nan=0.0)
            
            # Clear previous plot
            for widget in self.plot_frame.winfo_children():
                widget.destroy()
            
            # Create plot
            fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Plot mdot
            raw_line, = ax.plot(time, mdot, label="Raw Data", color="orange", alpha=0.4, linewidth=1)
            smoothed_line, = ax.plot(time, mdot, label="Smoothed Data", color="orange", linewidth=2)
            
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Mass Flow Rate (kg/s)")
            ax.set_title(f"{self.propellant_type} Mass Flow Rate from Venturi")
            ax.legend()
            ax.grid(True)
            fig.tight_layout()
            
            # Variables for selecting average region
            points = []
            avg_line = None
            
            def on_click(event):
                nonlocal points, avg_line
                if event.inaxes != ax:
                    return
                
                # Reset points if more than two are selected
                if len(points) == 2:
                    points.clear()
                    # Remove previous markers
                    while len(ax.lines) > 2:
                        ax.lines[-1].remove()
                    if avg_line:
                        avg_line.remove()
                        avg_line = None
                    canvas.draw()
                
                # Add the new point
                points.append((event.xdata, event.ydata))
                ax.plot(event.xdata, event.ydata, 'ro', markersize=8)
                canvas.draw()
                
                # If two points are selected, calculate and display the average
                if len(points) == 2:
                    x1, _ = points[0]
                    x2, _ = points[1]
                    
                    # Get indices for the selected time range
                    idx1 = np.searchsorted(time, min(x1, x2))
                    idx2 = np.searchsorted(time, max(x1, x2))
                    
                    # Calculate average mdot
                    avg_mdot = np.mean(mdot[idx1:idx2+1])
                    
                    # Draw horizontal line showing average
                    avg_line, = ax.plot([min(x1, x2), max(x1, x2)], [avg_mdot, avg_mdot], 
                                       'r--', linewidth=2, label=f"Avg: {avg_mdot:.4f} kg/s")
                    
                    ax.legend()
                    canvas.draw()
                    
                    # Update result label
                    avg_label.config(text=f"Average ṁ in selected range: {avg_mdot:.4f} kg/s")
            
            # Smoothing function
            def update_smoothing(val):
                window = smoothing_slider.get()
                if window > 1:
                    smoothed_mdot = np.convolve(mdot, np.ones(window) / window, mode='same')
                    smoothed_line.set_ydata(smoothed_mdot)
                else:
                    smoothed_line.set_ydata(mdot)
                canvas.draw()
            
            # Save function
            def save_plot():
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".png",
                    filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                    title="Save Plot As"
                )
                if file_path:
                    fig.savefig(file_path)
                    messagebox.showinfo("Saved", f"Plot saved to {file_path}")
            
            # Connect click event
            canvas.mpl_connect("button_press_event", on_click)
            
            # Controls frame
            controls_frame = tk.Frame(self.plot_frame)
            controls_frame.pack(fill=tk.X, pady=5)
            
            # Smoothing slider
            smoothing_slider = tk.Scale(
                controls_frame, from_=1, to=100, orient=tk.HORIZONTAL,
                label="Smoothing", command=update_smoothing
            )
            smoothing_slider.set(1)
            smoothing_slider.pack(side=tk.LEFT, padx=10)
            
            # Save button
            save_btn = tk.Button(controls_frame, text="Save Plot", command=save_plot)
            save_btn.pack(side=tk.LEFT, padx=10)
            
            # Average label
            avg_label = tk.Label(
                controls_frame,
                text="Click two points on the plot to calculate average ṁ",
                font=("Arial", 11)
            )
            avg_label.pack(side=tk.LEFT, padx=20)
            
            # Update result label with statistics
            avg_mdot_overall = np.nanmean(mdot[mdot > 0])
            max_mdot = np.nanmax(mdot)
            self.result_label.config(
                text=f"Overall Avg: {avg_mdot_overall:.4f} kg/s | Max: {max_mdot:.4f} kg/s",
                fg="green"
            )
            
            canvas.draw()
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input value: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Calculation failed: {e}")
