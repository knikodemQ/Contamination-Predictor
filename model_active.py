from __future__ import annotations

import argparse
import tkinter as tk
from tkinter import simpledialog

from oil_spill import run_simulation


class _InputDialog(simpledialog.Dialog):
    def body(self, master):
        tk.Label(master, text="Latitude of initial spill (e.g. 28.7):").grid(row=0)
        tk.Label(master, text="Longitude of initial spill (e.g. -88.3):").grid(row=1)
        tk.Label(master, text="Initial oil mass (kt):").grid(row=2)
        tk.Label(master, text="Temperature (C):").grid(row=3)

        self.lat_input = tk.Entry(master)
        self.lon_input = tk.Entry(master)
        self.mass_input = tk.Entry(master)
        self.temp_input = tk.Entry(master)

        self.lat_input.insert(0, "28.7")
        self.lon_input.insert(0, "-88.3")
        self.mass_input.insert(0, "100")
        self.temp_input.insert(0, "20")

        self.lat_input.grid(row=0, column=1)
        self.lon_input.grid(row=1, column=1)
        self.mass_input.grid(row=2, column=1)
        self.temp_input.grid(row=3, column=1)
        return self.lat_input

    def apply(self):
        self.latitude = float(self.lat_input.get())
        self.longitude = float(self.lon_input.get())
        self.mass = float(self.mass_input.get())
        self.temperature = float(self.temp_input.get())


def _ask_user_inputs() -> tuple[tuple[float, float], float, float]:
    root = tk.Tk()
    root.withdraw()
    dialog = _InputDialog(root)
    return (dialog.latitude, dialog.longitude), dialog.mass, dialog.temperature


def main() -> None:
    parser = argparse.ArgumentParser(description="Oil spill simulation")
    parser.add_argument("--no-gui", action="store_true", help="Use default values and skip Tk input dialog")
    parser.add_argument("--no-render", action="store_true", help="Run simulation without plotting")
    args = parser.parse_args()

    if args.no_gui:
        source = (28.7, -88.3)
        mass = 100.0
        temperature = 20.0
    else:
        source, mass, temperature = _ask_user_inputs()

    run_simulation(
        source_lat_lon=source,
        initial_oil_mass=mass,
        temperature_c=temperature,
        render=not args.no_render,
    )


if __name__ == "__main__":
    main()
